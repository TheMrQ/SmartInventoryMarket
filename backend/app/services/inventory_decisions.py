"""Explainable P16 inventory decision and human-review workflow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, ROUND_CEILING
from math import sqrt

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.db.models import RecommendationStatus, ReorderRecommendation, utc_now
from backend.app.repositories.business import BusinessRepository
from backend.app.repositories.inventory_decisions import InventoryDecisionRepository
from backend.app.schemas.business import RecommendationReview
from backend.app.services.errors import ConflictError, NotFoundError


Z_SERVICE_FACTOR = Decimal("1.645")
REVIEW_PERIOD_DAYS = 1
HISTORY_DAYS = 28


@dataclass(frozen=True)
class Decision:
    product_id: int
    sku: str
    product_name: str
    on_hand: int
    incoming_quantity: int
    inventory_position: int
    forecast_run_id: int
    lead_time_days: int
    expected_lead_time_demand: Decimal
    safety_stock: int
    reorder_point: int
    target_stock: int
    risk_status: str
    recommended_quantity: int
    supplier_id: int
    supplier_name: str

    def as_dict(self) -> dict:
        return self.__dict__.copy()


class InventoryDecisionService:
    """Generic business rules operating on valid forecasts; no stock mutation occurs here."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = InventoryDecisionRepository()
        self.business_repo = BusinessRepository()

    @staticmethod
    def _ceil(value: Decimal) -> int:
        return int(value.to_integral_value(rounding=ROUND_CEILING))

    def _supplier(self, product_id: int):
        mappings = self.repo.supplier_mappings(self.session, product_id)
        preferred = [mapping for mapping in mappings if mapping.is_preferred]
        if len(preferred) == 1:
            return preferred[0]
        if len(preferred) > 1:
            raise ConflictError("multiple active preferred suppliers require data correction")
        if len(mappings) == 1:
            return mappings[0]
        if not mappings:
            raise ConflictError("no active supplier mapping exists for this product")
        raise ConflictError("multiple active suppliers exist without a preferred supplier")

    def analyze(self, product_id: int) -> Decision:
        product = self.repo.product(self.session, product_id)
        if product is None:
            raise NotFoundError("product not found")
        if not product.is_active:
            raise ConflictError("inactive products cannot receive inventory decisions")
        inventory = self.repo.inventory(self.session, product_id)
        if inventory is None:
            raise ConflictError("product has no inventory row")
        supplier = self._supplier(product_id)
        forecast = self.repo.latest_forecast(self.session, product_id)
        if forecast is None:
            raise ConflictError("a persisted compatible forecast is required before an inventory decision")
        lead_time = supplier.lead_time_days
        values = sorted((value for value in forecast.values if value.product_id == product_id), key=lambda value: value.horizon_day)
        required_days = lead_time + REVIEW_PERIOD_DAYS
        if len(values) < required_days or [value.horizon_day for value in values[:required_days]] != list(range(1, required_days + 1)):
            raise ConflictError("the persisted forecast does not contain enough consecutive days for supplier lead time plus review period")
        start = forecast.history_end_date - timedelta(days=HISTORY_DAYS - 1)
        history = self.repo.sales_history(self.session, product_id, start, forecast.history_end_date)
        expected_dates = [start + timedelta(days=offset) for offset in range(HISTORY_DAYS)]
        if [row.sale_date for row in history] != expected_dates:
            raise ConflictError("28 contiguous observed sales days before the forecast boundary are required")
        demand = [Decimal(row.quantity_sold) for row in history]
        mean = sum(demand, Decimal("0")) / HISTORY_DAYS
        variance = sum((item - mean) ** 2 for item in demand) / HISTORY_DAYS
        safety_stock = self._ceil(Z_SERVICE_FACTOR * Decimal(str(sqrt(float(variance)))) * Decimal(str(sqrt(lead_time))))
        expected_lead = sum((value.predicted_demand for value in values[:lead_time]), Decimal("0"))
        target_demand = sum((value.predicted_demand for value in values[:required_days]), Decimal("0"))
        reorder_point = self._ceil(expected_lead + safety_stock)
        target_stock = self._ceil(target_demand + safety_stock)
        incoming = self.repo.incoming_quantity(self.session, product_id)
        position = inventory.on_hand + incoming
        if Decimal(position) < expected_lead:
            risk = "STOCKOUT_RISK"
        elif position <= reorder_point:
            risk = "REORDER_NEEDED"
        elif Decimal(position) > Decimal(target_stock) + values[0].predicted_demand:
            risk = "OVERSTOCK_RISK"
        else:
            risk = "HEALTHY"
        quantity = self._ceil(max(Decimal("0"), Decimal(target_stock) - Decimal(position))) if position <= reorder_point else 0
        return Decision(product_id=product.id, sku=product.sku, product_name=product.name, on_hand=inventory.on_hand, incoming_quantity=incoming, inventory_position=position, forecast_run_id=forecast.id, lead_time_days=lead_time, expected_lead_time_demand=expected_lead, safety_stock=safety_stock, reorder_point=reorder_point, target_stock=target_stock, risk_status=risk, recommended_quantity=quantity, supplier_id=supplier.supplier_id, supplier_name=supplier.supplier.name)

    def decisions(self, risk_status: str | None, search: str | None, limit: int, offset: int) -> list[Decision]:
        results: list[Decision] = []
        # The view is intentionally side-effect free. Products missing required inputs are
        # not decision-eligible and appear through their direct endpoint as clear errors.
        for product in self.repo.products(self.session, search, limit, offset):
            try:
                decision = self.analyze(product.id)
            except (ConflictError, NotFoundError):
                continue
            if risk_status is None or decision.risk_status == risk_status:
                results.append(decision)
        return results

    def _recommendation_dict(self, recommendation: ReorderRecommendation) -> dict:
        data = {column.name: getattr(recommendation, column.name) for column in ReorderRecommendation.__table__.columns}
        try:
            supplier = self._supplier(recommendation.product_id)
            data.update(supplier_id=supplier.supplier_id, supplier_name=supplier.supplier.name)
        except ConflictError:
            data.update(supplier_id=None, supplier_name=None)
        return data

    def generate(self, product_id: int) -> dict:
        decision = self.analyze(product_id)
        if decision.recommended_quantity == 0:
            return {"decision": decision.as_dict(), "recommendation": None}
        now = utc_now()
        for prior in self.repo.active_new_recommendations(self.session, product_id):
            prior.status = RecommendationStatus.EXPIRED
            prior.expires_at = now
        recommendation = ReorderRecommendation(product_id=product_id, forecast_run_id=decision.forecast_run_id, status=RecommendationStatus.NEW, current_on_hand=decision.on_hand, incoming_quantity=decision.incoming_quantity, lead_time_days=decision.lead_time_days, safety_stock=decision.safety_stock, reorder_point=decision.reorder_point, recommended_quantity=decision.recommended_quantity, expires_at=now + timedelta(days=REVIEW_PERIOD_DAYS))
        self.session.add(recommendation)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("recommendation persistence failed") from exc
        self.session.refresh(recommendation)
        return {"decision": decision.as_dict(), "recommendation": self._recommendation_dict(recommendation)}

    def recommendations(self, product_id: int | None, status: RecommendationStatus | None, limit: int, offset: int) -> list[dict]:
        return [self._recommendation_dict(item) for item in self.repo.recommendations(self.session, product_id, status, limit, offset)]

    def recommendation(self, recommendation_id: int) -> dict:
        item = self.repo.recommendation(self.session, recommendation_id)
        if item is None:
            raise NotFoundError("reorder recommendation not found")
        return self._recommendation_dict(item)

    def review(self, recommendation_id: int, data: RecommendationReview) -> dict:
        item = self.repo.recommendation(self.session, recommendation_id, lock=True)
        if item is None:
            raise NotFoundError("reorder recommendation not found")
        if item.status != RecommendationStatus.NEW:
            raise ConflictError("only NEW recommendations can be reviewed")
        if data.reviewed_by_user_id is not None and not self.business_repo.user_exists(self.session, data.reviewed_by_user_id):
            raise NotFoundError("user not found")
        if data.action == "ACCEPT":
            if data.approved_quantity not in {None, item.recommended_quantity}:
                raise ConflictError("ACCEPT uses the recommended quantity; use MODIFY for a different quantity")
            item.status = RecommendationStatus.ACCEPTED
            item.approved_quantity = item.recommended_quantity
        elif data.action == "MODIFY":
            if data.approved_quantity is None:
                raise ConflictError("MODIFY requires approved_quantity")
            item.status = RecommendationStatus.MODIFIED
            item.approved_quantity = data.approved_quantity
        else:
            if data.approved_quantity is not None:
                raise ConflictError("REJECT must not include approved_quantity")
            item.status = RecommendationStatus.REJECTED
            item.approved_quantity = None
        item.reviewed_at = utc_now()
        item.reviewed_by_user_id = data.reviewed_by_user_id
        item.notes = data.notes
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("recommendation review persistence failed") from exc
        self.session.refresh(item)
        return self._recommendation_dict(item)
