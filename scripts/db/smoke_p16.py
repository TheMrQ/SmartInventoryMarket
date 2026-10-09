"""Live P16 smoke check; removes only its marked supplier/forecast/recommendation data."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from backend.app.db.database import SessionLocal
from backend.app.db.models import ForecastRun, ForecastValue, Product, ReorderRecommendation, Supplier, SupplierProduct
from backend.app.main import app
from scripts.db.import_m5_demo import main as import_demo


def require(response, expected: int):
    if response.status_code != expected:
        raise RuntimeError(f"expected {expected}; received {response.status_code}: {response.text}")
    return response.json()


def main() -> None:
    marker = uuid4().hex[:10].upper()
    supplier_code = f"P16-{marker}-SUP"
    created_run: int | None = None
    created_recommendation: int | None = None
    try:
        import_demo()
        with TestClient(app) as client:
            require(client.get("/health/db"), 200)
            product = require(client.get("/api/products", params={"search": "FOODS_1_001"}), 200)[0]
            with SessionLocal() as session:
                if session.scalar(select(SupplierProduct.id).where(SupplierProduct.product_id == product["id"])) is not None:
                    raise RuntimeError("P16 smoke requires a demo product without pre-existing supplier mappings")
            supplier = require(client.post("/api/suppliers", json={"code": supplier_code, "name": "P16 smoke supplier"}), 201)
            require(client.post("/api/supplier-products", json={"supplier_id": supplier["id"], "product_id": product["id"], "lead_time_days": 2, "is_preferred": True}), 201)
            before = require(client.get(f"/api/inventory/{product['id']}"), 200)["on_hand"]
            forecast = require(client.post("/api/forecasts", json={"product_ids": [product["id"]], "horizon_days": 7}), 201)
            created_run = forecast["id"]
            decision = require(client.get("/api/inventory-decisions", params={"search": product["sku"]}), 200)
            if len(decision) != 1 or decision[0]["forecast_run_id"] != created_run:
                raise RuntimeError("decision view did not use the persisted forecast")
            generated = require(client.post("/api/reorder-recommendations/generate", json={"product_id": product["id"]}), 201)
            if generated["recommendation"] is None:
                raise RuntimeError("smoke setup expected an actionable reorder recommendation")
            created_recommendation = generated["recommendation"]["id"]
            reviewed = require(client.post(f"/api/reorder-recommendations/{created_recommendation}/review", json={"action": "REJECT", "notes": "smoke cleanup"}), 200)
            if reviewed["status"] != "REJECTED":
                raise RuntimeError("review action was not persisted")
            if require(client.get(f"/api/inventory/{product['id']}"), 200)["on_hand"] != before:
                raise RuntimeError("recommendations must not change inventory")
        print("P16 live MySQL decision/review smoke check passed.")
    finally:
        with SessionLocal.begin() as session:
            if created_recommendation is not None:
                session.execute(delete(ReorderRecommendation).where(ReorderRecommendation.id == created_recommendation))
            if created_run is not None:
                session.execute(delete(ForecastValue).where(ForecastValue.forecast_run_id == created_run))
                session.execute(delete(ForecastRun).where(ForecastRun.id == created_run))
            supplier_ids = list(session.scalars(select(Supplier.id).where(Supplier.code == supplier_code)))
            session.execute(delete(SupplierProduct).where(SupplierProduct.supplier_id.in_(supplier_ids)))
            session.execute(delete(Supplier).where(Supplier.id.in_(supplier_ids)))
        print("P16 smoke-only supplier, forecast, and recommendation records were removed.")


if __name__ == "__main__":
    main()
