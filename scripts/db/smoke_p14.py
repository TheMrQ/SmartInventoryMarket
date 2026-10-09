"""Run and clean up a live P14 API smoke workflow against configured local MySQL."""

import sys
from pathlib import Path
from uuid import uuid4

# Support direct ``python scripts/db/smoke_p14.py`` invocation from the repo.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from backend.app.db.database import SessionLocal
from backend.app.db.models import (
    Category,
    Inventory,
    Product,
    PurchaseOrder,
    PurchaseOrderItem,
    StockTransaction,
    Supplier,
    SupplierProduct,
)
from backend.app.main import app


def require(response, expected: int):
    """Fail without printing a connection string or database configuration."""
    if response.status_code != expected:
        raise RuntimeError(f"expected HTTP {expected}; received HTTP {response.status_code}: {response.text}")
    return response.json() if response.content else None


def cleanup(marker: str) -> None:
    """Delete only this script's uniquely marked smoke records in FK-safe order."""
    category_code = f"P14-{marker}-CAT"
    supplier_code = f"P14-{marker}-SUP"
    sku = f"P14-{marker}-SKU"
    po_number = f"P14-{marker}-PO"
    with SessionLocal.begin() as session:
        product_ids = list(session.scalars(select(Product.id).where(Product.sku == sku)))
        po_ids = list(session.scalars(select(PurchaseOrder.id).where(PurchaseOrder.po_number == po_number)))
        po_item_ids = list(
            session.scalars(select(PurchaseOrderItem.id).where(PurchaseOrderItem.purchase_order_id.in_(po_ids)))
        )
        session.execute(delete(StockTransaction).where(StockTransaction.product_id.in_(product_ids)))
        session.execute(delete(PurchaseOrderItem).where(PurchaseOrderItem.id.in_(po_item_ids)))
        session.execute(delete(PurchaseOrder).where(PurchaseOrder.id.in_(po_ids)))
        session.execute(delete(SupplierProduct).where(SupplierProduct.product_id.in_(product_ids)))
        session.execute(delete(Inventory).where(Inventory.product_id.in_(product_ids)))
        session.execute(delete(Product).where(Product.id.in_(product_ids)))
        session.execute(delete(Category).where(Category.code == category_code))
        session.execute(delete(Supplier).where(Supplier.code == supplier_code))


def main() -> None:
    marker = uuid4().hex[:10].upper()
    category_code = f"P14-{marker}-CAT"
    supplier_code = f"P14-{marker}-SUP"
    sku = f"P14-{marker}-SKU"
    po_number = f"P14-{marker}-PO"
    try:
        with TestClient(app) as client:
            require(client.get("/health/db"), 200)
            category = require(client.post("/api/categories", json={"code": category_code, "name": "P14 smoke category"}), 201)
            product = require(
                client.post(
                    "/api/products",
                    json={"sku": sku, "name": "P14 smoke product", "category_id": category["id"]},
                ),
                201,
            )
            supplier = require(client.post("/api/suppliers", json={"code": supplier_code, "name": "P14 smoke supplier"}), 201)
            require(
                client.post(
                    "/api/supplier-products",
                    json={
                        "supplier_id": supplier["id"],
                        "product_id": product["id"],
                        "lead_time_days": 3,
                        "unit_cost": "2.50",
                        "is_preferred": True,
                    },
                ),
                201,
            )
            order = require(
                client.post(
                    "/api/purchase-orders",
                    json={
                        "po_number": po_number,
                        "supplier_id": supplier["id"],
                        "items": [{"product_id": product["id"], "ordered_quantity": 5}],
                    },
                ),
                201,
            )
            for target in ("APPROVED", "ORDERED", "IN_TRANSIT"):
                require(client.post(f"/api/purchase-orders/{order['id']}/transition", json={"target_status": target}), 200)
            inventory = require(client.get(f"/api/inventory/{product['id']}"), 200)
            if inventory["on_hand"] != 0 or inventory["incoming_quantity"] != 5:
                raise RuntimeError("unexpected inventory state before receipt")
            received = require(
                client.post(
                    f"/api/purchase-orders/{order['id']}/receive",
                    json={"items": [{"purchase_order_item_id": order["items"][0]["id"], "quantity": 5}]},
                ),
                200,
            )
            if received["status"] != "RECEIVED":
                raise RuntimeError("complete receipt did not reach RECEIVED status")
            inventory = require(client.get(f"/api/inventory/{product['id']}"), 200)
            history = require(client.get("/api/stock-transactions", params={"product_id": product["id"]}), 200)
            if inventory["on_hand"] != 5 or inventory["incoming_quantity"] != 0 or not any(
                item["transaction_type"] == "RECEIPT" for item in history
            ):
                raise RuntimeError("receipt did not produce expected inventory and audit state")
        print("P14 live MySQL API smoke check passed; marker data will be removed.")
    finally:
        cleanup(marker)
        print("P14 live MySQL smoke data cleanup passed.")


if __name__ == "__main__":
    main()
