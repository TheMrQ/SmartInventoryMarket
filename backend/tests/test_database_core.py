"""Unit coverage for the P13 database core without requiring local MySQL."""

from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import configure_mappers

from backend.app.api import health
from backend.app.core.config import Settings
from backend.app.db.base import Base
from backend.app.db.models import (  # noqa: F401 - ensure metadata is loaded
    PurchaseOrderStatus,
    RecommendationStatus,
    StockTransactionType,
    UserRole,
)
from backend.app.main import app


client = TestClient(app)


def test_settings_require_pymysql_url_without_logging_it() -> None:
    settings = Settings(database_url="mysql+pymysql://user:example@localhost:3306/database")

    assert settings.database_url.startswith("mysql+pymysql://")
    assert settings.app_env == "development"

    try:
        Settings(database_url="postgresql+psycopg://user:example@localhost/database")
    except ValidationError as error:
        assert "mysql+pymysql" in str(error)
    else:
        raise AssertionError("A stale PostgreSQL URL must not be accepted")


def test_metadata_contains_the_frozen_single_store_schema() -> None:
    expected_tables = {
        "users",
        "categories",
        "products",
        "suppliers",
        "supplier_products",
        "inventory",
        "sales_daily",
        "purchase_orders",
        "purchase_order_items",
        "stock_transactions",
        "forecast_runs",
        "forecast_values",
        "model_metrics",
        "reorder_recommendations",
    }

    assert set(Base.metadata.tables) == expected_tables


def test_important_constraints_and_indexes_are_declared() -> None:
    inventory = Base.metadata.tables["inventory"]
    purchase_order_items = Base.metadata.tables["purchase_order_items"]
    sales_daily = Base.metadata.tables["sales_daily"]

    assert any("on_hand >= 0" in str(item.sqltext) for item in inventory.constraints if isinstance(item, CheckConstraint))
    assert any(
        "received_quantity <= ordered_quantity" in str(item.sqltext)
        for item in purchase_order_items.constraints
        if isinstance(item, CheckConstraint)
    )
    assert any(
        {"product_id", "sale_date"} == {column.name for column in item.columns}
        for item in sales_daily.constraints
        if isinstance(item, UniqueConstraint)
    )
    assert "ix_stock_transactions_product_occurred" in {
        index.name for index in Base.metadata.tables["stock_transactions"].indexes
    }


def test_controlled_status_values_and_relationships_are_available() -> None:
    assert {role.value for role in UserRole} == {"ADMIN", "MANAGER", "INVENTORY_STAFF"}
    assert {status.value for status in PurchaseOrderStatus} == {
        "DRAFT",
        "APPROVED",
        "ORDERED",
        "IN_TRANSIT",
        "RECEIVED",
        "CANCELLED",
    }
    assert {kind.value for kind in StockTransactionType} == {
        "RECEIPT",
        "SALE",
        "ADJUSTMENT_IN",
        "ADJUSTMENT_OUT",
    }
    assert {status.value for status in RecommendationStatus} == {
        "NEW",
        "ACCEPTED",
        "MODIFIED",
        "REJECTED",
        "EXPIRED",
    }

    configure_mappers()
    product_relationships = {item.key for item in Base.registry.mappers if item.class_.__name__ == "Product" for item in item.relationships}
    assert {"category", "inventory", "sales", "forecast_values"}.issubset(product_relationships)


def test_database_health_returns_success_with_a_mocked_connection(monkeypatch) -> None:
    monkeypatch.setattr(health, "check_database_connection", lambda: None)

    response = client.get("/health/db")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_database_health_hides_connection_errors(monkeypatch) -> None:
    def unavailable() -> None:
        raise SQLAlchemyError("sensitive connection details must not be returned")

    monkeypatch.setattr(health, "check_database_connection", unavailable)

    response = client.get("/health/db")

    assert response.status_code == 503
    assert response.json() == {"detail": {"status": "unavailable", "database": "unavailable"}}
    assert "sensitive" not in response.text
