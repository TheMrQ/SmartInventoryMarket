"""Execute the single frozen P12 final forecast and inventory-policy experiment.

The runner intentionally trains one selected XGBoost model through d_1913,
persists the full fixed-origin forecast hash, and only then calls the isolated
TEST-actual loader. It neither tunes nor compares alternative model settings.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
import xgboost
import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT))

from ml.data.m5_ca1_foods import load_final_evaluation_feature_source, load_final_test_actuals
from ml.evaluation.forecast_analysis import horizon_metrics
from ml.evaluation.metrics import aggregate_metrics, per_series_metrics
from ml.features.builder import (
    build_daily_price_matrix, build_encodings, build_training_features,
    encode_calendar_features, load_feature_config, load_train_price_rows,
)
from ml.inventory_simulation.engine import simulate_lost_sales_policy
from ml.inventory_simulation.metrics import per_sku_summary, policy_metrics
from ml.inventory_simulation.policies import forecast_reorder_decision, min_stock_ma28_decision
from ml.inventory_simulation.protocol import load_and_validate_inventory_protocol
from ml.models.recursive import recursive_forecast
from ml.models.xgboost_model import fit_global_model, load_model_config, load_saved_model, predict_checked


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _array_sha256(values: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(values).tobytes()).hexdigest()


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)


def _write_json(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected YAML mapping at {path}.")
    return value


def _category_levels(encodings, calendar: pd.DataFrame, metadata: pd.DataFrame) -> dict[str, list[int]]:
    encoded = encode_calendar_features(calendar, encodings)
    levels = {column: sorted(encoded[column].astype(int).unique().tolist()) for column in encoded.columns}
    levels["item_code"] = sorted(encodings.item_codes.values())
    levels["dept_code"] = sorted(encodings.dept_codes.values())
    return levels


def _plot_forecast_actual(actual: np.ndarray, forecast: np.ndarray, path: Path) -> None:
    horizon = np.arange(1, 29)
    figure, axis = plt.subplots(figsize=(10, 4.8), constrained_layout=True)
    axis.plot(horizon, actual.sum(axis=0), marker="o", label="TEST actual sales", color="#4C78A8")
    axis.plot(horizon, forecast.sum(axis=0), marker="o", label="XGBOOST_V1 fixed-origin forecast", color="#B279A2")
    axis.set_title("M5 CA_1/FOODS: Final TEST Actual vs Fixed-Origin Forecast")
    axis.set_xlabel("Forecast horizon (days)")
    axis.set_ylabel("Total daily units across 1,437 SKUs")
    axis.grid(axis="y", alpha=0.3)
    axis.legend()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _plot_horizon_mae(horizon: pd.DataFrame, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 4.5), constrained_layout=True)
    axis.plot(horizon["horizon"], horizon["MAE"], marker="o", color="#B279A2")
    axis.set_title("Final TEST Recursive Forecast MAE by Horizon")
    axis.set_xlabel("Forecast horizon (days ahead)")
    axis.set_ylabel("Aggregate MAE")
    axis.set_xticks(range(1, 29, 2))
    axis.grid(axis="y", alpha=0.3)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _plot_validation_test(selection: dict, test_metrics: dict[str, float], path: Path) -> None:
    names = ["Validation", "Final TEST"]
    values = {
        "MAE": [selection["validation_MAE"], test_metrics["MAE"]],
        "RMSE": [selection["validation_RMSE"], test_metrics["RMSE"]],
        "WAPE (%)": [selection["validation_WAPE"], test_metrics["WAPE_percent"]],
    }
    figure, axes = plt.subplots(1, 3, figsize=(12, 4.2), constrained_layout=True)
    for axis, (label, metric_values) in zip(axes, values.items(), strict=True):
        bars = axis.bar(names, metric_values, color=["#54A24B", "#B279A2"])
        axis.set_title(label)
        axis.set_ylabel(label)
        for bar, value in zip(bars, metric_values, strict=True):
            axis.text(bar.get_x() + bar.get_width() / 2, value, f"{value:.3f}", ha="center", va="bottom", fontsize=9)
    figure.suptitle("XGBOOST_V1: Validation vs Final TEST Metrics (Descriptive)")
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _bar_plot(labels: list[str], values: list[float], title: str, ylabel: str, path: Path, colors: list[str] | None = None) -> None:
    figure, axis = plt.subplots(figsize=(7, 4.5), constrained_layout=True)
    bars = axis.bar(labels, values, color=colors or ["#F58518", "#B279A2"])
    axis.set_title(title)
    axis.set_ylabel(ylabel)
    axis.grid(axis="y", alpha=0.25)
    for bar, value in zip(bars, values, strict=True):
        axis.text(bar.get_x() + bar.get_width() / 2, value, f"{value:.3f}", ha="center", va="bottom", fontsize=9)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _plot_inventory_primary(comparison: pd.DataFrame, path: Path) -> None:
    columns = [
        ("total_lost_sales_units", "Lost-sales units"),
        ("stockout_days", "Stockout SKU-days"),
        ("fill_rate", "Fill rate"),
        ("average_on_hand_inventory", "Average on-hand units"),
    ]
    figure, axes = plt.subplots(2, 2, figsize=(11, 7.2), constrained_layout=True)
    for axis, (column, label) in zip(axes.flat, columns, strict=True):
        bars = axis.bar(comparison["policy"], comparison[column], color=["#F58518", "#B279A2"])
        axis.set_title(label)
        axis.tick_params(axis="x", rotation=12)
        axis.grid(axis="y", alpha=0.25)
        for bar, value in zip(bars, comparison[column], strict=True):
            axis.text(bar.get_x() + bar.get_width() / 2, value, f"{value:.3f}", ha="center", va="bottom", fontsize=8)
    figure.suptitle("Frozen Inventory Policy Comparison: Primary Metrics")
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _write_forecast_summary(metrics: dict, per_sku: pd.DataFrame, horizon: pd.DataFrame, training_rows: int, runtime: float, path: Path) -> None:
    lines = [
        "# Final Held-Out TEST Forecast Evaluation", "",
        "`XGBOOST_V1` + `FEATURE_SET_V1` / `FULL_V1` was selected on validation before TEST was opened. It was retrained exactly once on TRAIN + VALIDATION through `d_1913` without tuning.", "",
        "## Final TEST Metrics", "", "| MAE | RMSE | WAPE (%) | Predictions |", "| ---: | ---: | ---: | ---: |",
        f"| {metrics['MAE']:.6f} | {metrics['RMSE']:.6f} | {metrics['WAPE_percent']:.6f} | 40,236 |", "",
        "## Protocol Evidence", "",
        f"- Train-plus-validation FEATURE_SET_V1 rows: {training_rows:,}.",
        f"- Fit runtime: {runtime:.3f} seconds; selected configuration and 25 features are unchanged.",
        "- All 40,236 fixed-origin predictions for `d_1914`–`d_1941` were created and hashed before TEST actual sales were loaded.",
        f"- Per-SKU WAPE is undefined for {int(per_sku['WAPE_percent'].isna().sum())} of {len(per_sku)} SKUs with zero TEST-demand denominators.",
        f"- Horizon MAE: first {horizon.iloc[0]['MAE']:.6f}, last {horizon.iloc[-1]['MAE']:.6f}, minimum {horizon['MAE'].min():.6f}, maximum {horizon['MAE'].max():.6f}.",
        "- TEST metrics are final held-out evidence and were not used for post-TEST model selection, feature changes, hyperparameter tuning, or retraining.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _add_relative_changes(comparison: pd.DataFrame) -> pd.DataFrame:
    result = comparison.copy()
    baseline = result.iloc[0]
    forecast_index = result.index[1]
    for column in ("total_lost_sales_units", "stockout_days", "average_on_hand_inventory", "reorder_count", "normalized_cost_proxy"):
        name = f"{column}_change_pct_vs_MIN_STOCK_MA28"
        result[name] = np.nan
        denominator = float(baseline[column])
        result.loc[forecast_index, name] = ((float(result.loc[forecast_index, column]) - denominator) / denominator * 100) if denominator else np.nan
    result["fill_rate_difference_points_vs_MIN_STOCK_MA28"] = np.nan
    result.loc[forecast_index, "fill_rate_difference_points_vs_MIN_STOCK_MA28"] = (float(result.loc[forecast_index, "fill_rate"]) - float(baseline["fill_rate"])) * 100
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=REPOSITORY_ROOT / "data/raw/m5")
    parser.add_argument("--data-config", type=Path, default=REPOSITORY_ROOT / "configs/data/m5_ca1_foods.yaml")
    parser.add_argument("--feature-config", type=Path, default=REPOSITORY_ROOT / "configs/features/ml_features_v1.yaml")
    parser.add_argument("--model-config", type=Path, default=REPOSITORY_ROOT / "configs/models/xgboost_v1.yaml")
    parser.add_argument("--selection-config", type=Path, default=REPOSITORY_ROOT / "configs/models/selected_forecasting_model.yaml")
    parser.add_argument("--model-path", type=Path, default=REPOSITORY_ROOT / "artifacts/models/xgboost_selected_trainval_final.json")
    parser.add_argument("--forecast-path", type=Path, default=REPOSITORY_ROOT / "artifacts/forecasts/xgboost_selected_final_test_forecast.npy")
    parser.add_argument("--pretest-manifest", type=Path, default=REPOSITORY_ROOT / "data/manifests/xgboost_selected_final_test_pretest_forecast.json")
    parser.add_argument("--manifest", type=Path, default=REPOSITORY_ROOT / "data/manifests/xgboost_selected_final_test.json")
    parser.add_argument("--tables-dir", type=Path, default=REPOSITORY_ROOT / "reports/tables")
    parser.add_argument("--figures-dir", type=Path, default=REPOSITORY_ROOT / "reports/figures")
    args = parser.parse_args()

    simulation_config, comparison_config, selection = load_and_validate_inventory_protocol(REPOSITORY_ROOT)
    model_config = load_model_config(args.model_config)
    feature_config = load_feature_config(args.feature_config)
    if selection["selected_model"] != model_config["model_name"] or selection["selected_feature_set"] != feature_config["feature_set"]:
        raise ValueError("Selected-model pointer does not match frozen XGBoost/feature configs.")
    if selection["feature_count"] != 25 or selection["forecast_horizon_days"] != 28:
        raise ValueError("Selected-model feature count or horizon changed.")

    # TEST sales are structurally unavailable in this source object.
    source = load_final_evaluation_feature_source(args.raw_dir, args.data_config)
    item_ids = tuple(source.metadata["item_id"].astype(str))
    if len(item_ids) != simulation_config["scope"]["expected_item_store_series"]:
        raise ValueError("Frozen inventory scope series count mismatch.")
    calendar_metadata = pd.concat([source.train_validation_calendar, source.forecast_calendar], ignore_index=True)
    encodings = build_encodings(source.metadata, calendar_metadata)
    category_levels = _category_levels(encodings, calendar_metadata, source.metadata)
    price_rows = load_train_price_rows(args.raw_dir, item_ids, source.train_validation_calendar)
    train_validation_prices = build_daily_price_matrix(price_rows, item_ids, source.train_validation_calendar)
    feature_result = build_training_features(
        source.metadata, source.train_validation_sales, source.train_validation_calendar,
        calendar_metadata, train_validation_prices, feature_config,
    )
    feature_names = list(feature_result.feature_names)
    if len(feature_names) != selection["feature_count"]:
        raise ValueError("Final training feature count does not match selected model.")

    started = time.perf_counter()
    model, categorical_schema = fit_global_model(
        feature_result.frame.loc[:, feature_names], feature_result.frame["sales_target"], model_config, category_levels
    )
    fit_seconds = time.perf_counter() - started
    args.model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(args.model_path)
    reloaded = load_saved_model(model_config, args.model_path)
    probe = feature_result.frame.loc[:7, feature_names]
    if not np.allclose(predict_checked(model, probe, categorical_schema), predict_checked(reloaded, probe, categorical_schema)):
        raise ValueError("Reloaded final XGBoost model differs on prediction probe.")

    # Fixed-origin TEST forecast: no TEST actual array exists in memory yet.
    fixed_origin_calendar = source.forecast_calendar.iloc[:28].reset_index(drop=True)
    fixed_origin_forecast = recursive_forecast(
        lambda frame: predict_checked(model, frame, categorical_schema), source.train_validation_sales,
        train_validation_prices, fixed_origin_calendar, source.metadata, encodings, feature_config, feature_names,
    )
    if fixed_origin_forecast.shape != (len(item_ids), 28) or fixed_origin_forecast.size != 40_236:
        raise ValueError("Final fixed-origin forecast must contain 40,236 predictions.")
    if not np.isfinite(fixed_origin_forecast).all() or (fixed_origin_forecast < 0).any():
        raise ValueError("Final fixed-origin forecast contains invalid values.")
    args.forecast_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(args.forecast_path, fixed_origin_forecast)
    prediction_created_at = datetime.now(UTC).isoformat()
    pretest = {
        "status": "FIXED_ORIGIN_FORECAST_COMPLETE_BEFORE_TEST_OPEN",
        "forecast_created_at_utc": prediction_created_at,
        "training_boundary": "d_1-d_1913",
        "forecast_boundary": "d_1914-d_1941",
        "prediction_count": int(fixed_origin_forecast.size),
        "prediction_sha256": _array_sha256(fixed_origin_forecast),
        "ignored_forecast_artifact": "artifacts/forecasts/xgboost_selected_final_test_forecast.npy",
        "test_actuals_loaded_at_write_time": False,
    }
    _write_json(pretest, args.pretest_manifest)

    # The only TEST-sales loader call occurs after the complete forecast hash exists above.
    actual_item_ids, test_actuals, test_dates = load_final_test_actuals(args.raw_dir, args.data_config)
    if actual_item_ids != item_ids or test_actuals.shape != fixed_origin_forecast.shape:
        raise ValueError("Final TEST actuals do not align with fixed-origin predictions.")
    test_metrics = aggregate_metrics(test_actuals, fixed_origin_forecast)
    test_per_sku = per_series_metrics(test_actuals, fixed_origin_forecast, item_ids)
    test_horizon = horizon_metrics(test_actuals, fixed_origin_forecast, test_dates)
    _write_csv(pd.DataFrame([{"Method": "XGBOOST_V1_SELECTED_FINAL_TEST", **test_metrics, "prediction_count": int(fixed_origin_forecast.size)}]), args.tables_dir / "final_test_forecast_metrics.csv")
    _write_csv(test_per_sku, args.tables_dir / "final_test_forecast_per_sku_metrics.csv")
    _write_csv(test_horizon, args.tables_dir / "final_test_horizon_metrics.csv")
    _write_forecast_summary(test_metrics, test_per_sku, test_horizon, len(feature_result.frame), fit_seconds, args.tables_dir / "final_test_forecast_summary.md")
    _plot_forecast_actual(test_actuals, fixed_origin_forecast, args.figures_dir / "final_test_forecast_actual_vs_predicted.png")
    _plot_horizon_mae(test_horizon, args.figures_dir / "final_test_horizon_mae.png")
    _plot_validation_test(selection, test_metrics, args.figures_dir / "final_validation_vs_test_metrics.png")

    lead_time = int(simulation_config["lead_time_days"])
    review_period = int(simulation_config["review_period_days"])
    z_value = float(simulation_config["safety_stock"]["service_factor_z"])
    if simulation_config["receipt_timing"] != "start_of_day" or simulation_config["inventory_state"]["backorders_enabled"]:
        raise ValueError("Frozen receipt timing or lost-sales protocol changed.")
    initial_history = source.train_validation_sales.astype(np.float32)

    def baseline_decision(history: np.ndarray, position: np.ndarray):
        return min_stock_ma28_decision(history, position, lead_time, review_period, z_value)

    forecast_call_index = 0

    def forecast_decision(history: np.ndarray, position: np.ndarray):
        nonlocal forecast_call_index
        calendar_slice = source.forecast_calendar.iloc[forecast_call_index + 1 : forecast_call_index + 1 + lead_time + review_period]
        if len(calendar_slice) != lead_time + review_period:
            raise ValueError("Future calendar metadata is unavailable for a rolling reorder decision.")
        unknown_price_days = history.shape[1] - train_validation_prices.shape[1]
        if unknown_price_days < 0:
            raise ValueError("Rolling history unexpectedly predates train-plus-validation prices.")
        price_history = np.concatenate([
            train_validation_prices,
            np.full((len(item_ids), unknown_price_days), np.nan, dtype=np.float32),
        ], axis=1)
        forecast = recursive_forecast(
            lambda frame: predict_checked(model, frame, categorical_schema), history, price_history,
            calendar_slice, source.metadata, encodings, feature_config, feature_names,
        )
        forecast_call_index += 1
        return forecast_reorder_decision(history, forecast, position, lead_time, review_period, z_value)

    baseline_result = simulate_lost_sales_policy(
        "MIN_STOCK_MA28", initial_history, test_actuals, lead_time, review_period, z_value, baseline_decision
    )
    forecast_result = simulate_lost_sales_policy(
        "FORECAST_REORDER_XGBOOST_V1", initial_history, test_actuals, lead_time, review_period, z_value, forecast_decision
    )
    if not np.array_equal(baseline_result.initial_on_hand, forecast_result.initial_on_hand):
        raise ValueError("Policies do not have identical initial on-hand inventory.")
    if not np.array_equal(baseline_result.realized_demand, forecast_result.realized_demand):
        raise ValueError("Policies did not receive identical realized demand replay.")

    cost = simulation_config["normalized_cost_proxy"]
    weights = {
        "holding": float(cost["holding_cost_weight_per_unit_day"]),
        "lost_sales": float(cost["lost_sales_cost_weight_per_lost_unit"]),
        "reorder_event": float(cost["order_event_cost_weight_per_reorder"]),
    }
    comparison = _add_relative_changes(pd.DataFrame([
        policy_metrics(baseline_result, weights), policy_metrics(forecast_result, weights),
    ]))
    per_sku = per_sku_summary(item_ids, baseline_result, forecast_result)
    _write_csv(comparison, args.tables_dir / "inventory_policy_comparison.csv")
    _write_csv(per_sku, args.tables_dir / "inventory_policy_per_sku_summary.csv")
    _plot_inventory_primary(comparison, args.figures_dir / "inventory_policy_primary_metrics.png")
    labels = comparison["policy"].tolist()
    _bar_plot(labels, comparison["fill_rate"].tolist(), "Inventory Policy Fill Rate", "Fill rate", args.figures_dir / "inventory_policy_fill_rate.png")
    _bar_plot(labels, comparison["stockout_days"].tolist(), "Inventory Policy Stockout Days", "Stockout SKU-days", args.figures_dir / "inventory_policy_stockout_comparison.png")
    _bar_plot(labels, comparison["average_on_hand_inventory"].tolist(), "Inventory Policy Average On-Hand Inventory", "Average units on hand", args.figures_dir / "inventory_policy_average_inventory.png")
    _bar_plot(labels, comparison["normalized_cost_proxy"].tolist(), "Inventory Policy Normalized Cost Proxy", "Normalized cost units (not USD)", args.figures_dir / "inventory_policy_cost_proxy.png")
    figure, axis = plt.subplots(figsize=(8, 4.8), constrained_layout=True)
    axis.hist(per_sku["baseline_fill_rate"].dropna(), bins=25, alpha=0.6, label="MIN_STOCK_MA28", color="#F58518")
    axis.hist(per_sku["forecast_fill_rate"].dropna(), bins=25, alpha=0.6, label="FORECAST_REORDER_XGBOOST_V1", color="#B279A2")
    axis.set_title("Per-SKU Fill-Rate Distribution")
    axis.set_xlabel("28-day per-SKU fill rate")
    axis.set_ylabel("Number of SKUs")
    axis.legend()
    figure.savefig(args.figures_dir / "inventory_policy_per_sku_fill_rate_distribution.png", dpi=220, bbox_inches="tight")
    plt.close(figure)

    manifest = {
        "status": "FINAL_HELD_OUT_TEST_AND_INVENTORY_POLICY_EXPERIMENT_COMPLETE",
        "selected_before_test": {"model": selection["selected_model"], "feature_set": selection["selected_feature_set"], "variant": selection["selected_variant"], "feature_count": selection["feature_count"]},
        "scope": {"store_id": "CA_1", "category_id": "FOODS", "series_count": len(item_ids)},
        "training": {"boundary": "d_1-d_1913", "rows": len(feature_result.frame), "feature_count": len(feature_names), "fit_seconds": round(fit_seconds, 3), "parameters": model_config, "final_trees": model.get_booster().num_boosted_rounds(), "categorical_level_counts": {key: len(value) for key, value in categorical_schema.items()}},
        "fixed_origin_forecast_before_test_actual_load": pretest,
        "final_test": {"boundary": "d_1914-d_1941", "prediction_count": int(fixed_origin_forecast.size), "metrics": test_metrics, "undefined_per_sku_wape_count": int(test_per_sku["WAPE_percent"].isna().sum())},
        "inventory_simulation": {"days": 28, "lead_time_days": lead_time, "review_period_days": review_period, "receipt_timing": simulation_config["receipt_timing"], "identical_initial_states": True, "identical_realized_demand": True, "policies": json.loads(comparison.to_json(orient="records"))},
        "model_artifact": {"path": "artifacts/models/xgboost_selected_trainval_final.json (Git-ignored)", "size_bytes": args.model_path.stat().st_size, "sha256": _sha256(args.model_path)},
        "versions": {"python": sys.version.split()[0], "numpy": np.__version__, "pandas": pd.__version__, "scikit_learn": sklearn.__version__, "xgboost": xgboost.__version__},
        "test_use": "Opened once after fixed-origin prediction hash; no post-TEST tuning, feature selection, or retraining occurred.",
    }
    _write_json(manifest, args.manifest)
    print(f"Trained selected XGBOOST_V1 once on {len(feature_result.frame):,} TRAIN+VALIDATION rows in {fit_seconds:.3f}s.")
    print(f"Created and hashed {fixed_origin_forecast.size:,} fixed-origin predictions before loading TEST actuals.")
    print(f"Final TEST MAE/RMSE/WAPE: {test_metrics['MAE']:.6f} / {test_metrics['RMSE']:.6f} / {test_metrics['WAPE_percent']:.6f}%.")
    print("Completed the frozen inventory-policy comparison without tuning.")


if __name__ == "__main__":
    main()
