"""Train XGBOOST_V1 and recursively evaluate only the frozen validation span."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
import xgboost

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT))

from ml.data.m5_ca1_foods import load_training_feature_source, load_validation_dataset
from ml.evaluation.forecast_analysis import compare_candidate_to_references, horizon_metrics
from ml.evaluation.metrics import aggregate_metrics, per_series_metrics
from ml.features.builder import (
    build_daily_price_matrix, build_encodings, encode_calendar_features,
    load_feature_config, load_train_price_rows,
)
from ml.models.recursive import recursive_forecast
from ml.models.xgboost_model import fit_global_model, load_model_config, load_saved_model, predict_checked


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _versions() -> dict[str, str]:
    return {
        "python": sys.version.split()[0], "xgboost": xgboost.__version__,
        "pandas": pd.__version__, "numpy": np.__version__, "scikit_learn": sklearn.__version__,
    }


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)


def _feature_names(config: dict) -> list[str]:
    return [
        *[f"lag_{value}" for value in config["sales_lags"]],
        *[f"rolling_mean_{value}" for value in config["rolling_mean_windows"]],
        *[f"rolling_std_{value}" for value in config["rolling_std_windows"]],
        "wday", "month", "year", "is_weekend", "snap_CA",
        "event_name_1_code", "event_type_1_code", "event_name_2_code", "event_type_2_code",
        "item_code", "dept_code", *config["price_features"],
    ]


def _extra_category_levels(encodings, train_calendar: pd.DataFrame, validation_calendar: pd.DataFrame) -> dict[str, list[int]]:
    """Include all calendar/event codes known for the recursive validation period."""
    calendar = encode_calendar_features(pd.concat([train_calendar, validation_calendar], ignore_index=True), encodings)
    levels = {column: sorted(calendar[column].astype(int).unique().tolist()) for column in calendar.columns}
    levels["item_code"] = sorted(encodings.item_codes.values())
    levels["dept_code"] = sorted(encodings.dept_codes.values())
    return levels


def _plot_model_comparison(metrics: pd.DataFrame, path: Path) -> None:
    measures = [("MAE", "MAE"), ("RMSE", "RMSE"), ("WAPE_percent", "WAPE (%)")]
    colors = ["#4C78A8", "#F58518", "#54A24B", "#B279A2"]
    figure, axes = plt.subplots(1, 3, figsize=(15, 4.8), constrained_layout=True)
    for axis, (column, label) in zip(axes, measures, strict=True):
        values = metrics[column].to_numpy(dtype=float)
        bars = axis.bar(metrics["Method"], values, color=colors)
        axis.set_title(label)
        axis.set_ylabel(label)
        axis.tick_params(axis="x", rotation=16)
        for bar, value in zip(bars, values, strict=True):
            axis.text(bar.get_x() + bar.get_width() / 2, value, f"{value:.3f}", ha="center", va="bottom", fontsize=8)
    figure.suptitle("M5 CA_1/FOODS: Four-Method Validation Comparison", fontsize=13)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _plot_importance(importance: pd.DataFrame, path: Path) -> None:
    top = importance.head(15).iloc[::-1]
    figure, axis = plt.subplots(figsize=(8, 6), constrained_layout=True)
    axis.barh(top["feature"], top["gain_importance"], color="#B279A2")
    axis.set_title("XGBOOST_V1 Top Feature Importance by Gain")
    axis.set_xlabel("Gain importance")
    axis.set_ylabel("Feature")
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _plot_horizon(horizon: pd.DataFrame, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 4.5), constrained_layout=True)
    axis.plot(horizon["horizon"], horizon["MAE"], marker="o", color="#B279A2")
    axis.set_title("XGBOOST_V1 Recursive Validation MAE by Horizon")
    axis.set_xlabel("Forecast horizon (days ahead)")
    axis.set_ylabel("Aggregate MAE")
    axis.set_xticks(range(1, 29, 2))
    axis.grid(axis="y", alpha=0.3)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _plot_horizon_comparison(lightgbm: pd.DataFrame, xgboost_horizon: pd.DataFrame, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 4.5), constrained_layout=True)
    axis.plot(lightgbm["horizon"], lightgbm["MAE"], marker="o", label="LIGHTGBM_V1", color="#54A24B")
    axis.plot(xgboost_horizon["horizon"], xgboost_horizon["MAE"], marker="o", label="XGBOOST_V1", color="#B279A2")
    axis.set_title("Recursive Validation MAE: LightGBM vs XGBoost")
    axis.set_xlabel("Forecast horizon (days ahead)")
    axis.set_ylabel("Aggregate MAE")
    axis.set_xticks(range(1, 29, 2))
    axis.legend()
    axis.grid(axis="y", alpha=0.3)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _plot_aggregate_totals(actual: np.ndarray, forecast: np.ndarray, path: Path) -> None:
    x = np.arange(1, forecast.shape[1] + 1)
    figure, axis = plt.subplots(figsize=(10, 4.8), constrained_layout=True)
    axis.plot(x, actual.sum(axis=0), marker="o", label="Actual sales", color="#4C78A8")
    axis.plot(x, forecast.sum(axis=0), marker="o", label="XGBOOST_V1 forecast", color="#B279A2")
    axis.set_title("M5 CA_1/FOODS: Aggregate Validation Actual vs Forecast")
    axis.set_xlabel("Validation day (d_1886 to d_1913)")
    axis.set_ylabel("Total daily units across 1,437 SKUs")
    axis.legend()
    axis.grid(axis="y", alpha=0.3)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _plot_per_sku_mae(xgboost_metrics: pd.DataFrame, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 5), constrained_layout=True)
    axis.hist(xgboost_metrics["MAE"], bins=35, color="#B279A2", edgecolor="white")
    axis.set_title("XGBOOST_V1 Per-SKU Validation MAE Distribution")
    axis.set_xlabel("28-day per-SKU MAE (units/day)")
    axis.set_ylabel("Number of SKUs")
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _summary(
    config: dict, schema: dict[str, list[int]], training_seconds: float, model_path: Path,
    metrics: pd.DataFrame, per_sku: pd.DataFrame, horizon: pd.DataFrame,
    importance: pd.DataFrame, versions: dict[str, str], runtime: pd.DataFrame, path: Path,
) -> None:
    xgb = metrics.loc[metrics["Method"] == "XGBOOST_V1"].iloc[0]
    lines = [
        "# XGBOOST_V1 Validation Summary", "",
        "XGBOOST_V1 is an initial / untuned global one-step model. `count:poisson` is its training objective; MAE, RMSE, and WAPE remain the thesis metrics.", "",
        "## Training Setup", "",
        "- One global CPU XGBoost model trained on 2,668,509 SKU-day rows from 1,437 CA_1/FOODS series using the unchanged 25-feature FEATURE_SET_V1.",
        f"- Parameters: `{json.dumps(config, sort_keys=True)}`.",
        "- Native categorical policy: the same deterministic integer codes were cast to pandas categorical dtype with a frozen schema; `enable_categorical=True` was used. No one-hot encoding or XGBoost-only feature was added.",
        f"- Categorical level counts: `{json.dumps({key: len(value) for key, value in schema.items()}, sort_keys=True)}`.",
        f"- Runtime: {training_seconds:.3f} seconds; final trees: {int(xgb['final_trees'])}; local ignored JSON model: `{model_path}` ({model_path.stat().st_size / 1024 / 1024:.3f} MiB).",
        f"- Versions: `{json.dumps(versions, sort_keys=True)}`.", "",
        "## Recursive Validation Protocol", "",
        "All forecasts for d_1886–d_1913 were generated before validation actuals were loaded. Each step used training history plus earlier XGBoost predictions, rebuilt past-only features, and never appended validation actual sales. Future prices remained unavailable (`NaN`).", "",
        "## Four-Method Validation Metrics", "",
        "| Method | MAE | RMSE | WAPE (%) |",
        "| --- | ---: | ---: | ---: |",
    ]
    for _, row in metrics.iterrows():
        lines.append(f"| {row['Method']} | {row['MAE']:.6f} | {row['RMSE']:.6f} | {row['WAPE_percent']:.6f} |")
    lines.extend([
        "", "## Comparisons", "",
        f"- Versus Moving Average: MAE difference {xgb['MAE_difference_vs_28_day_moving_average']:.6f} ({xgb['MAE_improvement_pct_vs_28_day_moving_average']:.3f}% improvement); RMSE difference {xgb['RMSE_difference_vs_28_day_moving_average']:.6f} ({xgb['RMSE_improvement_pct_vs_28_day_moving_average']:.3f}%); WAPE difference {xgb['WAPE_percent_difference_vs_28_day_moving_average']:.6f} points ({xgb['WAPE_percent_improvement_pct_vs_28_day_moving_average']:.3f}%).",
        f"- Versus LIGHTGBM_V1: MAE difference {xgb['MAE_difference_vs_lightgbm_v1']:.6f} ({xgb['MAE_improvement_pct_vs_lightgbm_v1']:.3f}% improvement); RMSE difference {xgb['RMSE_difference_vs_lightgbm_v1']:.6f} ({xgb['RMSE_improvement_pct_vs_lightgbm_v1']:.3f}%); WAPE difference {xgb['WAPE_percent_difference_vs_lightgbm_v1']:.6f} points ({xgb['WAPE_percent_improvement_pct_vs_lightgbm_v1']:.3f}%).",
        "", "## Per-SKU, Horizon, and Runtime Findings", "",
        f"- Per-SKU XGBoost MAE median/mean/p90: {per_sku['MAE'].median():.6f} / {per_sku['MAE'].mean():.6f} / {per_sku['MAE'].quantile(0.9):.6f}.",
        f"- Undefined per-SKU WAPE: {int(per_sku['WAPE_percent'].isna().sum())} of {len(per_sku)} because total validation demand is zero.",
        f"- Horizon MAE: first {horizon.iloc[0]['MAE']:.6f}, last {horizon.iloc[-1]['MAE']:.6f}, minimum {horizon['MAE'].min():.6f}, maximum {horizon['MAE'].max():.6f}.",
        f"- Top gain feature: `{importance.iloc[0]['feature']}` ({importance.iloc[0]['normalized_gain_percent']:.3f}% of total gain). Gain is descriptive model behavior, not causal evidence.",
        f"- Runtime/model-size evidence: `{runtime.to_dict(orient='records')}`. Speed and artifact size do not select a model.",
        "", "## Test Isolation", "", "TEST SALES VALUES WERE NOT READ, FORECAST, SCORED, SUMMARIZED, OR PLOTTED.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=REPOSITORY_ROOT / "data/raw/m5")
    parser.add_argument("--protocol", type=Path, default=REPOSITORY_ROOT / "configs/data/m5_ca1_foods.yaml")
    parser.add_argument("--feature-config", type=Path, default=REPOSITORY_ROOT / "configs/features/ml_features_v1.yaml")
    parser.add_argument("--model-config", type=Path, default=REPOSITORY_ROOT / "configs/models/xgboost_v1.yaml")
    parser.add_argument("--feature-cache", type=Path, default=REPOSITORY_ROOT / "data/processed/m5_ca1_foods_features_v1.pkl.gz")
    parser.add_argument("--baseline-metrics", type=Path, default=REPOSITORY_ROOT / "reports/tables/baseline_validation_metrics.csv")
    parser.add_argument("--lightgbm-metrics", type=Path, default=REPOSITORY_ROOT / "reports/tables/lightgbm_v1_validation_metrics.csv")
    parser.add_argument("--lightgbm-horizon", type=Path, default=REPOSITORY_ROOT / "reports/tables/lightgbm_v1_horizon_metrics.csv")
    parser.add_argument("--lightgbm-manifest", type=Path, default=REPOSITORY_ROOT / "data/manifests/lightgbm_v1_validation.json")
    parser.add_argument("--tables-dir", type=Path, default=REPOSITORY_ROOT / "reports/tables")
    parser.add_argument("--figures-dir", type=Path, default=REPOSITORY_ROOT / "reports/figures")
    parser.add_argument("--model-path", type=Path, default=REPOSITORY_ROOT / "artifacts/models/xgboost_v1.json")
    parser.add_argument("--manifest", type=Path, default=REPOSITORY_ROOT / "data/manifests/xgboost_v1_validation.json")
    args = parser.parse_args()

    feature_config = load_feature_config(args.feature_config)
    model_config = load_model_config(args.model_config)
    feature_names = _feature_names(feature_config)
    train_frame = pd.read_pickle(args.feature_cache)
    if len(train_frame) != 2_668_509 or train_frame["d_index"].min() != 29 or train_frame["d_index"].max() != 1885:
        raise ValueError("Cached training frame does not match the frozen FEATURE_SET_V1 train boundary.")
    if len(feature_names) != 25 or set(feature_names).difference(train_frame.columns) or "sales_target" not in train_frame:
        raise ValueError("Cached training frame is missing the frozen 25 model features or target.")

    # This source reads train sales and validation calendar metadata only; no validation actuals are available here.
    source = load_training_feature_source(args.raw_dir, args.protocol)
    item_ids = tuple(source.metadata["item_id"].astype(str))
    encodings = build_encodings(source.metadata, pd.concat([source.train_calendar, source.validation_calendar], ignore_index=True))
    category_levels = _extra_category_levels(encodings, source.train_calendar, source.validation_calendar)

    started = time.perf_counter()
    model, categorical_schema = fit_global_model(
        train_frame.loc[:, feature_names], train_frame["sales_target"], model_config, category_levels
    )
    training_seconds = time.perf_counter() - started
    args.model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(args.model_path)
    reloaded = load_saved_model(model_config, args.model_path)
    probe = train_frame.loc[:7, feature_names]
    if not np.allclose(predict_checked(model, probe, categorical_schema), predict_checked(reloaded, probe, categorical_schema)):
        raise ValueError("Reloaded XGBoost JSON model predictions differ from the fitted model.")

    price_rows = load_train_price_rows(args.raw_dir, item_ids, source.train_calendar)
    train_prices = build_daily_price_matrix(price_rows, item_ids, source.train_calendar)
    recursive_predictions = recursive_forecast(
        lambda frame: predict_checked(model, frame, categorical_schema), source.train_sales, train_prices,
        source.validation_calendar, source.metadata, encodings, feature_config, feature_names,
    )
    if recursive_predictions.shape != (1437, 28) or recursive_predictions.size != 40_236:
        raise ValueError("Recursive validation forecast does not have the frozen 1,437 by 28 shape.")

    # Validation actuals are loaded only after every prediction above has been created.
    validation = load_validation_dataset(args.raw_dir, args.protocol)
    validation_actuals = pd.DataFrame(validation.validation_actuals, index=validation.item_ids).loc[list(item_ids)].to_numpy()
    xgboost_metrics = aggregate_metrics(validation_actuals, recursive_predictions)
    xgboost_per_sku = per_series_metrics(validation_actuals, recursive_predictions, item_ids)
    horizon = horizon_metrics(validation_actuals, recursive_predictions, validation.validation_dates)

    baselines = pd.read_csv(args.baseline_metrics).loc[:, ["Method", "MAE", "RMSE", "WAPE_percent"]]
    lightgbm = pd.read_csv(args.lightgbm_metrics).query("Method == 'LIGHTGBM_V1'").loc[:, ["Method", "MAE", "RMSE", "WAPE_percent"]]
    metrics = pd.concat([baselines, lightgbm, pd.DataFrame([{"Method": "XGBOOST_V1", **xgboost_metrics}])], ignore_index=True)
    metrics = compare_candidate_to_references(metrics, "XGBOOST_V1", ("28-day Moving Average", "LIGHTGBM_V1"))
    metrics["final_trees"] = [np.nan, np.nan, np.nan, model.get_booster().num_boosted_rounds()]
    _write_csv(metrics, args.tables_dir / "xgboost_v1_validation_metrics.csv")
    _write_csv(horizon, args.tables_dir / "xgboost_v1_horizon_metrics.csv")

    gain_by_feature = model.get_booster().get_score(importance_type="gain")
    importance = pd.DataFrame({"feature": feature_names, "gain_importance": [gain_by_feature.get(name, 0.0) for name in feature_names]})
    importance = importance.sort_values("gain_importance", ascending=False, kind="stable")
    total_gain = float(importance["gain_importance"].sum())
    importance["normalized_gain_percent"] = importance["gain_importance"] / total_gain * 100 if total_gain else 0.0
    _write_csv(importance, args.tables_dir / "xgboost_v1_feature_importance.csv")

    with args.lightgbm_manifest.open(encoding="utf-8") as file:
        lightgbm_manifest = json.load(file)
    runtime = pd.DataFrame([
        {"model": "LIGHTGBM_V1", "training_seconds": lightgbm_manifest["training"]["duration_seconds"], "model_size_bytes": lightgbm_manifest["model_artifact"]["size_bytes"]},
        {"model": "XGBOOST_V1", "training_seconds": training_seconds, "model_size_bytes": args.model_path.stat().st_size},
    ])
    _write_csv(runtime, args.tables_dir / "ml_models_runtime_comparison.csv")
    lightgbm_horizon = pd.read_csv(args.lightgbm_horizon)
    _plot_model_comparison(metrics, args.figures_dir / "xgboost_v1_model_comparison.png")
    _plot_importance(importance, args.figures_dir / "xgboost_v1_feature_importance_gain.png")
    _plot_horizon(horizon, args.figures_dir / "xgboost_v1_horizon_mae.png")
    _plot_horizon_comparison(lightgbm_horizon, horizon, args.figures_dir / "ml_models_horizon_mae_comparison.png")
    _plot_aggregate_totals(validation_actuals, recursive_predictions, args.figures_dir / "xgboost_v1_validation_total_actual_vs_forecast.png")
    _plot_per_sku_mae(xgboost_per_sku, args.figures_dir / "xgboost_v1_per_sku_mae_distribution.png")

    versions = _versions()
    _summary(model_config, categorical_schema, training_seconds, args.model_path, metrics, xgboost_per_sku, horizon, importance, versions, runtime, args.tables_dir / "xgboost_v1_validation_summary.md")
    git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPOSITORY_ROOT, text=True).strip()
    manifest = {
        "model_name": model_config["model_name"], "status": "INITIAL_UNTUNED_VALIDATION_ONLY", "git_commit_at_run": git_commit,
        "feature_set": model_config["feature_set"], "scope": {"store_id": "CA_1", "category_id": "FOODS", "series_count": 1437},
        "training": {"rows": len(train_frame), "feature_count": len(feature_names), "target": "sales_target", "duration_seconds": round(training_seconds, 3), "final_trees": model.get_booster().num_boosted_rounds(), "cpu_count": os.cpu_count(), "parameters": model_config, "categorical_policy": "native_pandas_category_enable_categorical_true", "categorical_level_counts": {key: len(value) for key, value in categorical_schema.items()}},
        "validation": {"days": 28, "prediction_count": int(recursive_predictions.size), "metrics": xgboost_metrics, "undefined_per_sku_wape_count": int(xgboost_per_sku["WAPE_percent"].isna().sum()), "horizon_mae_first": float(horizon.iloc[0]["MAE"]), "horizon_mae_last": float(horizon.iloc[-1]["MAE"])},
        "versions": versions, "model_artifact": {"path": "artifacts/models/xgboost_v1.json (Git-ignored)", "size_bytes": args.model_path.stat().st_size, "sha256": _sha256(args.model_path)},
        "test_access_policy": "TEST sales values were not read, forecast, scored, summarized, or plotted.",
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Trained XGBOOST_V1 on {len(train_frame):,} rows in {training_seconds:.3f}s.")
    print(f"Generated {recursive_predictions.size:,} recursive validation predictions before loading validation actuals.")
    print("TEST SALES VALUES WERE NOT READ OR EVALUATED.")


if __name__ == "__main__":
    main()
