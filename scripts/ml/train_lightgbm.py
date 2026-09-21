"""Train LIGHTGBM_V1 and recursively evaluate only the frozen validation span."""

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

import joblib
import lightgbm
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT))

from ml.data.m5_ca1_foods import load_training_feature_source, load_validation_dataset
from ml.evaluation.forecast_analysis import compare_to_moving_average, horizon_metrics
from ml.evaluation.metrics import aggregate_metrics, per_series_metrics
from ml.features.builder import build_daily_price_matrix, build_encodings, load_feature_config, load_train_price_rows
from ml.models.lightgbm_model import fit_global_model, load_model_config, predict_checked
from ml.models.recursive import recursive_forecast


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _versions() -> dict[str, str]:
    return {
        "python": sys.version.split()[0],
        "lightgbm": lightgbm.__version__,
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "scikit_learn": sklearn.__version__,
    }


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)


def _plot_model_comparison(metrics: pd.DataFrame, path: Path) -> None:
    names = metrics["Method"].tolist()
    measures = [("MAE", "MAE"), ("RMSE", "RMSE"), ("WAPE_percent", "WAPE (%)")]
    figure, axes = plt.subplots(1, 3, figsize=(14, 4.8), constrained_layout=True)
    colors = ["#4C78A8", "#F58518", "#54A24B"]
    for axis, (column, label) in zip(axes, measures, strict=True):
        values = metrics[column].to_numpy(dtype=float)
        bars = axis.bar(names, values, color=colors)
        axis.set_title(label)
        axis.set_ylabel(label)
        axis.tick_params(axis="x", rotation=15)
        for bar, value in zip(bars, values, strict=True):
            axis.text(bar.get_x() + bar.get_width() / 2, value, f"{value:.3f}", ha="center", va="bottom", fontsize=8)
    figure.suptitle("M5 CA_1/FOODS: Validation Baseline and LightGBM Comparison", fontsize=13)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _plot_feature_importance(importance: pd.DataFrame, path: Path) -> None:
    top = importance.head(15).iloc[::-1]
    figure, axis = plt.subplots(figsize=(8, 6), constrained_layout=True)
    axis.barh(top["feature"], top["gain_importance"], color="#54A24B")
    axis.set_title("LIGHTGBM_V1 Top Feature Importance by Gain")
    axis.set_xlabel("Gain importance")
    axis.set_ylabel("Feature")
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _plot_horizon_mae(horizon: pd.DataFrame, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 4.5), constrained_layout=True)
    axis.plot(horizon["horizon"], horizon["MAE"], marker="o", color="#54A24B")
    axis.set_title("LIGHTGBM_V1 Recursive Validation MAE by Horizon")
    axis.set_xlabel("Forecast horizon (days ahead)")
    axis.set_ylabel("Aggregate MAE")
    axis.set_xticks(range(1, 29, 2))
    axis.grid(axis="y", alpha=0.3)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _plot_aggregate_totals(actual: np.ndarray, forecast: np.ndarray, dates: tuple[str, ...], path: Path) -> None:
    x = np.arange(1, len(dates) + 1)
    figure, axis = plt.subplots(figsize=(10, 4.8), constrained_layout=True)
    axis.plot(x, actual.sum(axis=0), marker="o", label="Actual sales", color="#4C78A8")
    axis.plot(x, forecast.sum(axis=0), marker="o", label="LIGHTGBM_V1 forecast", color="#54A24B")
    axis.set_title("M5 CA_1/FOODS: Aggregate Validation Actual vs Forecast")
    axis.set_xlabel("Validation day (d_1886 to d_1913)")
    axis.set_ylabel("Total daily units across 1,437 SKUs")
    axis.legend()
    axis.grid(axis="y", alpha=0.3)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _plot_per_sku_mae(lightgbm_metrics: pd.DataFrame, moving_metrics: pd.DataFrame, path: Path) -> None:
    maximum = max(float(lightgbm_metrics["MAE"].max()), float(moving_metrics["MAE"].max()))
    bins = np.linspace(0, maximum, 36) if maximum > 0 else 10
    figure, axis = plt.subplots(figsize=(8, 5), constrained_layout=True)
    axis.hist(moving_metrics["MAE"], bins=bins, alpha=0.55, label="28-day Moving Average", color="#F58518", edgecolor="white")
    axis.hist(lightgbm_metrics["MAE"], bins=bins, alpha=0.55, label="LIGHTGBM_V1", color="#54A24B", edgecolor="white")
    axis.set_title("Per-SKU Validation MAE Distribution")
    axis.set_xlabel("28-day per-SKU MAE (units/day)")
    axis.set_ylabel("Number of SKUs")
    axis.legend()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _summary(
    config: dict, feature_names: list[str], categorical: list[str], training_seconds: float, model_path: Path,
    metrics: pd.DataFrame, per_sku: pd.DataFrame, horizon: pd.DataFrame, importance: pd.DataFrame, versions: dict, path: Path
) -> None:
    lightgbm_row = metrics.loc[metrics["Method"] == "LIGHTGBM_V1"].iloc[0]
    moving = metrics.loc[metrics["Method"] == "28-day Moving Average"].iloc[0]
    lines = [
        "# LIGHTGBM_V1 Validation Summary", "",
        "LIGHTGBM_V1 is the initial / untuned global one-step model. Its Poisson objective is the training loss; MAE, RMSE, and WAPE remain the thesis evaluation metrics.", "",
        "## Training Setup", "",
        "- One global LightGBM model trained on 2,668,509 SKU-day rows from 1,437 CA_1/FOODS series using FEATURE_SET_V1 (25 features).",
        f"- Parameters: `{json.dumps(config, sort_keys=True)}`.",
        f"- Categorical features: `{', '.join(categorical)}`.",
        f"- Runtime: {training_seconds:.3f} seconds; final trees: {int(lightgbm_row['final_trees'])}; local ignored model: `{model_path}` ({model_path.stat().st_size / 1024 / 1024:.3f} MiB).",
        f"- Versions: `{json.dumps(versions, sort_keys=True)}`.", "",
        "Each boosted decision tree improves the preceding collection's residual fit; the fitted collection of trees is the saved global model. The same model is reused recursively for all 28 forecast days.", "",
        "## Recursive Validation Protocol", "",
        "Forecasts for d_1886–d_1913 were generated before validation actuals were loaded. At each step, the runner used train history plus earlier model predictions, rebuilt past-only features, and never appended validation actual sales. Future price values were not used.",
        "", "## Metrics and Baseline Comparison", "",
        "| Method | MAE | RMSE | WAPE (%) | MAE improvement vs Moving Average | RMSE improvement | WAPE improvement |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, row in metrics.iterrows():
        lines.append(f"| {row['Method']} | {row['MAE']:.6f} | {row['RMSE']:.6f} | {row['WAPE_percent']:.6f} | {row['MAE_improvement_pct_vs_moving_average']:.3f}% | {row['RMSE_improvement_pct_vs_moving_average']:.3f}% | {row['WAPE_percent_improvement_pct_vs_moving_average']:.3f}% |")
    lines.extend([
        "", f"LIGHTGBM_V1 validation metrics: MAE {lightgbm_row['MAE']:.6f}, RMSE {lightgbm_row['RMSE']:.6f}, WAPE {lightgbm_row['WAPE_percent']:.6f}%.",
        f"Against the Moving Average, its absolute differences are MAE {lightgbm_row['MAE_difference_vs_moving_average']:.6f}, RMSE {lightgbm_row['RMSE_difference_vs_moving_average']:.6f}, and WAPE {lightgbm_row['WAPE_percent_difference_vs_moving_average']:.6f} percentage points.",
        "", "## Per-SKU and Horizon Findings", "",
        f"- Per-SKU LightGBM MAE median/mean/p90: {per_sku['MAE'].median():.6f} / {per_sku['MAE'].mean():.6f} / {per_sku['MAE'].quantile(0.9):.6f}.",
        f"- Undefined per-SKU WAPE: {int(per_sku['WAPE_percent'].isna().sum())} of {len(per_sku)} due to zero 28-day validation actual demand.",
        f"- Recursive horizon MAE: first day {horizon.iloc[0]['MAE']:.6f}, last day {horizon.iloc[-1]['MAE']:.6f}, minimum {horizon['MAE'].min():.6f}, maximum {horizon['MAE'].max():.6f}.",
        f"- Top gain feature: `{importance.iloc[0]['feature']}` ({importance.iloc[0]['normalized_gain_percent']:.3f}% of total gain). Gain describes fitted-model use, not causal importance.",
        "", "## Test Isolation", "", "TEST SALES VALUES WERE NOT READ, FORECAST, SCORED, SUMMARIZED, OR PLOTTED.",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=REPOSITORY_ROOT / "data/raw/m5")
    parser.add_argument("--protocol", type=Path, default=REPOSITORY_ROOT / "configs/data/m5_ca1_foods.yaml")
    parser.add_argument("--feature-config", type=Path, default=REPOSITORY_ROOT / "configs/features/ml_features_v1.yaml")
    parser.add_argument("--model-config", type=Path, default=REPOSITORY_ROOT / "configs/models/lightgbm_v1.yaml")
    parser.add_argument("--feature-cache", type=Path, default=REPOSITORY_ROOT / "data/processed/m5_ca1_foods_features_v1.pkl.gz")
    parser.add_argument("--baseline-metrics", type=Path, default=REPOSITORY_ROOT / "reports/tables/baseline_validation_metrics.csv")
    parser.add_argument("--tables-dir", type=Path, default=REPOSITORY_ROOT / "reports/tables")
    parser.add_argument("--figures-dir", type=Path, default=REPOSITORY_ROOT / "reports/figures")
    parser.add_argument("--model-path", type=Path, default=REPOSITORY_ROOT / "artifacts/models/lightgbm_v1.joblib")
    parser.add_argument("--manifest", type=Path, default=REPOSITORY_ROOT / "data/manifests/lightgbm_v1_validation.json")
    args = parser.parse_args()

    feature_config = load_feature_config(args.feature_config)
    model_config = load_model_config(args.model_config)
    train_frame = pd.read_pickle(args.feature_cache)
    feature_names = [
        *[f"lag_{value}" for value in feature_config["sales_lags"]],
        *[f"rolling_mean_{value}" for value in feature_config["rolling_mean_windows"]],
        *[f"rolling_std_{value}" for value in feature_config["rolling_std_windows"]],
        "wday", "month", "year", "is_weekend", "snap_CA",
        "event_name_1_code", "event_type_1_code", "event_name_2_code", "event_type_2_code",
        "item_code", "dept_code", *feature_config["price_features"],
    ]
    if len(train_frame) != 2_668_509 or train_frame["d_index"].min() != 29 or train_frame["d_index"].max() != 1885:
        raise ValueError("Cached training frame does not match the frozen FEATURE_SET_V1 train boundary.")
    if set(feature_names).difference(train_frame.columns) or "sales_target" not in train_frame:
        raise ValueError("Cached training frame is missing frozen model features or target.")

    started = time.perf_counter()
    model, categorical = fit_global_model(train_frame.loc[:, feature_names], train_frame["sales_target"], model_config)
    training_seconds = time.perf_counter() - started
    args.model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.model_path)

    # Validation actuals are deliberately unavailable until this recursive block completes.
    source = load_training_feature_source(args.raw_dir, args.protocol)
    item_ids = tuple(source.metadata["item_id"].astype(str))
    price_rows = load_train_price_rows(args.raw_dir, item_ids, source.train_calendar)
    train_prices = build_daily_price_matrix(price_rows, item_ids, source.train_calendar)
    encodings = build_encodings(source.metadata, pd.concat([source.train_calendar, source.validation_calendar], ignore_index=True))
    recursive_predictions = recursive_forecast(
        lambda frame: predict_checked(model, frame), source.train_sales, train_prices, source.validation_calendar,
        source.metadata, encodings, feature_config, feature_names,
    )
    if recursive_predictions.shape != (1437, 28):
        raise ValueError("Recursive validation forecast does not have the frozen 1,437 by 28 shape.")

    # Only after all 40,236 predictions exist may validation actuals be loaded for scoring.
    validation = load_validation_dataset(args.raw_dir, args.protocol)
    validation_actuals = pd.DataFrame(validation.validation_actuals, index=validation.item_ids).loc[list(item_ids)].to_numpy()
    lightgbm_metrics = aggregate_metrics(validation_actuals, recursive_predictions)
    lightgbm_per_sku = per_series_metrics(validation_actuals, recursive_predictions, item_ids)
    horizon = horizon_metrics(validation_actuals, recursive_predictions, validation.validation_dates)

    baselines = pd.read_csv(args.baseline_metrics)
    metrics = pd.concat([baselines.loc[:, ["Method", "MAE", "RMSE", "WAPE_percent"]], pd.DataFrame([{"Method": "LIGHTGBM_V1", **lightgbm_metrics}])], ignore_index=True)
    metrics = compare_to_moving_average(metrics)
    metrics["final_trees"] = [np.nan, np.nan, model.booster_.num_trees()]
    _write_csv(metrics, args.tables_dir / "lightgbm_v1_validation_metrics.csv")
    _write_csv(horizon, args.tables_dir / "lightgbm_v1_horizon_metrics.csv")

    gain = model.booster_.feature_importance(importance_type="gain")
    importance = pd.DataFrame({"feature": feature_names, "gain_importance": gain}).sort_values("gain_importance", ascending=False, kind="stable")
    total_gain = float(importance["gain_importance"].sum())
    importance["normalized_gain_percent"] = importance["gain_importance"] / total_gain * 100 if total_gain else 0.0
    _write_csv(importance, args.tables_dir / "lightgbm_v1_feature_importance.csv")

    moving_predictions = None
    # Per-SKU moving-average errors are recreated from train-only history for the comparison figure.
    from ml.baselines import moving_average_28_day
    moving_predictions = moving_average_28_day(source.train_sales, 28)
    moving_per_sku = per_series_metrics(validation_actuals, moving_predictions, item_ids)
    _plot_model_comparison(metrics, args.figures_dir / "lightgbm_v1_model_comparison.png")
    _plot_feature_importance(importance, args.figures_dir / "lightgbm_v1_feature_importance_gain.png")
    _plot_horizon_mae(horizon, args.figures_dir / "lightgbm_v1_horizon_mae.png")
    _plot_aggregate_totals(validation_actuals, recursive_predictions, validation.validation_dates, args.figures_dir / "lightgbm_v1_validation_total_actual_vs_forecast.png")
    _plot_per_sku_mae(lightgbm_per_sku, moving_per_sku, args.figures_dir / "lightgbm_v1_per_sku_mae_distribution.png")

    versions = _versions()
    _summary(metrics=metrics, per_sku=lightgbm_per_sku, horizon=horizon, importance=importance, config=model_config, feature_names=feature_names, categorical=categorical, training_seconds=training_seconds, model_path=args.model_path, versions=versions, path=args.tables_dir / "lightgbm_v1_validation_summary.md")
    git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPOSITORY_ROOT, text=True).strip()
    manifest = {
        "model_name": model_config["model_name"], "status": "INITIAL_UNTUNED_VALIDATION_ONLY", "git_commit_at_run": git_commit,
        "feature_set": model_config["feature_set"], "scope": {"store_id": "CA_1", "category_id": "FOODS", "series_count": 1437},
        "training": {"rows": len(train_frame), "feature_count": len(feature_names), "target": "sales_target", "duration_seconds": round(training_seconds, 3), "final_trees": model.booster_.num_trees(), "cpu_count": os.cpu_count(), "parameters": model_config, "categorical_features": categorical},
        "validation": {"days": 28, "prediction_count": int(recursive_predictions.size), "metrics": lightgbm_metrics, "undefined_per_sku_wape_count": int(lightgbm_per_sku["WAPE_percent"].isna().sum()), "horizon_mae_first": float(horizon.iloc[0]["MAE"]), "horizon_mae_last": float(horizon.iloc[-1]["MAE"])},
        "versions": versions, "model_artifact": {"path": "artifacts/models/lightgbm_v1.joblib (Git-ignored)", "size_bytes": args.model_path.stat().st_size, "sha256": _sha256(args.model_path)},
        "test_access_policy": "TEST sales values were not read, forecast, scored, summarized, or plotted.",
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Trained LIGHTGBM_V1 on {len(train_frame):,} rows in {training_seconds:.3f}s.")
    print(f"Generated {recursive_predictions.size:,} recursive validation predictions before loading validation actuals.")
    print("TEST SALES VALUES WERE NOT READ OR EVALUATED.")


if __name__ == "__main__":
    main()
