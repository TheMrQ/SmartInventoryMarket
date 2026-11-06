"""P23 validation-only, leakage-safe XGBoost V2 candidate study.

No TEST sales loader is imported. All V1/V2 recursive predictions are generated
from d_1..d_1885 before the sole validation-actual read for d_1886..d_1913.
Large model JSON files remain ignored; only aggregate tables/manifests are saved.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ml.data.m5_ca1_foods import load_training_feature_source, load_validation_dataset
from ml.evaluation.forecast_analysis import horizon_metrics
from ml.evaluation.metrics import aggregate_metrics, per_series_metrics
from ml.features.builder import build_daily_price_matrix, build_encodings, build_training_features, encode_calendar_features, load_feature_config, load_train_price_rows
from ml.models.recursive import recursive_forecast
from ml.models.xgboost_model import fit_global_model, load_model_config, load_saved_model, predict_checked


def feature_names(config: dict) -> list[str]:
    return [
        *[f"lag_{value}" for value in config["sales_lags"]],
        *[f"rolling_mean_{value}" for value in config["rolling_mean_windows"]],
        *[f"rolling_std_{value}" for value in config["rolling_std_windows"]],
        "wday", "month", "year", "is_weekend", "snap_CA",
        "event_name_1_code", "event_type_1_code", "event_name_2_code", "event_type_2_code",
        "item_code", "dept_code", *config["price_features"],
    ]


def candidate_config(candidate: dict, seed: int) -> dict:
    required = {"name", "objective", "n_estimators", "learning_rate", "max_depth", "min_child_weight", "subsample", "colsample_bytree", "reg_alpha", "reg_lambda"}
    if required.difference(candidate) or candidate["objective"] not in {"count:poisson", "reg:squarederror"}:
        raise ValueError("invalid V2 candidate definition")
    return {"model_name": candidate["name"], "feature_set": "FEATURE_SET_V2", "tree_method": "hist", "random_state": seed, "n_jobs": -1, **{key: candidate[key] for key in required if key != "name"}}


def select_candidate(results: pd.DataFrame) -> tuple[pd.Series, bool]:
    """Choose only a strictly lower-WAPE candidate with no secondary regression."""
    baseline = results.loc[results["candidate"].eq("XGBOOST_V1")]
    if len(baseline) != 1:
        raise ValueError("Exactly one immutable XGBOOST_V1 comparison row is required")
    contenders = results.loc[~results["candidate"].eq("XGBOOST_V1")]
    if contenders.empty:
        raise ValueError("At least one V2 candidate is required")
    best = contenders.sort_values(["WAPE_percent", "MAE", "RMSE"], kind="stable").iloc[0]
    reference = baseline.iloc[0]
    selected = bool(
        best["WAPE_percent"] < reference["WAPE_percent"]
        and best["MAE"] <= reference["MAE"]
        and best["RMSE"] <= reference["RMSE"]
    )
    return best, selected


def _schema_levels(encodings, train_calendar: pd.DataFrame, validation_calendar: pd.DataFrame) -> dict[str, list[int]]:
    encoded = encode_calendar_features(pd.concat([train_calendar, validation_calendar], ignore_index=True), encodings)
    levels = {column: sorted(encoded[column].astype(int).unique().tolist()) for column in encoded.columns}
    levels["item_code"] = sorted(encodings.item_codes.values())
    levels["dept_code"] = sorted(encodings.dept_codes.values())
    return levels


def _digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _forecast(model, schema, source, prices, encodings, config, names) -> np.ndarray:
    return recursive_forecast(
        lambda frame: predict_checked(model, frame, schema), source.train_sales, prices,
        source.validation_calendar, source.metadata, encodings, config, names,
    )


def _error_profile(actual: np.ndarray, forecast: np.ndarray, items: tuple[str, ...], horizon: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    errors = forecast - actual
    per_sku = per_series_metrics(actual, forecast, items)
    volume = actual.sum(axis=1)
    labels = pd.qcut(pd.Series(volume).rank(method="first"), 4, labels=["low", "mid_low", "mid_high", "high"])
    volume_frame = pd.DataFrame({"volume_band": labels, "absolute_error": np.abs(errors).mean(axis=1), "bias": errors.mean(axis=1)})
    by_volume = volume_frame.groupby("volume_band", observed=True).agg(skus=("absolute_error", "size"), MAE=("absolute_error", "mean"), bias=("bias", "mean")).reset_index()
    profile = {
        "zero_total_validation_skus": int((volume == 0).sum()),
        "intermittent_skus_at_least_75pct_zero": int(((actual == 0).mean(axis=1) >= 0.75).sum()),
        "mean_bias": float(errors.mean()), "overprediction_share": float((errors > 0).mean()),
        "underprediction_share": float((errors < 0).mean()),
        "first_7_mae": float(horizon.iloc[:7]["MAE"].mean()), "last_7_mae": float(horizon.iloc[-7:]["MAE"].mean()),
        "per_sku_mae_median": float(per_sku["MAE"].median()), "per_sku_mae_p90": float(per_sku["MAE"].quantile(0.9)),
    }
    return profile, by_volume


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data/raw/m5")
    parser.add_argument("--protocol", type=Path, default=ROOT / "configs/data/m5_ca1_foods.yaml")
    parser.add_argument("--research-config", type=Path, default=ROOT / "configs/experiments/xgboost_v2_research.yaml")
    parser.add_argument("--feature-config", type=Path, default=ROOT / "configs/features/ml_features_v2.yaml")
    parser.add_argument("--v1-feature-config", type=Path, default=ROOT / "configs/features/ml_features_v1.yaml")
    parser.add_argument("--v1-model-config", type=Path, default=ROOT / "configs/models/xgboost_v1.yaml")
    parser.add_argument("--v1-model", type=Path, default=ROOT / "artifacts/models/xgboost_v1.json")
    parser.add_argument("--tables-dir", type=Path, default=ROOT / "reports/tables")
    parser.add_argument("--manifests-dir", type=Path, default=ROOT / "data/manifests")
    parser.add_argument("--models-dir", type=Path, default=ROOT / "artifacts/models")
    args = parser.parse_args()

    research = yaml.safe_load(args.research_config.read_text(encoding="utf-8"))
    v2_features = load_feature_config(args.feature_config)
    v1_features = load_feature_config(args.v1_feature_config)
    names_v2, names_v1 = feature_names(v2_features), feature_names(v1_features)
    if len(names_v2) <= len(names_v1) or int(v2_features["warmup_days"]) != 56:
        raise ValueError("V2 must be a separate extended-feature, 56-day-warmup study")
    source = load_training_feature_source(args.raw_dir, args.protocol)
    item_ids = tuple(source.metadata["item_id"].astype(str))
    encodings = build_encodings(source.metadata, pd.concat([source.train_calendar, source.validation_calendar], ignore_index=True))
    schema_levels = _schema_levels(encodings, source.train_calendar, source.validation_calendar)
    price_rows = load_train_price_rows(args.raw_dir, item_ids, source.train_calendar)
    prices = build_daily_price_matrix(price_rows, item_ids, source.train_calendar)

    # V1 error evidence is reproduced from its immutable artifact before actuals are read.
    v1_model_config = load_model_config(args.v1_model_config)
    v1_model = load_saved_model(v1_model_config, args.v1_model)
    from ml.models.xgboost_model import build_categorical_schema
    v1_cache = pd.read_pickle(ROOT / "data/processed/m5_ca1_foods_features_v1.pkl.gz")
    v1_schema = build_categorical_schema(v1_cache.loc[:, names_v1], schema_levels)
    v1_forecast = _forecast(v1_model, v1_schema, source, prices, encodings, v1_features, names_v1)

    v2_build = build_training_features(source.metadata, source.train_sales, source.train_calendar, pd.concat([source.train_calendar, source.validation_calendar], ignore_index=True), prices, v2_features)
    if set(names_v2).difference(v2_build.frame.columns):
        raise ValueError("V2 training features are incomplete")
    candidates: list[dict] = []
    args.models_dir.mkdir(parents=True, exist_ok=True)
    # Generate every candidate forecast before opening validation actuals.
    for candidate in research["candidates"]:
        config = candidate_config(candidate, int(research["random_state"]))
        started = time.perf_counter()
        model, schema = fit_global_model(v2_build.frame.loc[:, names_v2], v2_build.frame["sales_target"], config, schema_levels)
        seconds = time.perf_counter() - started
        model_path = args.models_dir / f"{candidate['name'].lower()}.json"
        model.save_model(model_path)
        reloaded = load_saved_model(config, model_path)
        probe = v2_build.frame.loc[:7, names_v2]
        if not np.allclose(predict_checked(model, probe, schema), predict_checked(reloaded, probe, schema)):
            raise ValueError(f"{candidate['name']} JSON reload changed probe predictions")
        try:
            forecast = _forecast(model, schema, source, prices, encodings, v2_features, names_v2)
        except ValueError as exc:
            if "negative" not in str(exc).lower():
                raise
            # Never clip or score an invalid count forecast.  Recording this
            # separately lets the other predeclared candidates finish without
            # opening validation actuals early.
            candidates.append({
                "candidate": candidate, "training_seconds": seconds, "model_path": model_path,
                "forecast": None, "disqualification_reason": str(exc),
            })
            continue
        candidates.append({
            "candidate": candidate, "training_seconds": seconds, "model_path": model_path,
            "forecast": forecast, "disqualification_reason": None,
        })

    validation = load_validation_dataset(args.raw_dir, args.protocol)
    actual = pd.DataFrame(validation.validation_actuals, index=validation.item_ids).loc[list(item_ids)].to_numpy()
    v1_metrics = aggregate_metrics(actual, v1_forecast)
    v1_horizon = horizon_metrics(actual, v1_forecast, validation.validation_dates)
    profile, volume = _error_profile(actual, v1_forecast, item_ids, v1_horizon)
    rows = [{"candidate": "XGBOOST_V1", "feature_count": len(names_v1), "training_seconds": 109.747, "model_size_MiB": args.v1_model.stat().st_size / 1024**2, "model_sha256": _digest(args.v1_model), **v1_metrics, "raw_min_prediction": float(v1_forecast.min())}]
    horizons = [v1_horizon.assign(candidate="XGBOOST_V1")]
    for run in candidates:
        candidate = run["candidate"]
        model_path = run["model_path"]
        forecast = run["forecast"]
        if forecast is None:
            rows.append({
                "candidate": candidate["name"], "feature_count": len(names_v2),
                "training_seconds": run["training_seconds"], "model_size_MiB": model_path.stat().st_size / 1024**2,
                "model_sha256": _digest(model_path), "MAE": np.nan, "RMSE": np.nan,
                "WAPE_percent": np.nan, "raw_min_prediction": np.nan,
                "disqualification_reason": run["disqualification_reason"],
            })
            continue
        raw_min = float(forecast.min())
        if raw_min < 0:
            raise ValueError(f"{candidate['name']} produced negative forecasts and is disqualified; no clipping is applied")
        metrics = aggregate_metrics(actual, forecast)
        rows.append({"candidate": candidate["name"], "feature_count": len(names_v2), "training_seconds": run["training_seconds"], "model_size_MiB": model_path.stat().st_size / 1024**2, "model_sha256": _digest(model_path), **metrics, "raw_min_prediction": raw_min, "disqualification_reason": None})
        horizons.append(horizon_metrics(actual, forecast, validation.validation_dates).assign(candidate=candidate["name"]))
    results = pd.DataFrame(rows)
    baseline = results.iloc[0]
    for metric in ("MAE", "RMSE", "WAPE_percent"):
        results[f"{metric}_improvement_vs_v1_pct"] = (baseline[metric] - results[metric]) / baseline[metric] * 100
    scored_results = results.loc[results[["MAE", "RMSE", "WAPE_percent"]].notna().all(axis=1)].copy()
    best, selected = select_candidate(scored_results)
    results["selected_by_protocol"] = results["candidate"].eq(best["candidate"]) & selected
    args.tables_dir.mkdir(parents=True, exist_ok=True); args.manifests_dir.mkdir(parents=True, exist_ok=True)
    results.to_csv(args.tables_dir / "xgboost_v2_validation_results.csv", index=False)
    pd.concat(horizons, ignore_index=True).to_csv(args.tables_dir / "xgboost_v2_horizon_metrics.csv", index=False)
    volume.to_csv(args.tables_dir / "xgboost_v1_error_by_validation_volume.csv", index=False)
    manifest = {"experiment": research["experiment_id"], "selection_status": "SELECTED" if selected else "NO_CANDIDATE_SELECTED", "best_candidate": str(best["candidate"]), "v1_error_profile": profile, "feature_schema": {"name": v2_features["feature_set"], "count": len(names_v2), "names": names_v2, "warmup_days": v2_features["warmup_days"]}, "validation": {"train_end": "d_1885", "validation": "d_1886:d_1913", "prediction_count": 40236}, "test_policy": research["test_policy"], "direct_multi_horizon": research["direct_multi_horizon"], "results": results.to_dict(orient="records")}
    (args.manifests_dir / "xgboost_v2_validation.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"best_candidate": str(best["candidate"]), "selected": selected, "metrics": best[["MAE", "RMSE", "WAPE_percent"]].to_dict(), "v1": baseline[["MAE", "RMSE", "WAPE_percent"]].to_dict()}, indent=2))


if __name__ == "__main__":
    main()
