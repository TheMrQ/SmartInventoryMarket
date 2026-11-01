"""P15 isolated tests: no MySQL, raw M5 files, or saved model artifact required."""

from collections.abc import Generator
from types import SimpleNamespace
from datetime import date, timedelta
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.db.database import get_db_session
from backend.app.api.auth import operational_user
import backend.app.db.models  # noqa: F401
from backend.app.db.models import Category, ForecastRun, Inventory, Product, SalesDaily, StockTransaction, User, UserRole
from backend.app.main import app
from backend.app.schemas.business import ForecastCreate
from backend.app.services.errors import ConflictError
from backend.app.services.forecasting import ForecastService, FrozenMetadata, validate_artifact
from ml.features.builder import FeatureEncodings


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        session.add(User(email="manager@example.test", full_name="Test Manager", password_hash="test", role=UserRole.MANAGER))
        session.commit()
    def override() -> Generator[Session, None, None]:
        session = factory()
        try:
            yield session
        finally:
            session.close()
    app.dependency_overrides[get_db_session] = override
    app.dependency_overrides[operational_user] = lambda: SimpleNamespace(id=1, role="MANAGER")
    with TestClient(app) as api_client:
        yield api_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def catalog(client: TestClient, sku: str = "FOODS_1_001") -> int:
    category = client.post("/api/categories", json={"code": "FOOD", "name": "Food"}).json()
    product = client.post("/api/products", json={"sku": sku, "name": "Item", "category_id": category["id"]})
    assert product.status_code == 201
    return product.json()["id"]


def csv_text(*rows: str) -> bytes:
    return ("sku,sale_date,quantity_sold,sell_price,source\n" + "\n".join(rows)).encode()


def test_historical_import_upserts_and_never_changes_inventory(client: TestClient) -> None:
    product_id = catalog(client)
    response = client.post("/api/sales/import", files={"file": ("history.csv", csv_text("FOODS_1_001,2016-04-01,4,2.50,POS"), "text/csv")})
    assert response.status_code == 200
    assert response.json() == {"rows_received": 1, "rows_inserted": 1, "rows_updated": 0, "rows_rejected": 0}
    second = client.post("/api/sales/import", files={"file": ("history.csv", csv_text("FOODS_1_001,2016-04-01,7,,BACKFILL"), "text/csv")})
    assert second.json()["rows_updated"] == 1
    assert client.get(f"/api/inventory/{product_id}").json()["on_hand"] == 0
    daily = client.get(f"/api/sales/{product_id}").json()[0]
    assert daily["quantity_sold"] == 7 and daily["sell_price"] is None


def test_import_rejects_unknown_duplicate_and_invalid_csv(client: TestClient) -> None:
    catalog(client)
    unknown = client.post("/api/sales/import", files={"file": ("x.csv", csv_text("UNKNOWN,2016-04-01,1,,"), "text/csv")})
    assert unknown.status_code == 404
    duplicate = client.post("/api/sales/import", files={"file": ("x.csv", csv_text("FOODS_1_001,2016-04-01,1,,", "FOODS_1_001,2016-04-01,2,,"), "text/csv")})
    assert duplicate.status_code == 409
    missing = client.post("/api/sales/import", files={"file": ("x.csv", b"sku,sale_date\nFOODS_1_001,2016-04-01", "text/csv")})
    assert missing.status_code == 409


def test_operational_sale_is_atomic_inventory_and_audit(client: TestClient) -> None:
    product_id = catalog(client)
    assert client.post(f"/api/inventory/{product_id}/adjustments", json={"transaction_type": "ADJUSTMENT_IN", "quantity": 5, "reason": "opening"}).status_code == 201
    sale = client.post("/api/sales/record", json={"product_id": product_id, "quantity": 2, "sale_date": "2016-04-24", "sell_price": "3.25", "idempotency_key": "sale-1"})
    assert sale.status_code == 201 and sale.json()["quantity_sold"] == 2
    second = client.post("/api/sales/record", json={"product_id": product_id, "quantity": 1, "sale_date": "2016-04-24", "idempotency_key": "sale-2"})
    assert second.json()["quantity_sold"] == 3 and second.json()["sell_price"] == "3.25"
    assert client.get(f"/api/inventory/{product_id}").json()["on_hand"] == 2
    history = client.get("/api/stock-transactions", params={"product_id": product_id}).json()
    assert [item["transaction_type"] for item in history].count("SALE") == 2
    rejected = client.post("/api/sales/record", json={"product_id": product_id, "quantity": 3, "sale_date": "2016-04-24", "idempotency_key": "sale-3"})
    assert rejected.status_code == 409
    assert client.get(f"/api/inventory/{product_id}").json()["on_hand"] == 2
    assert client.get(f"/api/sales/{product_id}").json()[0]["quantity_sold"] == 3


def test_operational_sale_replay_is_idempotent_and_conflicts_on_payload_change(client: TestClient) -> None:
    product_id = catalog(client)
    assert client.post(f"/api/inventory/{product_id}/adjustments", json={"transaction_type": "ADJUSTMENT_IN", "quantity": 5, "reason": "opening"}).status_code == 201
    payload = {"product_id": product_id, "quantity": 2, "sale_date": "2016-04-24", "idempotency_key": "same-logical-sale"}
    first = client.post("/api/sales/record", json=payload)
    replay = client.post("/api/sales/record", json=payload)
    assert first.status_code == replay.status_code == 201
    assert replay.json()["id"] == first.json()["id"]
    assert client.get(f"/api/inventory/{product_id}").json()["on_hand"] == 3
    assert [row["transaction_type"] for row in client.get("/api/stock-transactions", params={"product_id": product_id}).json()].count("SALE") == 1
    conflict = client.post("/api/sales/record", json={**payload, "quantity": 1})
    assert conflict.status_code == 409
    assert client.get(f"/api/inventory/{product_id}").json()["on_hand"] == 3


def test_server_actor_ignores_forged_actor_fields(client: TestClient) -> None:
    product_id = catalog(client)
    adjustment = client.post(
        f"/api/inventory/{product_id}/adjustments",
        json={"transaction_type": "ADJUSTMENT_IN", "quantity": 2, "reason": "opening", "created_by_user_id": 9999},
    )
    assert adjustment.status_code == 201
    assert adjustment.json()["created_by_user_id"] == 1


class FakeModel:
    def predict(self, features: pd.DataFrame) -> np.ndarray:
        return np.full(len(features), 2.0)


def fake_metadata() -> FrozenMetadata:
    dates = pd.date_range("2016-04-25", periods=28, freq="D")
    calendar = pd.DataFrame({"date": dates, "d": [f"d_{1914 + index}" for index in range(28)], "wday": [1] * 28, "month": [4] * 7 + [5] * 21, "year": [2016] * 28, "snap_CA": [0] * 28, "event_name_1": [np.nan] * 28, "event_type_1": [np.nan] * 28, "event_name_2": [np.nan] * 28, "event_type_2": [np.nan] * 28})
    encodings = FeatureEncodings(item_codes={"FOODS_1_001": 0}, dept_codes={"FOODS_1": 0}, event_codes={"event_name_1": {"__NONE__": 0}, "event_type_1": {"__NONE__": 0}, "event_name_2": {"__NONE__": 0}, "event_type_2": {"__NONE__": 0}})
    names = ("lag_1", "lag_7", "lag_14", "lag_28", "rolling_mean_7", "rolling_mean_14", "rolling_mean_28", "rolling_std_7", "rolling_std_28", "wday", "month", "year", "is_weekend", "snap_CA", "event_name_1_code", "event_type_1_code", "event_name_2_code", "event_type_2_code", "item_code", "dept_code", "last_known_sell_price", "price_lag_7", "price_change_from_7_days_ago", "price_available", "price_missing")
    return FrozenMetadata(names, encodings, frozenset(encodings.item_codes), calendar)


def test_forecast_service_persists_recursive_values_without_future_actuals() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        category = Category(code="M5", name="M5")
        session.add(category); session.flush()
        product = Product(sku="FOODS_1_001", name="Demo", category_id=category.id)
        session.add_all([product]); session.flush(); session.add(Inventory(product_id=product.id, on_hand=9))
        start = date(2016, 3, 28)
        session.add_all([SalesDaily(product_id=product.id, sale_date=start + timedelta(days=index), quantity_sold=index % 3, sell_price=Decimal("2.00")) for index in range(28)])
        session.commit()
        result = ForecastService(session, fake_metadata(), lambda: FakeModel()).create(ForecastCreate(product_ids=[product.id], horizon_days=14))
        assert len(result["values"]) == 14
        assert result["totals_by_product"][product.id]["days_7"] == Decimal("14.0000")
        assert result["totals_by_product"][product.id]["days_14"] == Decimal("28.0000")
        assert result["totals_by_product"][product.id]["days_28"] is None
        assert session.scalar(select(ForecastRun)) is not None
        assert session.get(Inventory, product.id).on_hand == 9
    engine.dispose()


def test_forecast_rejects_unknown_and_insufficient_history_and_hash(tmp_path) -> None:
    bad = tmp_path / "artifact.json"; bad.write_text("not the frozen artifact")
    with pytest.raises(ConflictError):
        validate_artifact(bad)
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        category = Category(code="M5", name="M5"); session.add(category); session.flush()
        product = Product(sku="NOT_M5", name="No", category_id=category.id); session.add(product); session.commit()
        with pytest.raises(ConflictError, match="frozen M5 vocabulary"):
            ForecastService(session, fake_metadata(), lambda: FakeModel()).create(ForecastCreate(product_ids=[product.id], horizon_days=7))
    engine.dispose()


def test_forecast_eligibility_exposes_frozen_m5_boundary() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        category = Category(code="M5", name="M5")
        session.add(category)
        session.flush()
        session.add_all(
            [
                Product(sku="FOODS_1_001", name="Supported", category_id=category.id),
                Product(sku="LOCAL-001", name="Local", category_id=category.id),
            ]
        )
        session.commit()
        eligibility = {item["product_id"]: item for item in ForecastService(session, fake_metadata()).eligibility()}
        assert eligibility[1] == {"product_id": 1, "eligible": True, "reason": None}
        assert eligibility[2]["eligible"] is False
        assert "frozen M5" in eligibility[2]["reason"]
    engine.dispose()
