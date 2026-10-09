"""P14 API tests using an isolated SQLite database, never local MySQL."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.db.database import get_db_session
import backend.app.db.models  # noqa: F401 - register all metadata
from backend.app.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_session() -> Generator[Session, None, None]:
        session = test_session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_session
    with TestClient(app) as api_client:
        yield api_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def create_catalog(client: TestClient) -> tuple[int, int, int]:
    category = client.post("/api/categories", json={"code": "FOOD", "name": "Food"})
    assert category.status_code == 201
    product = client.post(
        "/api/products",
        json={"sku": "MILK-001", "name": "Milk", "category_id": category.json()["id"], "unit": "bottle"},
    )
    assert product.status_code == 201
    supplier = client.post("/api/suppliers", json={"code": "SUP-001", "name": "Fresh Supply"})
    assert supplier.status_code == 201
    mapping = client.post(
        "/api/supplier-products",
        json={
            "supplier_id": supplier.json()["id"],
            "product_id": product.json()["id"],
            "unit_cost": "2.50",
            "lead_time_days": 3,
            "is_preferred": True,
        },
    )
    assert mapping.status_code == 201
    return category.json()["id"], product.json()["id"], supplier.json()["id"]


def create_order(client: TestClient, product_id: int, supplier_id: int, number: str, quantity: int = 5) -> dict:
    response = client.post(
        "/api/purchase-orders",
        json={
            "po_number": number,
            "supplier_id": supplier_id,
            "items": [{"product_id": product_id, "ordered_quantity": quantity}],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def move_to_in_transit(client: TestClient, order_id: int) -> dict:
    for target in ("APPROVED", "ORDERED", "IN_TRANSIT"):
        response = client.post(f"/api/purchase-orders/{order_id}/transition", json={"target_status": target})
        assert response.status_code == 200, response.text
    return response.json()


def test_category_product_creation_inventory_and_conflicts(client: TestClient) -> None:
    category_id, product_id, _ = create_catalog(client)

    inventory = client.get(f"/api/inventory/{product_id}")
    assert inventory.status_code == 200
    assert inventory.json()["on_hand"] == 0
    assert inventory.json()["incoming_quantity"] == 0

    assert client.post("/api/categories", json={"code": "FOOD", "name": "Duplicate"}).status_code == 409
    assert (
        client.post(
            "/api/products",
            json={"sku": "MILK-001", "name": "Duplicate", "category_id": category_id},
        ).status_code
        == 409
    )
    assert (
        client.post("/api/products", json={"sku": "BAD", "name": "Bad", "category_id": 9999}).status_code
        == 404
    )


def test_supplier_mapping_validation_and_single_preferred_supplier(client: TestClient) -> None:
    _, product_id, supplier_id = create_catalog(client)
    assert (
        client.post(
            "/api/suppliers", json={"code": "SUP-001", "name": "Duplicate supplier"}
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/supplier-products",
            json={"supplier_id": supplier_id, "product_id": product_id, "lead_time_days": 3},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/supplier-products",
            json={"supplier_id": supplier_id, "product_id": product_id, "lead_time_days": 0},
        ).status_code
        == 422
    )


def test_adjustments_are_auditable_and_never_make_inventory_negative(client: TestClient) -> None:
    _, product_id, _ = create_catalog(client)
    adjustment = client.post(
        f"/api/inventory/{product_id}/adjustments",
        json={"transaction_type": "ADJUSTMENT_IN", "quantity": 7, "reason": "opening count"},
    )
    assert adjustment.status_code == 201
    assert adjustment.json()["transaction_type"] == "ADJUSTMENT_IN"
    assert client.get(f"/api/inventory/{product_id}").json()["on_hand"] == 7

    outgoing = client.post(
        f"/api/inventory/{product_id}/adjustments",
        json={"transaction_type": "ADJUSTMENT_OUT", "quantity": 2, "reason": "damaged goods"},
    )
    assert outgoing.status_code == 201
    assert client.get(f"/api/inventory/{product_id}").json()["on_hand"] == 5
    assert (
        client.post(
            f"/api/inventory/{product_id}/adjustments",
            json={"transaction_type": "ADJUSTMENT_OUT", "quantity": 6, "reason": "invalid"},
        ).status_code
        == 409
    )
    history = client.get("/api/stock-transactions", params={"product_id": product_id}).json()
    assert [item["transaction_type"] for item in history] == ["ADJUSTMENT_OUT", "ADJUSTMENT_IN"]


def test_purchase_order_incoming_state_machine_and_draft_only_items(client: TestClient) -> None:
    _, product_id, supplier_id = create_catalog(client)
    order = create_order(client, product_id, supplier_id, "PO-INCOMING")
    order_id = order["id"]
    assert client.get(f"/api/inventory/{product_id}").json()["incoming_quantity"] == 0  # DRAFT

    approved = client.post(f"/api/purchase-orders/{order_id}/transition", json={"target_status": "APPROVED"})
    assert approved.status_code == 200
    assert client.get(f"/api/inventory/{product_id}").json()["incoming_quantity"] == 0  # APPROVED
    assert client.post(f"/api/purchase-orders/{order_id}/transition", json={"target_status": "ORDERED"}).status_code == 200
    assert client.get(f"/api/inventory/{product_id}").json()["incoming_quantity"] == 5
    assert client.post(f"/api/purchase-orders/{order_id}/transition", json={"target_status": "IN_TRANSIT"}).status_code == 200
    assert client.get(f"/api/inventory/{product_id}").json()["incoming_quantity"] == 5
    assert (
        client.patch(
            f"/api/purchase-orders/{order_id}/items/{order['items'][0]['id']}", json={"ordered_quantity": 6}
        ).status_code
        == 409
    )
    assert client.post(f"/api/purchase-orders/{order_id}/transition", json={"target_status": "APPROVED"}).status_code == 409

    cancelled = create_order(client, product_id, supplier_id, "PO-CANCELLED")
    assert client.post(f"/api/purchase-orders/{cancelled['id']}/transition", json={"target_status": "CANCELLED"}).status_code == 200
    assert client.get(f"/api/inventory/{product_id}").json()["incoming_quantity"] == 5
    assert client.post(f"/api/purchase-orders/{cancelled['id']}/receive", json={"items": []}).status_code == 422


def test_receipts_are_atomic_partial_then_complete_and_auditable(client: TestClient) -> None:
    _, product_id, supplier_id = create_catalog(client)
    order = create_order(client, product_id, supplier_id, "PO-RECEIVE")
    order = move_to_in_transit(client, order["id"])
    item_id = order["items"][0]["id"]

    over = client.post(f"/api/purchase-orders/{order['id']}/receive", json={"items": [{"purchase_order_item_id": item_id, "quantity": 6}]})
    assert over.status_code == 409
    assert client.get(f"/api/inventory/{product_id}").json()["on_hand"] == 0

    partial = client.post(f"/api/purchase-orders/{order['id']}/receive", json={"items": [{"purchase_order_item_id": item_id, "quantity": 3}]})
    assert partial.status_code == 200
    assert partial.json()["status"] == "IN_TRANSIT"
    assert partial.json()["items"][0]["received_quantity"] == 3
    assert client.get(f"/api/inventory/{product_id}").json()["on_hand"] == 3

    complete = client.post(f"/api/purchase-orders/{order['id']}/receive", json={"items": [{"purchase_order_item_id": item_id, "quantity": 2}]})
    assert complete.status_code == 200
    assert complete.json()["status"] == "RECEIVED"
    assert complete.json()["received_at"] is not None
    assert client.get(f"/api/inventory/{product_id}").json()["incoming_quantity"] == 0
    assert client.get(f"/api/inventory/{product_id}").json()["on_hand"] == 5
    transactions = client.get("/api/stock-transactions", params={"product_id": product_id}).json()
    assert [row["transaction_type"] for row in transactions] == ["RECEIPT", "RECEIPT"]
    assert client.post(f"/api/purchase-orders/{order['id']}/receive", json={"items": [{"purchase_order_item_id": item_id, "quantity": 1}]}).status_code == 409
