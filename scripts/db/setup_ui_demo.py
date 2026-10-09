"""Prepare an optional, idempotent local database for the React thesis demo.

The script intentionally uses the same application services as the API.  It
does not insert forecasts, recommendations, purchase orders, or inventory
quantities directly.  Forecasts come from the frozen XGBOOST_V1 artifact and
all current-stock changes create immutable adjustment transactions.
"""

from __future__ import annotations

import math
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import func, select

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.db.database import SessionLocal
from backend.app.db.models import (
    ForecastRun,
    ForecastValue,
    Product,
    PurchaseOrder,
    PurchaseOrderStatus,
    RecommendationStatus,
    StockTransaction,
    StockTransactionType,
    Supplier,
    SupplierProduct,
)
from backend.app.schemas.business import (
    AdjustmentCreate,
    ForecastCreate,
    PurchaseOrderCreate,
    PurchaseOrderItemCreate,
    PurchaseOrderTransition,
    SupplierCreate,
    SupplierProductCreate,
    SupplierProductUpdate,
    SupplierUpdate,
)
from backend.app.services.business import BusinessService
from backend.app.services.forecasting import FrozenMetadata, ForecastService, validate_artifact
from backend.app.services.inventory_decisions import InventoryDecisionService
from scripts.db.import_m5_demo import ITEM_IDS, main as import_m5_demo


REASON = "Thesis UI demo setup"
PO_NUMBER = "DEMO-PO-001"
SUPPLIERS = (
    ("DEMO_SUPPLIER_A", "North Distribution — Demo"),
    ("DEMO_SUPPLIER_B", "Central Foods Supply — Demo"),
)
LEAD_TIMES = (3, 4, 5, 6, 7)


def _require_forecast_prerequisites() -> None:
    """Fail before mutating demo operations when frozen inference is unavailable."""
    validate_artifact()
    FrozenMetadata.load()


def _demo_products(session) -> list[Product]:
    products = list(session.scalars(select(Product).where(Product.sku.in_(ITEM_IDS)).order_by(Product.sku)))
    if [product.sku for product in products] != sorted(ITEM_IDS):
        raise RuntimeError("M5 demo catalog was not imported correctly")
    return products


def _ensure_supplier(service: BusinessService, session, code: str, name: str) -> Supplier:
    supplier = session.scalar(select(Supplier).where(Supplier.code == code))
    if supplier is None:
        return service.supplier_create(SupplierCreate(code=code, name=name, is_active=True))
    if not supplier.is_active or supplier.name != name:
        return service.supplier_update(supplier.id, SupplierUpdate(name=name, is_active=True))
    return supplier


def _ensure_mapping(service: BusinessService, session, supplier: Supplier, product: Product, lead_time_days: int) -> None:
    mapping = session.scalar(
        select(SupplierProduct).where(
            SupplierProduct.supplier_id == supplier.id,
            SupplierProduct.product_id == product.id,
        )
    )
    data = {
        "supplier_sku": f"DEMO-{product.sku}",
        "unit_cost": None,
        "lead_time_days": lead_time_days,
        "is_preferred": True,
    }
    if mapping is None:
        service.supplier_product_create(SupplierProductCreate(supplier_id=supplier.id, product_id=product.id, **data))
    else:
        service.supplier_product_update(mapping.id, SupplierProductUpdate(**data))


def _usable_forecast(session, product_ids: set[int]) -> int | None:
    for run in session.scalars(
        select(ForecastRun)
        .where(ForecastRun.model_name == "XGBOOST_V1", ForecastRun.feature_set == "FEATURE_SET_V1", ForecastRun.horizon_days >= 28)
        .order_by(ForecastRun.generated_at.desc(), ForecastRun.id.desc())
    ):
        ids = set(session.scalars(select(ForecastValue.product_id).where(ForecastValue.forecast_run_id == run.id)))
        latest_ids = {
            session.scalar(
                select(ForecastRun.id)
                .join(ForecastValue)
                .where(ForecastValue.product_id == product_id)
                .order_by(ForecastRun.generated_at.desc(), ForecastRun.id.desc())
            )
            for product_id in product_ids
        }
        if product_ids.issubset(ids) and latest_ids == {run.id}:
            return run.id
    return None


def _ensure_forecast(session, product_ids: list[int]) -> int:
    run_id = _usable_forecast(session, set(product_ids))
    if run_id is not None:
        return run_id
    return int(ForecastService(session).create(ForecastCreate(product_ids=product_ids, horizon_days=28))["id"])


def _ensure_incoming_po(service: BusinessService, session, supplier_id: int, product_id: int, quantity: int) -> PurchaseOrder:
    order = session.scalar(select(PurchaseOrder).where(PurchaseOrder.po_number == PO_NUMBER))
    if order is None:
        order = service.purchase_order_create(
            PurchaseOrderCreate(
                po_number=PO_NUMBER,
                supplier_id=supplier_id,
                expected_arrival_date=date.today() + timedelta(days=4),
                notes="Optional local thesis UI demo only; do not receive automatically.",
                items=[PurchaseOrderItemCreate(product_id=product_id, ordered_quantity=quantity)],
            )
        )
    order = service.purchase_order(order.id)
    transitions = {
        PurchaseOrderStatus.DRAFT: PurchaseOrderStatus.APPROVED,
        PurchaseOrderStatus.APPROVED: PurchaseOrderStatus.ORDERED,
        PurchaseOrderStatus.ORDERED: PurchaseOrderStatus.IN_TRANSIT,
    }
    while order.status in transitions:
        order = service.purchase_order_transition(order.id, PurchaseOrderTransition(target_status=transitions[order.status]))
    if order.status != PurchaseOrderStatus.IN_TRANSIT:
        raise RuntimeError(f"{PO_NUMBER} must remain IN_TRANSIT for the UI demo; found {order.status.value}")
    return order


def _first(candidates, message: str):
    candidate = next(iter(candidates), None)
    if candidate is None:
        raise RuntimeError(message)
    return candidate


def _inventory_targets(engine: InventoryDecisionService, products: list[Product], forecast_run_id: int) -> tuple[dict[int, int], dict[int, str]]:
    """Choose positions from real thresholds; labels remain engine-derived."""
    baseline = {product.id: engine.analyze(product.id) for product in products}
    run = engine.session.get(ForecastRun, forecast_run_id)
    if run is None:
        raise RuntimeError("persisted demo forecast disappeared")
    values = {
        product.id: {
            value.horizon_day: value.predicted_demand
            for value in run.values
            if value.product_id == product.id
        }
        for product in products
    }
    stockout = _first((item for item in baseline.values() if item.expected_lead_time_demand > 0), "no positive lead-time demand was available for a stockout demo")
    remaining = [item for item in baseline.values() if item.product_id != stockout.product_id]
    reorder = _first((item for item in remaining if item.target_stock > item.reorder_point), "no actionable reorder demo position was available")
    remaining = [item for item in remaining if item.product_id != reorder.product_id]
    overstock = _first(reversed(remaining), "insufficient products for an overstock demo")
    healthy = [item for item in remaining if item.product_id != overstock.product_id]
    if len(healthy) != 2:
        raise RuntimeError("five independent demo products are required")

    positions = {
        stockout.product_id: max(0, math.ceil(float(stockout.expected_lead_time_demand)) - 1),
        reorder.product_id: max(math.ceil(float(reorder.expected_lead_time_demand)), reorder.reorder_point),
        overstock.product_id: overstock.target_stock + max(1, math.ceil(float(values[overstock.product_id][1]))) + 8,
    }
    for item in healthy:
        positions[item.product_id] = max(item.target_stock, item.reorder_point + 1)
    roles = {
        stockout.product_id: "STOCKOUT_RISK",
        reorder.product_id: "REORDER_NEEDED",
        overstock.product_id: "OVERSTOCK_RISK",
        **{item.product_id: "HEALTHY" for item in healthy},
    }
    return positions, roles


def _set_on_hand(service: BusinessService, product_id: int, current: int, desired: int) -> None:
    difference = desired - current
    if difference == 0:
        return
    transaction_type = StockTransactionType.ADJUSTMENT_IN if difference > 0 else StockTransactionType.ADJUSTMENT_OUT
    service.adjustment(product_id, AdjustmentCreate(transaction_type=transaction_type, quantity=abs(difference), reason=REASON))


def main() -> None:
    _require_forecast_prerequisites()
    import_m5_demo()
    with SessionLocal() as session:
        business = BusinessService(session)
        suppliers = [_ensure_supplier(business, session, *values) for values in SUPPLIERS]
        products = _demo_products(session)
        for index, product in enumerate(products):
            _ensure_mapping(business, session, suppliers[index % len(suppliers)], product, LEAD_TIMES[index])

        forecast_run_id = _ensure_forecast(session, [product.id for product in products])
        engine = InventoryDecisionService(session)
        initial_targets, expected_roles = _inventory_targets(engine, products, forecast_run_id)
        incoming_product_id = max(
            (product_id for product_id, role in expected_roles.items() if role == "HEALTHY"),
            key=initial_targets.get,
        )
        incoming_supplier_id = next(
            mapping.supplier_id
            for mapping in session.scalars(select(SupplierProduct).where(SupplierProduct.product_id == incoming_product_id, SupplierProduct.is_preferred.is_(True)))
        )
        _ensure_incoming_po(business, session, incoming_supplier_id, incoming_product_id, max(1, min(8, initial_targets[incoming_product_id] // 3 or 1)))

        positions, expected_roles = _inventory_targets(engine, products, forecast_run_id)
        for product in products:
            decision = engine.analyze(product.id)
            desired_on_hand = max(0, positions[product.id] - decision.incoming_quantity)
            _set_on_hand(business, product.id, decision.on_hand, desired_on_hand)

        final = {product.id: engine.analyze(product.id) for product in products}
        mismatches = {product.sku: (expected_roles[product.id], final[product.id].risk_status) for product in products if expected_roles[product.id] != final[product.id].risk_status}
        if mismatches:
            raise RuntimeError(f"could not establish the intended real decision-state portfolio: {mismatches}")

        actionable = 0
        for product in products:
            decision = final[product.id]
            existing_new = engine.recommendations(product.id, RecommendationStatus.NEW, 1, 0)
            if decision.recommended_quantity > 0 and not existing_new:
                engine.generate(product.id)
            actionable += int(decision.recommended_quantity > 0)

        incoming_units = sum(item.incoming_quantity for item in final.values())
        audit_rows = int(session.scalar(select(func.count(StockTransaction.id)).where(StockTransaction.reason == REASON)) or 0)
        distribution = Counter(item.risk_status for item in final.values())
        new_count = sum(len(engine.recommendations(product.id, RecommendationStatus.NEW, 100, 0)) for product in products)
        print("UI demo setup complete:")
        print(f"- {len(products)} products")
        print(f"- {len(suppliers)} demo suppliers")
        print(f"- {len(products)} preferred supplier mappings")
        print(f"- persisted forecast run #{forecast_run_id}: XGBOOST_V1 / FEATURE_SET_V1")
        print(f"- {incoming_units} incoming PO units via {PO_NUMBER}")
        print(f"- {audit_rows} inventory adjustments with audit reason {REASON!r}")
        print(f"- {new_count} NEW recommendations ({actionable} actionable decisions)")
        print(f"- risk distribution {dict(sorted(distribution.items()))}")


if __name__ == "__main__":
    main()
