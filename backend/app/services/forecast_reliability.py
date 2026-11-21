"""Read-only P25-03 reliability evidence for saved frozen-model forecasts."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.db.models import Product
from backend.app.services.errors import NotFoundError
from backend.app.services.forecasting import ForecastService


ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PATH = ROOT / "data/manifests/forecast_reliability_reference.json"


@lru_cache(maxsize=1)
def _reference() -> dict:
    if not REFERENCE_PATH.is_file():
        raise RuntimeError("forecast reliability reference is unavailable; run scripts/ml/run_forecast_reliability.py")
    return json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))


def _interval_row(reference: dict, horizon_day: int, band: str, coverage: float) -> dict:
    rows = [row for row in reference["intervals"] if row["coverage"] == coverage and row["usable"]]
    for level, match in (
        ("horizon_and_sparsity", lambda row: row["horizon_day"] == horizon_day and row["sparsity_band"] == band),
        ("horizon", lambda row: row["horizon_day"] == horizon_day),
        ("global", lambda row: True),
    ):
        found = [row for row in rows if row["level"] == level and match(row)]
        if len(found) == 1:
            return found[0]
    raise RuntimeError("forecast reliability reference has no usable interval fallback")


class ForecastReliabilityService:
    """Overlay empirical intervals/evidence without changing a V1 point forecast."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def for_product(self, product_id: int) -> dict:
        product = self.session.get(Product, product_id)
        if product is None:
            raise NotFoundError("product not found")
        try:
            reference = _reference()
        except RuntimeError as exc:
            return {"available": False, "reason": str(exc), "product_id": product_id}
        evidence = reference["products"].get(product.sku)
        if evidence is None:
            return {"available": False, "reason": "No comparable pre-TEST reliability evidence exists for this SKU.", "product_id": product_id}
        try:
            run = ForecastService(self.session).latest(product_id)
        except NotFoundError:
            return {"available": False, "reason": "Generate a compatible saved forecast before viewing its reliability evidence.", "product_id": product_id}
        intervals = []
        for value in run["values"]:
            point = float(value.predicted_demand)
            daily = {"horizon_day": value.horizon_day, "forecast_date": value.forecast_date, "point_forecast": point}
            for coverage in (.80, .95):
                residual = _interval_row(reference, value.horizon_day, evidence["sparsity_band"], coverage)
                lower = max(0.0, point + float(residual["residual_lower"]))
                upper = max(lower, point + float(residual["residual_upper"]))
                daily[str(int(coverage * 100))] = {"lower": lower, "upper": upper, "level": residual["level"], "sample_size": residual["sample_size"]}
            intervals.append(daily)
        return {
            "available": True, "product_id": product_id,
            "model_name": run["model_name"], "feature_set": run["feature_set"],
            "forecast_run_id": run["id"], "history_end_date": run["history_end_date"],
            "forecast_start_date": run["forecast_start_date"], "generated_at": run["generated_at"],
            "freshness": {"status": "HISTORICAL_DEMO_CUTOFF", "message": "This saved forecast uses the fixed M5 thesis-demo origin; it is not a current real-world demand signal."},
            "historical": evidence,
            "calibration": reference.get("independent_fold_4_calibration", []),
            "intervals": intervals,
            "limitations": [
                "Forecasts are estimates, not guarantees; wider intervals reflect greater historical uncertainty.",
                "M5 demand is historical Walmart data and operational inventory/supplier records are simulated.",
                "New or arbitrary retailer SKUs require local retraining and validation.",
            ],
        }
