"""Create a manifest-scoped M5 historical forecast and synthetic supermarket demo.

Dry-run is the default. ``--apply`` is intentionally required before any local
database write; this script never creates users, resets tables, or uses M5 TEST
actuals. Observed M5 sales/prices are imported through d_1913 only. Inventory,
suppliers, POs, receipts, and review actions are labelled synthetic.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.db.database import SessionLocal
from backend.app.db.models import (
    Category, DemoProductSource, DemoScenario, DemoScenarioForecast, ForecastRun,
    Inventory, Product, PurchaseOrder, PurchaseOrderStatus, RecommendationStatus,
    ReorderRecommendation, SalesDaily, Supplier, SupplierProduct, User, UserRole,
)
from backend.app.schemas.business import (
    AdjustmentCreate, ForecastCreate, PurchaseOrderCreate, PurchaseOrderItemCreate,
    PurchaseOrderTransition, ReceiptCreate, ReceiptLine, RecommendationPurchaseOrderCreate,
    RecommendationReview, SupplierCreate, SupplierProductCreate, SupplierProductUpdate,
)
from backend.app.services.business import BusinessService
from backend.app.services.errors import ConflictError
from backend.app.services.forecasting import ForecastService, FrozenMetadata, validate_artifact
from backend.app.services.inventory_decisions import InventoryDecisionService


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "m5"
CONFIG_PATH = ROOT / "configs" / "data" / "m5_ca1_foods_demo.yaml"
OBSERVED_SOURCE = "M5_OBSERVED_CA1_FOODS_V1"


@dataclass(frozen=True)
class SelectedSku:
    item_id: str
    dept_id: str


def load_config(path: Path = CONFIG_PATH) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def selection_digest(selected: list[SelectedSku]) -> str:
    payload = "\n".join(f"{item.dept_id}:{item.item_id}" for item in selected).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def friendly_name(item_id: str) -> str:
    _, department, number = item_id.split("_", 2)
    return f"Food Item {department}-{number} (M5 simulation)"


def select_skus(frame: pd.DataFrame, departments: list[str], per_department: int) -> list[SelectedSku]:
    """Stable lexical sample: exact, broad FOODS coverage without random selection."""
    selected: list[SelectedSku] = []
    for department in departments:
        candidates = frame.loc[frame["dept_id"] == department, ["item_id", "dept_id"]].drop_duplicates().sort_values("item_id")
        if len(candidates) < per_department:
            raise RuntimeError(f"M5 source does not contain {per_department} eligible {department} SKUs")
        selected.extend(SelectedSku(row.item_id, row.dept_id) for row in candidates.head(per_department).itertuples(index=False))
    return selected


def _paths(config: dict) -> tuple[Path, Path, Path]:
    sources = config["sources"]
    paths = tuple(RAW / sources[name] for name in ("sales", "calendar", "prices"))
    if not all(path.is_file() for path in paths):
        raise RuntimeError("P22 requires local ignored M5 sales_train_evaluation.csv, calendar.csv, and sell_prices.csv")
    return paths  # type: ignore[return-value]


def load_observed_selection(config: dict) -> tuple[list[SelectedSku], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sales_path, calendar_path, prices_path = _paths(config)
    end = int(str(config["history_end_d"]).split("_")[1])
    days = [f"d_{day}" for day in range(1, end + 1)]
    sales = pd.read_csv(sales_path, usecols=["item_id", "dept_id", "cat_id", "store_id", *days])
    sales = sales.loc[(sales["store_id"] == config["store_id"]) & (sales["cat_id"] == "FOODS")].copy()
    selected = select_skus(sales, list(config["selection"]["departments"]), int(config["selection"]["per_department"]))
    ids = [item.item_id for item in selected]
    sales = sales.loc[sales["item_id"].isin(ids)].set_index("item_id").sort_index()
    calendar = pd.read_csv(calendar_path, usecols=["d", "date", "wm_yr_wk", "event_name_1", "event_type_1", "snap_CA"])
    calendar = calendar.iloc[:end].copy()
    calendar["date"] = pd.to_datetime(calendar["date"]).dt.date
    chunks = []
    for chunk in pd.read_csv(prices_path, chunksize=100_000):
        match = chunk.loc[(chunk["store_id"] == config["store_id"]) & chunk["item_id"].isin(ids), ["item_id", "wm_yr_wk", "sell_price"]]
        if not match.empty:
            chunks.append(match)
    prices = pd.concat(chunks, ignore_index=True)
    if set(ids) != set(prices["item_id"]):
        raise RuntimeError("one or more selected M5 SKUs have no CA_1 sell-price history")
    return selected, sales, calendar, prices


def _actor(session) -> User:
    user = session.scalar(select(User).where(User.is_active.is_(True), User.role.in_([UserRole.ADMIN, UserRole.MANAGER])).order_by(User.id))
    if user is None:
        raise RuntimeError("P22 apply requires an existing active manager or admin; it will not create a user")
    return user


def _scenario(session, config: dict, selected: list[SelectedSku]) -> DemoScenario:
    digest = selection_digest(selected)
    scenario = session.scalar(select(DemoScenario).where(DemoScenario.scenario_key == config["scenario_key"]))
    if scenario is None:
        scenario = DemoScenario(
            scenario_key=config["scenario_key"], m5_store_id=config["store_id"],
            source_sales_file=config["sources"]["sales"], source_calendar_file=config["sources"]["calendar"],
            source_prices_file=config["sources"]["prices"], history_start_d=config["history_start_d"],
            history_end_d=config["history_end_d"], selection_size=len(selected), selection_sha256=digest,
        )
        session.add(scenario)
        session.flush()
    elif (scenario.selection_sha256, scenario.selection_size) != (digest, len(selected)):
        raise RuntimeError("existing scenario manifest does not match the configured deterministic selection")
    return scenario


def _existing_scenario_result(session, scenario: DemoScenario) -> dict:
    """Return an existing manifest's state without issuing operational writes."""
    products = list(session.scalars(select(Product).join(DemoProductSource).where(DemoProductSource.scenario_id == scenario.id)))
    if len(products) != scenario.selection_size:
        raise RuntimeError("existing scenario has incomplete product provenance; refusing to mutate it")
    forecast = session.scalar(select(DemoScenarioForecast).where(DemoScenarioForecast.scenario_id == scenario.id))
    if forecast is None:
        raise RuntimeError("existing scenario has no persisted forecast link; refusing to mutate it")
    marker = scenario.scenario_key
    orders = list(session.scalars(select(PurchaseOrder).where(PurchaseOrder.po_number.like(f"{marker}-%"))))
    if len(orders) != 4:
        raise RuntimeError("existing scenario has an unexpected purchase-order count; refusing to mutate it")
    risks = [InventoryDecisionService(session).analyze(product.id).risk_status for product in products]
    recommendations = list(session.scalars(select(ReorderRecommendation).where(ReorderRecommendation.notes.like(f"{marker}:%"))))
    if len(recommendations) < 3:
        raise RuntimeError("existing scenario has incomplete reviewed recommendations; refusing to mutate it")
    linked = next((order for order in orders if order.po_number == f"{marker}-LINKED-DRAFT"), None)
    if linked is None or linked.reorder_recommendation_id is None:
        raise RuntimeError("existing scenario lacks its linked draft purchase order")
    return {
        "scenario": marker, "skus": len(products), "forecast_run_id": forecast.forecast_run_id,
        "risk_distribution": {name: risks.count(name) for name in ("HEALTHY", "REORDER_NEEDED", "STOCKOUT_RISK", "OVERSTOCK_RISK")},
        "purchase_orders": {order.po_number.removeprefix(f"{marker}-").lower(): order.id for order in orders},
        "recommendation_count": len(recommendations), "reused_existing": True,
    }


def _upsert_observed_history(session, scenario: DemoScenario, config: dict, selected: list[SelectedSku], sales: pd.DataFrame, calendar: pd.DataFrame, prices: pd.DataFrame) -> list[Product]:
    category = session.scalar(select(Category).where(Category.code == config["category_code"]))
    if category is None:
        category = Category(code=config["category_code"], name="M5 CA_1 FOODS — simulated operations")
        session.add(category); session.flush()
    price_lookup = prices.set_index(["item_id", "wm_yr_wk"])["sell_price"].to_dict()
    products: list[Product] = []
    for selected_sku in selected:
        product = session.scalar(select(Product).where(Product.sku == selected_sku.item_id))
        if product is None:
            product = Product(sku=selected_sku.item_id, name=friendly_name(selected_sku.item_id), category_id=category.id, unit="unit", is_active=True)
            session.add(product); session.flush(); session.add(Inventory(product_id=product.id, on_hand=0))
        elif product.category_id == category.id or product.name.startswith("Demo Product —"):
            product.category_id = category.id; product.name = friendly_name(selected_sku.item_id); product.is_active = True
        else:
            raise RuntimeError(f"SKU {selected_sku.item_id} belongs to an unrelated product and will not be modified")
        source = session.scalar(select(DemoProductSource).where(DemoProductSource.scenario_id == scenario.id, DemoProductSource.product_id == product.id))
        if source is None:
            session.add(DemoProductSource(scenario_id=scenario.id, product_id=product.id, m5_item_id=selected_sku.item_id, m5_dept_id=selected_sku.dept_id))
        elif (source.m5_item_id, source.m5_dept_id) != (selected_sku.item_id, selected_sku.dept_id):
            raise RuntimeError("existing product provenance disagrees with the M5 selection")
        existing = {row.sale_date: row for row in session.scalars(select(SalesDaily).where(SalesDaily.product_id == product.id))}
        quantities = sales.loc[selected_sku.item_id, [f"d_{day}" for day in range(1, 1914)]].to_numpy(dtype=int)
        for row, quantity in zip(calendar.itertuples(index=False), quantities, strict=True):
            price = price_lookup.get((selected_sku.item_id, row.wm_yr_wk))
            record = existing.get(row.date)
            if record is None:
                session.add(SalesDaily(product_id=product.id, sale_date=row.date, quantity_sold=int(quantity), sell_price=None if pd.isna(price) else float(price), source=OBSERVED_SOURCE))
            else:
                if record.source not in {OBSERVED_SOURCE, "M5_CA1_FOODS_DEMO"}:
                    raise RuntimeError(f"SKU {selected_sku.item_id} has unrelated sales history on {row.date}; refusing overwrite")
                record.quantity_sold = int(quantity); record.sell_price = None if pd.isna(price) else float(price); record.source = OBSERVED_SOURCE
        products.append(product)
    session.commit()
    return products


def _ensure_supplier_mapping(service: BusinessService, session, scenario_key: str, product: Product, index: int, actor_id: int) -> Supplier:
    code = f"{scenario_key}_SUP_{index % 3 + 1:02d}"
    supplier = session.scalar(select(Supplier).where(Supplier.code == code))
    if supplier is None:
        supplier = service.supplier_create(SupplierCreate(code=code, name=f"Synthetic Supplier {index % 3 + 1} — {scenario_key}", is_active=True))
    mapping = session.scalar(select(SupplierProduct).where(SupplierProduct.supplier_id == supplier.id, SupplierProduct.product_id == product.id))
    data = dict(supplier_sku=f"SYN-{product.sku}", unit_cost=None, lead_time_days=3 + index % 5, is_preferred=True)
    if mapping is None:
        service.supplier_product_create(SupplierProductCreate(supplier_id=supplier.id, product_id=product.id, **data))
    else:
        service.supplier_product_update(mapping.id, SupplierProductUpdate(**data))
    return supplier


def _set_stock(service: BusinessService, session, product_id: int, desired: int, actor_id: int, marker: str) -> None:
    current = session.get(Inventory, product_id)
    if current is None:
        raise RuntimeError("scenario product has no inventory")
    difference = desired - current.on_hand
    if difference:
        service.adjustment(product_id, AdjustmentCreate(transaction_type="ADJUSTMENT_IN" if difference > 0 else "ADJUSTMENT_OUT", quantity=abs(difference), reason=f"{marker}: synthetic initial stock"), actor_id)


def _scenario_forecast(session, scenario: DemoScenario, products: list[Product]) -> int:
    existing = session.scalar(select(DemoScenarioForecast).where(DemoScenarioForecast.scenario_id == scenario.id))
    if existing is not None:
        return existing.forecast_run_id
    run = ForecastService(session).create(ForecastCreate(product_ids=[product.id for product in products], horizon_days=28))
    session.add(DemoScenarioForecast(scenario_id=scenario.id, forecast_run_id=run["id"])); session.commit()
    return int(run["id"])


def _ensure_po(service: BusinessService, session, actor_id: int, marker: str, name: str, product: Product, supplier: Supplier, quantity: int, receive: int | None = None) -> PurchaseOrder:
    po_number = f"{marker}-{name}"
    order = session.scalar(select(PurchaseOrder).where(PurchaseOrder.po_number == po_number))
    if order is None:
        order = service.purchase_order_create(PurchaseOrderCreate(po_number=po_number, supplier_id=supplier.id, expected_arrival_date=date.today() + timedelta(days=5), notes=f"{marker}: synthetic procurement only", items=[PurchaseOrderItemCreate(product_id=product.id, ordered_quantity=quantity)]), actor_id)
    order = service.purchase_order(order.id)
    for target in (PurchaseOrderStatus.APPROVED, PurchaseOrderStatus.ORDERED, PurchaseOrderStatus.IN_TRANSIT):
        if order.status == target:
            continue
        if order.status in {PurchaseOrderStatus.DRAFT, PurchaseOrderStatus.APPROVED, PurchaseOrderStatus.ORDERED}:
            order = service.purchase_order_transition(order.id, PurchaseOrderTransition(target_status=target), actor_id)
    if receive is not None and order.status == PurchaseOrderStatus.IN_TRANSIT:
        item = order.items[0]
        remaining = item.ordered_quantity - item.received_quantity
        if remaining:
            service.receive_purchase_order(order.id, ReceiptCreate(items=[ReceiptLine(purchase_order_item_id=item.id, quantity=min(receive, remaining))]), actor_id)
    return service.purchase_order(order.id)


def apply(config: dict) -> dict:
    selected, sales, calendar, prices = load_observed_selection(config)
    validate_artifact(); FrozenMetadata.load()
    with SessionLocal() as session:
        actor = _actor(session)
        existing = session.scalar(select(DemoScenario).where(DemoScenario.scenario_key == config["scenario_key"]))
        if existing is not None:
            # An applied manifest is immutable on rerun.  This avoids duplicate
            # stock adjustments, reviews, purchase orders, and audit rows.
            return _existing_scenario_result(session, existing)
        scenario = _scenario(session, config, selected)
        products = _upsert_observed_history(session, scenario, config, selected, sales, calendar, prices)
        business = BusinessService(session)
        suppliers = [_ensure_supplier_mapping(business, session, scenario.scenario_key, product, index, actor.id) for index, product in enumerate(products)]
        forecast_id = _scenario_forecast(session, scenario, products)
        decisions = InventoryDecisionService(session)
        marker = scenario.scenario_key
        # Engine-derived positions create real healthy, low-stock, and stockout states.
        for index, product in enumerate(products):
            decision = decisions.analyze(product.id)
            if index < 6:
                desired = 0
            elif index < 12:
                desired = max(0, min(decision.reorder_point, math.ceil(float(decision.expected_lead_time_demand))))
            elif index < 16:
                desired = decision.target_stock + math.ceil(float(decision.expected_lead_time_demand)) + 8
            else:
                desired = decision.target_stock
            _set_stock(business, session, product.id, desired, actor.id, marker)
        incoming = _ensure_po(business, session, actor.id, marker, "INCOMING", products[16], suppliers[16], 8)
        partial = _ensure_po(business, session, actor.id, marker, "PARTIAL", products[17], suppliers[17], 8, receive=3)
        completed = _ensure_po(business, session, actor.id, marker, "COMPLETE", products[18], suppliers[18], 6, receive=6)
        # Recommendations are calculated by the existing engine, then reviewed through P21 services.
        generated = []
        for product in products[:6]:
            result = decisions.generate(product.id)
            if result["recommendation"]:
                generated.append(result["recommendation"])
        if len(generated) < 3:
            raise RuntimeError("scenario did not produce enough engine-generated restock recommendations")
        accepted = decisions.review(generated[1]["id"], RecommendationReview(action="ACCEPT", notes=f"{marker}: synthetic accepted review"), actor.id)
        modified = decisions.review(generated[2]["id"], RecommendationReview(action="MODIFY", approved_quantity=max(1, generated[2]["recommended_quantity"] - 1), notes=f"{marker}: synthetic modified review"), actor.id)
        linked = session.scalar(select(PurchaseOrder).where(PurchaseOrder.reorder_recommendation_id == accepted["id"]))
        if linked is None:
            linked = business.recommendation_purchase_order_create(accepted["id"], RecommendationPurchaseOrderCreate(po_number=f"{marker}-LINKED-DRAFT", notes=f"{marker}: linked synthetic draft", confirm=True), actor.id)
        final = [decisions.analyze(product.id) for product in products]
        return {
            "scenario": scenario.scenario_key, "skus": len(products), "forecast_run_id": forecast_id,
            "risk_distribution": {name: sum(item.risk_status == name for item in final) for name in ("HEALTHY", "REORDER_NEEDED", "STOCKOUT_RISK", "OVERSTOCK_RISK")},
            "purchase_orders": {"incoming": incoming.id, "partial": partial.id, "completed": completed.id, "linked_draft": linked.id},
            "recommendations": {"pending": generated[0]["id"], "accepted": accepted["id"], "modified": modified["id"]},
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write only the named P22 scenario after dry-run review")
    args = parser.parse_args()
    config = load_config()
    selected, _, calendar, _ = load_observed_selection(config)
    print(f"P22 scenario {config['scenario_key']}: {len(selected)} deterministic CA_1/FOODS SKUs")
    print(f"- observed historical sales/prices: {config['history_start_d']} through {config['history_end_d']} ({calendar['date'].iloc[0]} to {calendar['date'].iloc[-1]})")
    print(f"- departments: {', '.join(config['selection']['departments'])}; selection SHA-256: {selection_digest(selected)}")
    print("- calendar/events remain observed M5 context consumed by the frozen inference service; inventory, suppliers, POs, and movements are synthetic.")
    if not args.apply:
        print("Dry run only. Re-run with --apply to write this manifest-scoped scenario.")
        return
    print(apply(config))


if __name__ == "__main__":
    main()
