"""Generate P25-03 reliability evidence from pre-TEST rolling V1 artifacts only.

The script reloads the already-created four rolling V1 artifacts.  It never
trains/replaces V1 and deliberately opens each fold's actuals only after that
fold's recursive point forecast is complete.  It imports no final-TEST loader.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ml.data.m5_ca1_foods import load_rolling_fold_actuals
from ml.evaluation.forecast_reliability import (
    apply_intervals, assert_pretest_folds, calibration_table, evidence_level,
    residuals, sparsity_band,
)
from ml.evaluation.metrics import aggregate_metrics
from ml.features.builder import _feature_names, load_feature_config
from ml.models.lightgbm_model import CATEGORICAL_FEATURES
from ml.models.xgboost_model import load_model_config, load_saved_model
from scripts.ml.run_xgboost_v3_research import _fold_context, _forecast


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_revision() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _metrics(frame: pd.DataFrame) -> dict[str, float | int | None]:
    actual = frame["actual"].to_numpy(float)
    forecast = frame["point_forecast"].to_numpy(float)
    absolute = np.abs(actual - forecast)
    denominator = float(actual.sum())
    return {
        "observations": int(len(frame)), "MAE": float(absolute.mean()),
        "RMSE": float(np.sqrt(np.square(actual - forecast).mean())),
        "WAPE_percent": None if denominator == 0 else float(100 * absolute.sum() / denominator),
        "mean_signed_error": float((actual - forecast).mean()),
    }


def _interval_metrics(frame: pd.DataFrame, coverage: float) -> dict[str, float | int]:
    inside = (frame["actual"] >= frame["lower_bound"]) & (frame["actual"] <= frame["upper_bound"])
    return {
        "coverage_level": float(coverage), "observations": int(len(frame)),
        "nominal_coverage_percent": float(coverage * 100),
        "empirical_coverage_percent": float(inside.mean() * 100),
        "average_interval_width": float(frame["interval_width"].mean()),
        "under_coverage_percent": float(max(0, coverage * 100 - inside.mean() * 100)),
        "over_coverage_percent": float(max(0, inside.mean() * 100 - coverage * 100)),
    }


def _residual_frame(fold: str, item_ids: tuple[str, ...], actual: np.ndarray, forecast: np.ndarray, zero_rate: np.ndarray) -> pd.DataFrame:
    matrix = residuals(actual, forecast)
    series, horizon = actual.shape
    if horizon != 28 or len(item_ids) != series:
        raise ValueError("unexpected rolling V1 forecast shape")
    return pd.DataFrame({
        "fold": fold,
        "sku": np.repeat(np.asarray(item_ids, dtype=str), horizon),
        "horizon_day": np.tile(np.arange(1, horizon + 1), series),
        "zero_rate_56": np.repeat(zero_rate, horizon),
        "sparsity_band": np.repeat(sparsity_band(zero_rate), horizon),
        "actual": actual.reshape(-1), "point_forecast": forecast.reshape(-1), "residual": matrix.reshape(-1),
    })


def _reference_payload(calibration: pd.DataFrame, products: pd.DataFrame, thresholds: dict, config: dict, evaluation: list[dict]) -> dict:
    interval_rows = calibration.loc[calibration["usable"]].copy()
    for column in ("horizon_day", "sparsity_band"):
        interval_rows[column] = interval_rows[column].where(interval_rows[column].notna(), None)
    return {
        "reference_version": "P25-03 empirical-residual-v1",
        "model_name": "XGBOOST_V1", "feature_set": "FEATURE_SET_V1",
        "source": "four pre-TEST expanding rolling folds ending d_1913",
        "test_actuals_accessed": False,
        "minimum_calibration_sample_size": int(config["minimum_calibration_sample_size"]),
        "intervals": interval_rows.to_dict(orient="records"),
        "independent_fold_4_calibration": evaluation,
        "product_thresholds": thresholds,
        "products": {row.sku: {
            "historical_mae": row.MAE, "historical_rmse": row.RMSE,
            "mean_signed_error": row.mean_signed_error, "zero_rate_56": row.zero_rate_56,
            "sparsity_band": row.sparsity_band, "mean_80_width": row.mean_80_width,
            "evidence_level": row.evidence_level, "evidence_reason": row.evidence_reason,
            "fold_observations": int(row.fold_observations),
        } for row in products.itertuples(index=False)},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data/raw/m5")
    parser.add_argument("--protocol", type=Path, default=ROOT / "configs/data/m5_ca1_foods.yaml")
    parser.add_argument("--config", type=Path, default=ROOT / "configs/experiments/forecast_reliability_v1.yaml")
    parser.add_argument("--model-config", type=Path, default=ROOT / "configs/models/xgboost_v1.yaml")
    parser.add_argument("--models-dir", type=Path, default=ROOT / "artifacts/models")
    parser.add_argument("--tables-dir", type=Path, default=ROOT / "reports/tables")
    parser.add_argument("--manifests-dir", type=Path, default=ROOT / "data/manifests")
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    folds = config["folds"]
    assert_pretest_folds(folds)
    if config.get("test_policy") != "NEVER_LOAD_TEST_ACTUALS_D_1914_TO_D_1941":
        raise ValueError("reliability research requires explicit final-TEST exclusion")
    model_config = load_model_config(args.model_config)
    feature_config = load_feature_config(ROOT / "configs/features/ml_features_v1.yaml")
    all_rows: list[pd.DataFrame] = []
    fold_rows: list[dict] = []
    artifacts: list[dict] = []

    for definition in folds:
        context = _fold_context(args.raw_dir, args.protocol, definition)
        feature_names = _feature_names(feature_config)
        schema = {column: context.schema_levels[column] for column in CATEGORICAL_FEATURES if column in feature_names}
        model_path = args.models_dir / definition["model"]
        if not model_path.is_file():
            raise FileNotFoundError(f"missing existing rolling V1 artifact: {model_path}")
        # Point forecasts finish before this fold's actuals are opened below.
        forecast = _forecast(load_saved_model(model_config, model_path), schema, context, feature_config, feature_names)
        if forecast.shape != (1437, 28) or not np.isfinite(forecast).all() or (forecast < 0).any():
            raise ValueError("saved V1 artifact violated the recursive point-forecast contract")
        item_ids, actual, _ = load_rolling_fold_actuals(args.raw_dir, args.protocol, definition["validation_start_d"], definition["validation_end_d"])
        expected_ids = tuple(context.source.metadata["item_id"].astype(str))
        if item_ids != expected_ids:
            raise ValueError("item order changed between prediction and scoring")
        zero_rate = (context.source.train_sales[:, -56:] == 0).mean(axis=1)
        rows = _residual_frame(definition["name"], item_ids, actual, forecast, zero_rate)
        all_rows.append(rows)
        fold_rows.append({"fold": definition["name"], **definition, **aggregate_metrics(actual, forecast), "mean_signed_error": float(rows["residual"].mean())})
        artifacts.append({"fold": definition["name"], "model": definition["model"], "sha256": _digest(model_path), "point_forecast_unchanged": True})

    residual_rows = pd.concat(all_rows, ignore_index=True)
    calibration_cfg = config["calibration"]
    pool = residual_rows.loc[residual_rows["fold"].isin(calibration_cfg["evaluation_calibration_folds"])]
    evaluation = residual_rows.loc[residual_rows["fold"].eq(calibration_cfg["evaluation_fold"])].copy()
    coverages = [float(value) for value in calibration_cfg["coverage_levels"]]
    evaluation_calibration = calibration_table(pool, coverages, int(config["minimum_calibration_sample_size"]))
    production_calibration = calibration_table(residual_rows, coverages, int(config["minimum_calibration_sample_size"]))

    calibration_results: list[dict] = []
    interval_horizon: list[dict] = []
    for coverage in coverages:
        scored = apply_intervals(evaluation, evaluation_calibration, coverage)
        result = _interval_metrics(scored, coverage)
        calibration_results.append({"stage": "fold_4_independent_evaluation", "calibration_folds": "fold_1,fold_2,fold_3", **result})
        for horizon, group in scored.groupby("horizon_day", observed=True):
            interval_horizon.append({"stage": "fold_4_independent_evaluation", "horizon_day": int(horizon), **_interval_metrics(group, coverage)})

    by_fold = pd.DataFrame(fold_rows)
    overall = pd.DataFrame([{
        **_metrics(residual_rows), "aggregation": "pooled_observations", "folds": 4,
        "mean_fold_MAE": float(by_fold["MAE"].mean()), "mean_fold_RMSE": float(by_fold["RMSE"].mean()),
        "mean_fold_WAPE_percent": float(by_fold["WAPE_percent"].mean()),
        "model_name": "XGBOOST_V1", "feature_set": "FEATURE_SET_V1",
    }])
    by_horizon = pd.DataFrame([{"horizon_day": int(day), **_metrics(group)} for day, group in residual_rows.groupby("horizon_day", observed=True)])
    by_sparsity = pd.DataFrame([{"sparsity_band": str(band), **_metrics(group)} for band, group in residual_rows.groupby("sparsity_band", observed=True)])

    production_80 = apply_intervals(residual_rows, production_calibration, .80)
    product = production_80.groupby("sku", observed=True).apply(lambda group: pd.Series({
        "MAE": _metrics(group)["MAE"], "RMSE": _metrics(group)["RMSE"], "mean_signed_error": _metrics(group)["mean_signed_error"],
        "zero_rate_56": float(group["zero_rate_56"].mean()), "sparsity_band": str(group["sparsity_band"].mode().iloc[0]),
        "mean_80_width": float(group["interval_width"].mean()), "fold_observations": int(len(group)),
    }), include_groups=False).reset_index()
    thresholds = {"mae_p50": float(product["MAE"].quantile(.50)), "mae_p75": float(product["MAE"].quantile(.75)), "width_p50": float(product["mean_80_width"].quantile(.50)), "width_p75": float(product["mean_80_width"].quantile(.75))}
    product["evidence_level"] = product.apply(lambda row: evidence_level(row.zero_rate_56, row.MAE, row.mean_80_width, **thresholds), axis=1)
    product["evidence_reason"] = product.apply(lambda row: "Highly intermittent demand or a wide/higher-error historical backtest." if row.evidence_level == "LIMITED" else ("Regular demand with below-median historical error and interval width." if row.evidence_level == "HIGHER" else "Comparable historical evidence is mixed; review the range and inputs."), axis=1)

    args.tables_dir.mkdir(parents=True, exist_ok=True)
    args.manifests_dir.mkdir(parents=True, exist_ok=True)
    overall.to_csv(args.tables_dir / "forecast_reliability_overall.csv", index=False)
    by_fold.to_csv(args.tables_dir / "forecast_reliability_by_fold.csv", index=False)
    by_horizon.to_csv(args.tables_dir / "forecast_reliability_by_horizon.csv", index=False)
    by_sparsity.to_csv(args.tables_dir / "forecast_reliability_by_sparsity.csv", index=False)
    pd.DataFrame(calibration_results).to_csv(args.tables_dir / "forecast_interval_calibration.csv", index=False)
    pd.DataFrame(interval_horizon).to_csv(args.tables_dir / "forecast_interval_by_horizon.csv", index=False)
    product.to_csv(args.tables_dir / "forecast_reliability_by_product.csv", index=False)
    reference = _reference_payload(production_calibration, product, thresholds, config, calibration_results)
    manifest = {"experiment_id": config["experiment_id"], "git_revision": _git_revision(), "test_actuals_accessed": False, "folds": folds, "model_artifacts": artifacts, "calibration_protocol": {"evaluation": "fold_1-3 residuals calibrate; fold_4 evaluates", "production_reference": "all four pre-TEST folds after evaluation", "minimum_sample_size": int(config["minimum_calibration_sample_size"])}, "outputs": ["forecast_reliability_overall.csv", "forecast_reliability_by_fold.csv", "forecast_reliability_by_horizon.csv", "forecast_reliability_by_sparsity.csv", "forecast_interval_calibration.csv", "forecast_interval_by_horizon.csv", "forecast_reliability_by_product.csv"]}
    (args.manifests_dir / "forecast_reliability_reference.json").write_text(json.dumps(reference, indent=2, default=float), encoding="utf-8")
    (args.manifests_dir / "forecast_reliability_v1.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"test_actuals_accessed": False, "rows": int(len(residual_rows)), "fold_4_interval_evaluation": calibration_results}, indent=2))


if __name__ == "__main__":
    main()
