"""Live P15 smoke check using the intentional reusable M5 demo catalog.

Forecast-run records made only for this smoke test are removed afterwards;
the five-product M5 demo seed remains available for manual Swagger evidence.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.app.db.database import SessionLocal
from backend.app.db.models import ForecastRun, ForecastValue
from backend.app.main import app
from scripts.db.import_m5_demo import main as import_demo


def require(response, expected: int):
    if response.status_code != expected:
        raise RuntimeError(f"expected {expected}; received {response.status_code}: {response.text}")
    return response.json()


def main() -> None:
    import_demo()
    run_ids: list[int] = []
    try:
        with TestClient(app) as client:
            require(client.get("/health/db"), 200)
            product = require(client.get("/api/products", params={"search": "FOODS_1_001"}), 200)[0]
            before = require(client.get(f"/api/inventory/{product['id']}"), 200)["on_hand"]
            seven = require(client.post("/api/forecasts", json={"product_ids": [product["id"]], "horizon_days": 7}), 201)
            twenty_eight = require(client.post("/api/forecasts", json={"product_ids": [product["id"]], "horizon_days": 28}), 201)
            run_ids.extend([seven["id"], twenty_eight["id"]])
            if len(seven["values"]) != 7 or len(twenty_eight["values"]) != 28:
                raise RuntimeError("forecast horizon/value counts did not match the request")
            if twenty_eight["values"][0]["forecast_date"] != "2016-04-25" or twenty_eight["values"][-1]["forecast_date"] != "2016-05-22":
                raise RuntimeError("M5-compatible forecast dates are incorrect")
            if require(client.get(f"/api/inventory/{product['id']}"), 200)["on_hand"] != before:
                raise RuntimeError("forecasting must not change inventory")
        print("P15 live MySQL/model smoke check passed (7-day and 28-day frozen forecasts).")
    finally:
        if run_ids:
            with SessionLocal.begin() as session:
                session.execute(delete(ForecastValue).where(ForecastValue.forecast_run_id.in_(run_ids)))
                session.execute(delete(ForecastRun).where(ForecastRun.id.in_(run_ids)))
        print("P15 smoke forecast runs were removed; reusable M5 demo catalog remains.")


if __name__ == "__main__":
    main()
