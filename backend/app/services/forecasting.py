"""M5-compatible frozen XGBOOST_V1 inference and atomic forecast persistence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from functools import lru_cache
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.db.models import ForecastRun, ForecastValue, Product
from backend.app.repositories.sales_forecasts import SalesForecastRepository
from backend.app.schemas.business import ForecastCreate
from backend.app.services.errors import ConflictError, NotFoundError
from ml.features.builder import FeatureEncodings, load_feature_config
from ml.models.recursive import recursive_forecast
from ml.models.xgboost_model import load_model_config, load_saved_model, predict_checked


ROOT = Path(__file__).resolve().parents[3]
ARTIFACT = ROOT / "artifacts/models/xgboost_selected_trainval_final.json"
EXPECTED_SHA256 = "1b484f3028b012abeb2dcd768b784342ecac340a3b5bb5ad5bc46d790d5f59b7"
ORIGIN_DATE = date(2016, 4, 24)
MODEL_VERSION = "selected_trainval_final_sha256_1b484f30"


def validate_artifact(path: Path = ARTIFACT, expected_sha256: str = EXPECTED_SHA256) -> None:
    """Verify an ignored artifact without disclosing its local filesystem path."""
    if not path.is_file():
        raise ConflictError("the frozen forecasting artifact is unavailable; retraining is not performed by this API")
    hasher = hashlib.sha256()
    with path.open("rb") as artifact:
        for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
            hasher.update(chunk)
    digest = hasher.hexdigest()
    if digest != expected_sha256:
        raise ConflictError("the frozen forecasting artifact failed integrity validation; retraining is not performed by this API")


@lru_cache(maxsize=1)
def _cached_model():
    validate_artifact()
    return load_saved_model(load_model_config(ROOT / "configs/models/xgboost_v1.yaml"), ARTIFACT)


@dataclass(frozen=True)
class FrozenMetadata:
    feature_names: tuple[str, ...]
    encodings: FeatureEncodings
    known_items: frozenset[str]
    calendar: pd.DataFrame

    @classmethod
    def load(cls) -> "FrozenMetadata":
        manifest = json.loads((ROOT / "data/manifests/m5_ca1_foods_features_v1.json").read_text(encoding="utf-8"))
        codes = manifest["categorical_encodings"]
        raw_calendar = ROOT / "data/raw/m5/calendar.csv"
        if not raw_calendar.is_file():
            raise ConflictError("required M5-compatible calendar metadata is unavailable")
        calendar = pd.read_csv(raw_calendar, usecols=["date", "d", "wday", "month", "year", "snap_CA", "event_name_1", "event_type_1", "event_name_2", "event_type_2"])
        calendar["date"] = pd.to_datetime(calendar["date"])
        return cls(
            feature_names=tuple(manifest["feature_names"]),
            encodings=FeatureEncodings(item_codes={key: int(value) for key, value in codes["item_id"].items()}, dept_codes={key: int(value) for key, value in codes["dept_id"].items()}, event_codes={key: {name: int(code) for name, code in values.items()} for key, values in codes["event_categories"].items()}),
            known_items=frozenset(codes["item_id"]),
            calendar=calendar,
        )


class ForecastService:
    """Runs the frozen model only in its M5 CA_1/FOODS deployment context."""

    def __init__(self, session: Session, metadata: FrozenMetadata | None = None, model_loader: Callable[[], object] | None = None) -> None:
        self.session = session
        self.repo = SalesForecastRepository()
        self.metadata = metadata
        self.model_loader = model_loader or _cached_model

    def _metadata(self) -> FrozenMetadata:
        return self.metadata or FrozenMetadata.load()

    @staticmethod
    def _dept_from_sku(sku: str) -> str:
        return "_".join(sku.split("_")[:2])

    def _products(self, product_ids: list[int], metadata: FrozenMetadata) -> list[Product]:
        products: list[Product] = []
        for product_id in product_ids:
            product = self.session.get(Product, product_id)
            if product is None:
                raise NotFoundError("product not found")
            if not product.is_active:
                raise ConflictError("inactive products cannot be forecast")
            if product.sku not in metadata.known_items:
                raise ConflictError("this SKU is not in the frozen M5 vocabulary; reliable forecasting requires retraining on the target store data")
            if self._dept_from_sku(product.sku) not in metadata.encodings.dept_codes:
                raise ConflictError("the frozen M5 department identity is unavailable for this SKU")
            products.append(product)
        return products

    def _histories(self, products: list[Product]) -> tuple[np.ndarray, np.ndarray]:
        start = ORIGIN_DATE - timedelta(days=27)
        demand_rows: list[list[float]] = []
        price_rows: list[list[float]] = []
        expected_dates = [start + timedelta(days=index) for index in range(28)]
        for product in products:
            history = self.repo.product_history_between(self.session, product.id, start, ORIGIN_DATE)
            if [row.sale_date for row in history] != expected_dates:
                raise ConflictError("product requires 28 contiguous daily sales records through the M5 demo origin (2016-04-24)")
            demand_rows.append([float(row.quantity_sold) for row in history])
            price_rows.append([np.nan if row.sell_price is None else float(row.sell_price) for row in history])
        return np.asarray(demand_rows, dtype=np.float32), np.asarray(price_rows, dtype=np.float32)

    def _future_calendar(self, metadata: FrozenMetadata, horizon: int) -> pd.DataFrame:
        start = pd.Timestamp(ORIGIN_DATE + timedelta(days=1))
        end = pd.Timestamp(ORIGIN_DATE + timedelta(days=horizon))
        future = metadata.calendar.loc[(metadata.calendar["date"] >= start) & (metadata.calendar["date"] <= end)].copy()
        if len(future) != horizon or future["date"].tolist() != list(pd.date_range(start, end, freq="D")):
            raise ConflictError("required M5-compatible calendar metadata is incomplete")
        return future.reset_index(drop=True)

    @staticmethod
    def _schema(metadata: FrozenMetadata) -> dict[str, list[int]]:
        # This is the exact categorical field set and finite vocabulary used by FEATURE_SET_V1.
        return {
            "item_code": sorted(metadata.encodings.item_codes.values()),
            "dept_code": sorted(metadata.encodings.dept_codes.values()),
            "wday": list(range(1, 8)), "month": list(range(1, 13)), "year": list(range(2011, 2017)),
            "is_weekend": [0, 1], "snap_CA": [0, 1],
            **{f"{name}_code": sorted(codes.values()) for name, codes in metadata.encodings.event_codes.items()},
        }

    @staticmethod
    def _as_response(run: ForecastRun) -> dict:
        grouped: dict[int, list[ForecastValue]] = {}
        for value in sorted(run.values, key=lambda item: (item.product_id, item.horizon_day)):
            grouped.setdefault(value.product_id, []).append(value)
        totals = {}
        for product_id, values in grouped.items():
            totals[product_id] = {
                "days_7": sum((value.predicted_demand for value in values[:7]), Decimal("0")) if len(values) >= 7 else None,
                "days_14": sum((value.predicted_demand for value in values[:14]), Decimal("0")) if len(values) >= 14 else None,
                "days_28": sum((value.predicted_demand for value in values[:28]), Decimal("0")) if len(values) >= 28 else None,
            }
        return {"id": run.id, "model_name": run.model_name, "feature_set": run.feature_set, "model_version": run.model_version, "history_end_date": run.history_end_date, "forecast_start_date": run.forecast_start_date, "horizon_days": run.horizon_days, "generated_at": run.generated_at, "values": [value for values in grouped.values() for value in values], "totals_by_product": totals}

    def create(self, data: ForecastCreate) -> dict:
        metadata = self._metadata()
        products = self._products(data.product_ids, metadata)
        sales, prices = self._histories(products)
        calendar = self._future_calendar(metadata, data.horizon_days)
        config = load_feature_config(ROOT / "configs/features/ml_features_v1.yaml")
        model = self.model_loader()
        model_metadata = pd.DataFrame({"item_id": [product.sku for product in products], "dept_id": [self._dept_from_sku(product.sku) for product in products]})
        try:
            forecast = recursive_forecast(lambda features: predict_checked(model, features, self._schema(metadata)), sales, prices, calendar, model_metadata, metadata.encodings, config, metadata.feature_names)
        except (ValueError, KeyError) as exc:
            raise ConflictError("frozen M5 forecasting failed for the supplied compatible history") from exc
        run = ForecastRun(model_name="XGBOOST_V1", feature_set="FEATURE_SET_V1", model_version=MODEL_VERSION, history_end_date=ORIGIN_DATE, forecast_start_date=ORIGIN_DATE + timedelta(days=1), horizon_days=data.horizon_days)
        self.session.add(run)
        self.session.flush()
        for product_index, product in enumerate(products):
            for horizon_index, prediction in enumerate(forecast[product_index], start=1):
                self.session.add(ForecastValue(forecast_run_id=run.id, product_id=product.id, forecast_date=ORIGIN_DATE + timedelta(days=horizon_index), horizon_day=horizon_index, predicted_demand=Decimal(str(prediction)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)))
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("forecast persistence failed; no partial forecast was saved") from exc
        persisted = self.repo.forecast_run(self.session, run.id)
        if persisted is None:
            raise ConflictError("forecast persistence failed")
        return self._as_response(persisted)

    def runs(self, limit: int, offset: int) -> list[dict]:
        return [self._as_response(run) for run in self.repo.forecast_runs(self.session, limit, offset)]

    def run(self, run_id: int) -> dict:
        run = self.repo.forecast_run(self.session, run_id)
        if run is None:
            raise NotFoundError("forecast run not found")
        return self._as_response(run)

    def latest(self, product_id: int) -> dict:
        if self.session.get(Product, product_id) is None:
            raise NotFoundError("product not found")
        run = self.repo.latest_run_for_product(self.session, product_id)
        if run is None:
            raise NotFoundError("forecast not found")
        result = self._as_response(run)
        result["values"] = [value for value in result["values"] if value.product_id == product_id]
        result["totals_by_product"] = {product_id: result["totals_by_product"][product_id]}
        return result
