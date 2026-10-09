"""P16 decision-service tests on disposable SQLite state only."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
import backend.app.db.models  # noqa: F401
from backend.app.db.models import (
    Category,
    ForecastRun,
    ForecastValue,
    Inventory,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseOrderStatus,
    Product,
    RecommendationStatus,
    ReorderRecommendation,
    SalesDaily,
    Supplier,
    SupplierProduct,
)
from backend.app.schemas.business import RecommendationReview
from backend.app.services.errors import ConflictError
from backend.app.services.inventory_decisions import InventoryDecisionService


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as database:
        yield database
    Base.metadata.drop_all(engine)
    engine.dispose()


def seed(session: Session, *, on_hand: int = 0, lead_time: int = 2, supplier_count: int = 1, preferred: bool = True, history_days: int = 28, forecast_days: int = 7, incoming: int = 0):
    category = Category(code="FOOD", name="Food")
    session.add(category); session.flush()
    product = Product(sku="FOODS_1_001", name="Demo", category_id=category.id)
    session.add(product); session.flush(); session.add(Inventory(product_id=product.id, on_hand=on_hand))
    for index in range(supplier_count):
        supplier = Supplier(code=f"SUP-{index}", name=f"Supplier {index}")
        session.add(supplier); session.flush()
        session.add(SupplierProduct(supplier_id=supplier.id, product_id=product.id, lead_time_days=lead_time, is_preferred=preferred and index == 0))
    session.flush()
    if incoming:
        order = PurchaseOrder(po_number="PO-TEST", supplier_id=1, status=PurchaseOrderStatus.ORDERED)
        session.add(order); session.flush()
        session.add(PurchaseOrderItem(purchase_order_id=order.id, product_id=product.id, ordered_quantity=incoming, received_quantity=0))
    origin = date(2016, 4, 24)
    start = origin - timedelta(days=history_days - 1)
    session.add_all(SalesDaily(product_id=product.id, sale_date=start + timedelta(days=index), quantity_sold=index, source="test") for index in range(history_days))
    run = ForecastRun(model_name="XGBOOST_V1", feature_set="FEATURE_SET_V1", history_end_date=origin, forecast_start_date=origin + timedelta(days=1), horizon_days=forecast_days)
    session.add(run); session.flush()
    session.add_all(ForecastValue(forecast_run_id=run.id, product_id=product.id, forecast_date=origin + timedelta(days=index), horizon_day=index, predicted_demand=Decimal("2.0000")) for index in range(1, forecast_days + 1))
    session.commit()
    return product, run


def test_calculation_safety_stock_and_persisted_recommendation_do_not_change_inventory(session: Session) -> None:
    product, run = seed(session)
    service = InventoryDecisionService(session)
    decision = service.analyze(product.id)
    assert decision.forecast_run_id == run.id
    assert decision.lead_time_days == 2
    assert decision.inventory_position == 0
    assert decision.expected_lead_time_demand == Decimal("4.0000")
    assert decision.safety_stock == 19  # ceil(1.645 * population_std(0..27) * sqrt(2))
    assert decision.reorder_point == 23 and decision.target_stock == 25
    assert decision.recommended_quantity == 25 and decision.risk_status == "STOCKOUT_RISK"
    created = service.generate(product.id)
    assert created["recommendation"]["status"] == RecommendationStatus.NEW
    assert session.get(Inventory, product.id).on_hand == 0


def test_inventory_position_includes_open_purchase_order_and_decision_reads_have_no_side_effect(session: Session) -> None:
    product, _ = seed(session, incoming=3)
    service = InventoryDecisionService(session)
    assert service.analyze(product.id).inventory_position == 3
    assert service.decisions(None, None, 50, 0)
    assert session.query(ReorderRecommendation).count() == 0


@pytest.mark.parametrize(("on_hand", "expected"), [(0, "STOCKOUT_RISK"), (20, "REORDER_NEEDED"), (24, "HEALTHY"), (28, "OVERSTOCK_RISK")])
def test_risk_classification_rules(session: Session, on_hand: int, expected: str) -> None:
    product, _ = seed(session, on_hand=on_hand)
    assert InventoryDecisionService(session).analyze(product.id).risk_status == expected


def test_supplier_selection_preferred_fallback_and_ambiguity(session: Session) -> None:
    product, _ = seed(session, supplier_count=2, preferred=True)
    assert InventoryDecisionService(session).analyze(product.id).supplier_name == "Supplier 0"
    session.query(SupplierProduct).update({"is_preferred": False}); session.commit()
    with pytest.raises(ConflictError, match="multiple active suppliers"):
        InventoryDecisionService(session).analyze(product.id)
    session.query(SupplierProduct).filter(SupplierProduct.supplier_id != 1).delete(); session.commit()
    assert InventoryDecisionService(session).analyze(product.id).supplier_name == "Supplier 0"
    session.query(SupplierProduct).delete(); session.commit()
    with pytest.raises(ConflictError, match="no active supplier"):
        InventoryDecisionService(session).analyze(product.id)


def test_history_and_forecast_horizon_requirements(session: Session) -> None:
    product, _ = seed(session, history_days=27)
    with pytest.raises(ConflictError, match="28 contiguous"):
        InventoryDecisionService(session).analyze(product.id)
    session.add(SalesDaily(product_id=product.id, sale_date=date(2016, 3, 28), quantity_sold=0, source="test"))
    session.query(SupplierProduct).update({"lead_time_days": 7}); session.commit()
    with pytest.raises(ConflictError, match="enough consecutive"):
        InventoryDecisionService(session).analyze(product.id)


def test_missing_forecast_is_rejected(session: Session) -> None:
    product, _ = seed(session)
    session.query(ForecastValue).delete(); session.query(ForecastRun).delete(); session.commit()
    with pytest.raises(ConflictError, match="persisted compatible forecast"):
        InventoryDecisionService(session).analyze(product.id)


def test_expiration_and_human_review_transitions(session: Session) -> None:
    product, _ = seed(session)
    service = InventoryDecisionService(session)
    first = service.generate(product.id)["recommendation"]
    second = service.generate(product.id)["recommendation"]
    assert service.recommendation(first["id"])["status"] == RecommendationStatus.EXPIRED
    accepted = service.review(second["id"], RecommendationReview(action="ACCEPT", notes="approved"))
    assert accepted["status"] == RecommendationStatus.ACCEPTED
    assert accepted["approved_quantity"] == accepted["recommended_quantity"]
    with pytest.raises(ConflictError, match="only NEW"):
        service.review(second["id"], RecommendationReview(action="REJECT"))
    modified = service.generate(product.id)["recommendation"]
    changed = service.review(modified["id"], RecommendationReview(action="MODIFY", approved_quantity=4))
    assert changed["status"] == RecommendationStatus.MODIFIED and changed["approved_quantity"] == 4
    rejected = service.generate(product.id)["recommendation"]
    declined = service.review(rejected["id"], RecommendationReview(action="REJECT"))
    assert declined["status"] == RecommendationStatus.REJECTED and declined["approved_quantity"] is None
