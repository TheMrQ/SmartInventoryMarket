"""Execute only the frozen XGBoost feature-group ablations on validation data.

FULL_V1 is read from existing tracked XGBOOST_V1 artifacts.  The three reduced
variants train on the same frozen train cache and produce all recursive
validation predictions before validation actuals are loaded.  TEST is never read.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT))

from ml.data.m5_ca1_foods import load_training_feature_source, load_validation_dataset
from ml.evaluation.forecast_analysis import horizon_metrics
from ml.evaluation.metrics import aggregate_metrics, per_series_metrics
from ml.features.builder import (
    build_daily_price_matrix, build_encodings, encode_calendar_features,
    load_feature_config, load_train_price_rows,
)
from ml.models.recursive import recursive_forecast
from ml.models.xgboost_model import (
    build_categorical_schema, fit_global_model, load_model_config, load_saved_model, predict_checked,
)


def _feature_names(config: dict) -> list[str]:
    return [
        *[f"lag_{value}" for value in config["sales_lags"]],
        *[f"rolling_mean_{value}" for value in config["rolling_mean_windows"]],
        *[f"rolling_std_{value}" for value in config["rolling_std_windows"]],
        "wday", "month", "year", "is_weekend", "snap_CA",
        "event_name_1_code", "event_type_1_code", "event_name_2_code", "event_type_2_code",
        "item_code", "dept_code", *config["price_features"],
    ]


def select_variant_features(variant_name: str, variant: dict, full_features: list[str]) -> list[str]:
    """Select exactly the pre-registered subset; no importance-based selection."""
    if variant_name == "FULL_V1":
        selected = list(full_features)
    elif "remove_features" in variant:
        removed = list(variant["remove_features"])
        if len(removed) != len(set(removed)) or set(removed).difference(full_features):
            raise ValueError(f"{variant_name} removes invalid frozen features.")
        selected = [feature for feature in full_features if feature not in removed]
    elif "keep_features" in variant:
        kept = list(variant["keep_features"])
        if len(kept) != len(set(kept)) or set(kept).difference(full_features):
            raise ValueError(f"{variant_name} keeps invalid frozen features.")
        selected = [feature for feature in full_features if feature in kept]
    else:
        raise ValueError(f"{variant_name} requires a feature selection rule.")
    if len(selected) != int(variant["expected_feature_count"]):
        raise ValueError(f"{variant_name} expected {variant['expected_feature_count']} features, got {len(selected)}.")
    return selected


def recommend_candidate(results: pd.DataFrame) -> str:
    """Apply the pre-registered WAPE-first rule without declaring a final model."""
    required = {"variant", "WAPE", "MAE", "RMSE"}
    if missing := required.difference(results.columns):
        raise ValueError(f"Ablation results missing selection columns: {sorted(missing)}")
    return str(results.sort_values(["WAPE", "MAE", "RMSE"], kind="stable").iloc[0]["variant"])


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _extra_category_levels(encodings, train_calendar: pd.DataFrame, validation_calendar: pd.DataFrame) -> dict[str, list[int]]:
    calendar = encode_calendar_features(pd.concat([train_calendar, validation_calendar], ignore_index=True), encodings)
    levels = {column: sorted(calendar[column].astype(int).unique().tolist()) for column in calendar.columns}
    levels["item_code"] = sorted(encodings.item_codes.values())
    levels["dept_code"] = sorted(encodings.dept_codes.values())
    return levels


def _read_full_per_sku(summary_path: Path) -> tuple[float, float, float, int]:
    text = summary_path.read_text(encoding="utf-8")
    number = r"([0-9]+(?:\.[0-9]+)?)"
    match = re.search(rf"Per-SKU XGBoost MAE median/mean/p90: {number} / {number} / {number}", text)
    undefined = re.search(r"Undefined per-SKU WAPE: (\d+) of", text)
    if not match or not undefined:
        raise ValueError("Existing FULL_V1 summary cannot supply required per-SKU evidence.")
    return float(match.group(1)), float(match.group(2)), float(match.group(3)), int(undefined.group(1))


def _plot_metrics(results: pd.DataFrame, path: Path) -> None:
    panels = [("MAE", "MAE"), ("RMSE", "RMSE"), ("WAPE", "WAPE (%)")]
    figure, axes = plt.subplots(1, 3, figsize=(15, 4.8), constrained_layout=True)
    colors = ["#B279A2", "#4C78A8", "#F58518", "#54A24B"]
    for axis, (column, label) in zip(axes, panels, strict=True):
        values = results[column].to_numpy(dtype=float)
        bars = axis.bar(results["variant"], values, color=colors)
        axis.set_title(label)
        axis.set_ylabel(label)
        axis.tick_params(axis="x", rotation=18)
        for bar, value in zip(bars, values, strict=True):
            axis.text(bar.get_x() + bar.get_width() / 2, value, f"{value:.3f}", ha="center", va="bottom", fontsize=8)
    figure.suptitle("XGBoost Feature-Group Ablation: Validation Metrics", fontsize=13)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _plot_feature_count_wape(results: pd.DataFrame, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(7, 4.8), constrained_layout=True)
    colors = ["#B279A2", "#4C78A8", "#F58518", "#54A24B"]
    for (_, row), color in zip(results.iterrows(), colors, strict=True):
        axis.scatter(row["feature_count"], row["WAPE"], color=color, s=100)
        axis.annotate(row["variant"], (row["feature_count"], row["WAPE"]), xytext=(5, 5), textcoords="offset points")
    axis.set_title("XGBoost Validation WAPE vs Feature Count")
    axis.set_xlabel("Feature count")
    axis.set_ylabel("Validation WAPE (%) — lower is better")
    axis.grid(alpha=0.3)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _plot_runtime(results: pd.DataFrame, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 4.5), constrained_layout=True)
    bars = axis.bar(results["variant"], results["training_seconds"], color=["#B279A2", "#4C78A8", "#F58518", "#54A24B"])
    axis.set_title("XGBoost Feature-Group Ablation Training Runtime")
    axis.set_xlabel("Variant")
    axis.set_ylabel("Training runtime (seconds)")
    axis.tick_params(axis="x", rotation=18)
    for bar, value in zip(bars, results["training_seconds"], strict=True):
        axis.text(bar.get_x() + bar.get_width() / 2, value, f"{value:.1f}", ha="center", va="bottom", fontsize=8)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _plot_horizon(full: pd.DataFrame, reduced: pd.DataFrame, candidate: str, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 4.5), constrained_layout=True)
    axis.plot(full["horizon"], full["MAE"], marker="o", label="FULL_V1", color="#B279A2")
    axis.plot(reduced["horizon"], reduced["MAE"], marker="o", label=candidate, color="#54A24B")
    axis.set_title("Recursive Horizon MAE: Full vs Best Reduced Variant")
    axis.set_xlabel("Forecast horizon (days ahead)")
    axis.set_ylabel("Aggregate MAE")
    axis.set_xticks(range(1, 29, 2))
    axis.legend()
    axis.grid(axis="y", alpha=0.3)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _group_answer(full: pd.Series, variant: pd.Series, label: str) -> str:
    if variant["WAPE"] < full["WAPE"] and variant["MAE"] <= full["MAE"] and variant["RMSE"] <= full["RMSE"]:
        return f"Removing {label} improved all three validation metrics in this experiment; that group did not improve this validation result under the frozen protocol."
    if variant["WAPE"] < full["WAPE"]:
        return f"Removing {label} lowered WAPE but did not improve every secondary metric, so the evidence is mixed."
    return f"Removing {label} worsened validation WAPE, so the group helps this validation experiment under the frozen protocol."


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=REPOSITORY_ROOT / "data/raw/m5")
    parser.add_argument("--protocol", type=Path, default=REPOSITORY_ROOT / "configs/data/m5_ca1_foods.yaml")
    parser.add_argument("--feature-config", type=Path, default=REPOSITORY_ROOT / "configs/features/ml_features_v1.yaml")
    parser.add_argument("--model-config", type=Path, default=REPOSITORY_ROOT / "configs/models/xgboost_v1.yaml")
    parser.add_argument("--ablation-config", type=Path, default=REPOSITORY_ROOT / "configs/experiments/xgboost_feature_ablation_v1.yaml")
    parser.add_argument("--feature-cache", type=Path, default=REPOSITORY_ROOT / "data/processed/m5_ca1_foods_features_v1.pkl.gz")
    parser.add_argument("--tables-dir", type=Path, default=REPOSITORY_ROOT / "reports/tables")
    parser.add_argument("--figures-dir", type=Path, default=REPOSITORY_ROOT / "reports/figures")
    parser.add_argument("--manifests-dir", type=Path, default=REPOSITORY_ROOT / "data/manifests")
    parser.add_argument("--models-dir", type=Path, default=REPOSITORY_ROOT / "artifacts/models")
    parser.add_argument("--reuse-existing-artifacts", action="store_true", help="Regenerate reports from already trained ignored reduced-model artifacts without retraining.")
    args = parser.parse_args()

    feature_config = load_feature_config(args.feature_config)
    model_config = load_model_config(args.model_config)
    with args.ablation_config.open(encoding="utf-8") as file:
        ablation = yaml.safe_load(file)
    if ablation.get("status") not in {"TODO", "DONE"} or ablation.get("primary_metric") != "WAPE":
        raise ValueError("Expected a canonical-status, frozen WAPE-primary ablation plan.")
    full_features = _feature_names(feature_config)
    if len(full_features) != 25:
        raise ValueError("FEATURE_SET_V1 no longer has the frozen 25 fields.")
    variant_features = {name: select_variant_features(name, variant, full_features) for name, variant in ablation["variants"].items()}

    train_frame = pd.read_pickle(args.feature_cache)
    if len(train_frame) != 2_668_509 or train_frame["d_index"].min() != 29 or train_frame["d_index"].max() != 1885:
        raise ValueError("Cached train features do not match the frozen training boundary.")
    if set(full_features).difference(train_frame.columns):
        raise ValueError("The frozen train cache is missing FEATURE_SET_V1 fields.")

    # Train sales and validation calendar metadata only: validation actuals remain unavailable here.
    source = load_training_feature_source(args.raw_dir, args.protocol)
    item_ids = tuple(source.metadata["item_id"].astype(str))
    encodings = build_encodings(source.metadata, pd.concat([source.train_calendar, source.validation_calendar], ignore_index=True))
    category_levels = _extra_category_levels(encodings, source.train_calendar, source.validation_calendar)
    price_rows = load_train_price_rows(args.raw_dir, item_ids, source.train_calendar)
    train_prices = build_daily_price_matrix(price_rows, item_ids, source.train_calendar)

    with (args.manifests_dir / "xgboost_v1_validation.json").open(encoding="utf-8") as file:
        full_manifest = json.load(file)
    full_metrics = pd.read_csv(args.tables_dir / "xgboost_v1_validation_metrics.csv").query("Method == 'XGBOOST_V1'").iloc[0]
    full_horizon = pd.read_csv(args.tables_dir / "xgboost_v1_horizon_metrics.csv")
    full_median, full_mean, full_p90, full_undefined = _read_full_per_sku(args.tables_dir / "xgboost_v1_validation_summary.md")
    results = [{
        "variant": "FULL_V1", "feature_count": len(variant_features["FULL_V1"]),
        "feature_names": ";".join(variant_features["FULL_V1"]), "training_rows": full_manifest["training"]["rows"],
        "training_seconds": full_manifest["training"]["duration_seconds"], "model_size_MiB": full_manifest["model_artifact"]["size_bytes"] / 1024**2,
        "model_sha256": full_manifest["model_artifact"]["sha256"], "MAE": full_metrics["MAE"], "RMSE": full_metrics["RMSE"], "WAPE": full_metrics["WAPE_percent"],
        "per_sku_mae_median": full_median, "per_sku_mae_mean": full_mean, "per_sku_mae_p90": full_p90, "undefined_per_sku_wape_count": full_undefined,
        "horizon_1_MAE": full_horizon.iloc[0]["MAE"], "horizon_28_MAE": full_horizon.iloc[-1]["MAE"], "horizon_min_MAE": full_horizon["MAE"].min(), "horizon_max_MAE": full_horizon["MAE"].max(),
        "prediction_count": int(full_manifest["validation"]["prediction_count"]), "artifact_source": "existing_XGBOOST_V1_manifest",
    }]
    horizon_frames = [full_horizon.assign(variant="FULL_V1")]
    pending: list[tuple[str, np.ndarray, float, Path, list[str]]] = []
    args.models_dir.mkdir(parents=True, exist_ok=True)
    prior_results_path = args.tables_dir / "xgboost_feature_ablation_v1_results.csv"
    prior_results = pd.read_csv(prior_results_path).set_index("variant") if args.reuse_existing_artifacts and prior_results_path.is_file() else None

    # Every reduced recursive forecast finishes before validation actuals are loaded below.
    for variant_name in ("NO_PRICE", "NO_CALENDAR_EVENT", "DEMAND_PRODUCT_ONLY"):
        features = variant_features[variant_name]
        model_path = args.models_dir / f"xgboost_v1_{variant_name.lower()}.json"
        if args.reuse_existing_artifacts:
            if prior_results is None or variant_name not in prior_results.index or not model_path.is_file():
                raise FileNotFoundError(f"Cannot reuse missing {variant_name} ablation artifact/metadata.")
            model = load_saved_model(model_config, model_path)
            schema = build_categorical_schema(train_frame.loc[:, features], category_levels)
            training_seconds = float(prior_results.loc[variant_name, "training_seconds"])
        else:
            started = time.perf_counter()
            model, schema = fit_global_model(train_frame.loc[:, features], train_frame["sales_target"], model_config, category_levels)
            training_seconds = time.perf_counter() - started
            model.save_model(model_path)
        forecast = recursive_forecast(
            lambda frame, current_model=model, current_schema=schema: predict_checked(current_model, frame, current_schema),
            source.train_sales, train_prices, source.validation_calendar, source.metadata, encodings, feature_config, features,
        )
        if forecast.shape != (1437, 28) or forecast.size != 40_236:
            raise ValueError(f"{variant_name} did not create the frozen 40,236 predictions.")
        pending.append((variant_name, forecast, training_seconds, model_path, features))

    # This is the first validation-sales read in this runner, after all reduced forecasts exist.
    validation = load_validation_dataset(args.raw_dir, args.protocol)
    actual = pd.DataFrame(validation.validation_actuals, index=validation.item_ids).loc[list(item_ids)].to_numpy()
    for variant_name, forecast, training_seconds, model_path, features in pending:
        metrics = aggregate_metrics(actual, forecast)
        metrics["WAPE"] = metrics.pop("WAPE_percent")
        per_sku = per_series_metrics(actual, forecast, item_ids)
        horizon = horizon_metrics(actual, forecast, validation.validation_dates).assign(variant=variant_name)
        horizon_frames.append(horizon)
        results.append({
            "variant": variant_name, "feature_count": len(features), "feature_names": ";".join(features), "training_rows": len(train_frame),
            "training_seconds": training_seconds, "model_size_MiB": model_path.stat().st_size / 1024**2, "model_sha256": _sha256(model_path),
            **metrics, "per_sku_mae_median": per_sku["MAE"].median(), "per_sku_mae_mean": per_sku["MAE"].mean(), "per_sku_mae_p90": per_sku["MAE"].quantile(0.9),
            "undefined_per_sku_wape_count": int(per_sku["WAPE_percent"].isna().sum()), "horizon_1_MAE": horizon.iloc[0]["MAE"], "horizon_28_MAE": horizon.iloc[-1]["MAE"],
            "horizon_min_MAE": horizon["MAE"].min(), "horizon_max_MAE": horizon["MAE"].max(), "prediction_count": int(forecast.size), "artifact_source": str(model_path.relative_to(REPOSITORY_ROOT)) + " (Git-ignored)",
        })

    result_frame = pd.DataFrame(results)
    full_row = result_frame.loc[result_frame["variant"] == "FULL_V1"].iloc[0]
    for metric in ("MAE", "RMSE", "WAPE"):
        result_frame[f"{metric}_vs_FULL_pct"] = (full_row[metric] - result_frame[metric]) / full_row[metric] * 100
    result_frame["recommended_candidate"] = recommend_candidate(result_frame)
    args.tables_dir.mkdir(parents=True, exist_ok=True)
    result_path = args.tables_dir / "xgboost_feature_ablation_v1_results.csv"
    result_frame.to_csv(result_path, index=False)
    horizons = pd.concat(horizon_frames, ignore_index=True)
    horizons.to_csv(args.tables_dir / "xgboost_feature_ablation_v1_horizon_metrics.csv", index=False)

    candidate = recommend_candidate(result_frame)
    best_reduced = recommend_candidate(result_frame.loc[result_frame["variant"] != "FULL_V1"])
    no_price = result_frame.loc[result_frame["variant"] == "NO_PRICE"].iloc[0]
    no_calendar = result_frame.loc[result_frame["variant"] == "NO_CALENDAR_EVENT"].iloc[0]
    demand_only = result_frame.loc[result_frame["variant"] == "DEMAND_PRODUCT_ONLY"].iloc[0]
    candidate_row = result_frame.loc[result_frame["variant"] == candidate].iloc[0]
    summary = [
        "# XGBoost Feature-Group Ablation V1", "",
        "All variants use the same frozen CA_1/FOODS scope, 1,437 series, 2,668,509 training rows, XGBOOST_V1 hyperparameters/seed, 28-step recursive validation protocol, and metric utilities. FULL_V1 was reused from its verified tracked result; the other three variants alone were trained. All reduced forecasts were generated before validation actuals were loaded. TEST SALES VALUES WERE NOT READ, FORECAST, SCORED, SUMMARIZED, OR PLOTTED.", "",
        "| Variant | Meaning | Features | MAE | RMSE | WAPE (%) | Runtime (s) | Size (MiB) | WAPE improvement vs FULL |", "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    meanings = {"FULL_V1": "all frozen information", "NO_PRICE": "removes historical price information", "NO_CALENDAR_EVENT": "removes calendar/event information", "DEMAND_PRODUCT_ONLY": "keeps demand history plus product identity"}
    for _, row in result_frame.iterrows():
        summary.append(f"| {row['variant']} | {meanings[row['variant']]} | {int(row['feature_count'])} | {row['MAE']:.6f} | {row['RMSE']:.6f} | {row['WAPE']:.6f} | {row['training_seconds']:.3f} | {row['model_size_MiB']:.3f} | {row['WAPE_vs_FULL_pct']:.3f}% |")
    summary.extend([
        "", "## Research Questions", "",
        f"- **RQ-A:** {('Demand/product-only matches or improves FULL_V1 on all three metrics in this validation experiment.' if demand_only['WAPE'] <= full_row['WAPE'] and demand_only['MAE'] <= full_row['MAE'] and demand_only['RMSE'] <= full_row['RMSE'] else 'Demand/product-only does not match FULL_V1 on all three validation metrics; demand history is highly informative but the 11-feature model is not sufficient by this strict criterion.')}",
        f"- **RQ-B:** {_group_answer(full_row, no_calendar, 'calendar/event features')}",
        f"- **RQ-C:** {_group_answer(full_row, no_price, 'historical price features')}",
        f"- **RQ-D:** {('Yes for this validation experiment: the 11-feature model matches or exceeds FULL_V1 on all three metrics.' if demand_only['WAPE'] <= full_row['WAPE'] and demand_only['MAE'] <= full_row['MAE'] and demand_only['RMSE'] <= full_row['RMSE'] else 'No for this validation experiment: the 11-feature model does not match or exceed FULL_V1 on all three metrics.')}",
        "", "## Pre-registered Recommendation", "",
        f"**RECOMMENDED CANDIDATE FOR NEXT-010B: {candidate}.** It has the lowest validation WAPE under the pre-registered WAPE-first rule (MAE/RMSE remain secondary). This is a recommended candidate only; NEXT-010B, not this experiment, formally freezes the forecasting model and feature set.",
        f"The best reduced variant by WAPE is {best_reduced}. Feature count is a parsimony consideration, not a substitute for forecast quality.",
    ])
    (args.tables_dir / "xgboost_feature_ablation_v1_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    _plot_metrics(result_frame, args.figures_dir / "xgboost_feature_ablation_metrics.png")
    _plot_feature_count_wape(result_frame, args.figures_dir / "xgboost_feature_count_vs_wape.png")
    _plot_runtime(result_frame, args.figures_dir / "xgboost_ablation_runtime.png")
    _plot_horizon(
        horizons.query("variant == 'FULL_V1'"), horizons.query("variant == @best_reduced"), best_reduced,
        args.figures_dir / "xgboost_ablation_horizon_mae.png",
    )
    manifest = {
        "experiment_name": ablation["experiment_name"], "status": "VALIDATION_COMPLETE_RECOMMENDATION_PENDING_SELECTION",
        "git_commit_at_run": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPOSITORY_ROOT, text=True).strip(),
        "scope": {"store_id": "CA_1", "category_id": "FOODS", "series_count": 1437}, "training_rows": len(train_frame),
        "feature_counts": {row["variant"]: int(row["feature_count"]) for _, row in result_frame.iterrows()}, "prediction_counts": {row["variant"]: int(row["prediction_count"]) for _, row in result_frame.iterrows()},
        "primary_metric": "WAPE", "secondary_metrics": ["MAE", "RMSE"], "recommended_candidate_for_next_010b": candidate,
        "results_path": "reports/tables/xgboost_feature_ablation_v1_results.csv", "test_access_policy": "TEST sales values were not read, forecast, scored, summarized, or plotted.",
    }
    (args.manifests_dir / "xgboost_feature_ablation_v1.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Completed frozen XGBoost feature-group ablation; recommended candidate: {candidate}.")
    print("TEST SALES VALUES WERE NOT READ OR EVALUATED.")


if __name__ == "__main__":
    main()
