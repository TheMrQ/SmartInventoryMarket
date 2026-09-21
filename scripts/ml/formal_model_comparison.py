"""Create CHECKPOINT-010 validation-only comparison and ablation-plan evidence.

This script reads existing tracked experiment outputs only.  It does not load raw
M5 data, train a model, create forecasts, or access the sealed TEST window.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT))


FEATURE_GROUPS = {
    "sales_lag": ["lag_1", "lag_7", "lag_14", "lag_28"],
    "rolling": ["rolling_mean_7", "rolling_mean_14", "rolling_mean_28", "rolling_std_7", "rolling_std_28"],
    "calendar_event": ["wday", "month", "year", "is_weekend", "snap_CA", "event_name_1_code", "event_type_1_code", "event_name_2_code", "event_type_2_code"],
    "product_identity": ["item_code", "dept_code"],
    "price": ["last_known_sell_price", "price_lag_7", "price_change_from_7_days_ago", "price_available", "price_missing"],
}
METRICS = ("MAE", "RMSE", "WAPE")


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def _metric_columns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.loc[:, ["Method", "MAE", "RMSE", "WAPE_percent"]].copy()
    return result.rename(columns={"Method": "method", "WAPE_percent": "WAPE"})


def build_formal_comparison(
    baselines: pd.DataFrame, lightgbm: pd.DataFrame, xgboost: pd.DataFrame,
    lightgbm_manifest: dict, xgboost_manifest: dict,
) -> pd.DataFrame:
    """Build the four-method table from verified tracked result files."""
    result = pd.concat([
        _metric_columns(baselines),
        _metric_columns(lightgbm).query("method == 'LIGHTGBM_V1'"),
        _metric_columns(xgboost).query("method == 'XGBOOST_V1'"),
    ], ignore_index=True)
    result["training_required"] = result["method"].isin(["LIGHTGBM_V1", "XGBOOST_V1"])
    result["training_seconds"] = np.nan
    result["model_size_MiB"] = np.nan
    result["feature_count"] = np.nan
    metadata = {
        "LIGHTGBM_V1": lightgbm_manifest,
        "XGBOOST_V1": xgboost_manifest,
    }
    for index, row in result.iterrows():
        if row["method"] in metadata:
            manifest = metadata[row["method"]]
            result.loc[index, "training_seconds"] = manifest["training"]["duration_seconds"]
            result.loc[index, "model_size_MiB"] = manifest["model_artifact"]["size_bytes"] / 1024**2
            result.loc[index, "feature_count"] = manifest["training"]["feature_count"]
    for reference_name, slug in (("28-day Moving Average", "moving_average"), ("XGBOOST_V1", "xgboost_v1")):
        reference = result.loc[result["method"] == reference_name].iloc[0]
        for metric in METRICS:
            result[f"{metric}_difference_vs_{slug}"] = result[metric] - reference[metric]
            result[f"{metric}_improvement_pct_vs_{slug}"] = (reference[metric] - result[metric]) / reference[metric] * 100
    return result


def build_feature_group_importance(lightgbm: pd.DataFrame, xgboost: pd.DataFrame) -> pd.DataFrame:
    """Aggregate each model's normalized gain by the frozen feature groups."""
    rows = []
    for model_name, importance in (("LIGHTGBM_V1", lightgbm), ("XGBOOST_V1", xgboost)):
        values = importance.set_index("feature")["normalized_gain_percent"]
        for group, features in FEATURE_GROUPS.items():
            missing = set(features).difference(values.index)
            if missing:
                raise ValueError(f"{model_name} importance is missing frozen features: {sorted(missing)}")
            rows.append({
                "model": model_name, "feature_group": group, "feature_count": len(features),
                "normalized_gain_percent": float(values.loc[features].sum()),
            })
    return pd.DataFrame(rows)


def validate_ablation_config(config: dict, all_features: set[str]) -> None:
    """Verify prescribed ablation groups are mutually interpretable and correctly sized."""
    if config["status"] != "FROZEN_NOT_EXECUTED" or config["primary_metric"] != "WAPE":
        raise ValueError("Ablation plan must remain frozen and use WAPE as the primary metric.")
    variants = config["variants"]
    if set(variants) != {"FULL_V1", "NO_PRICE", "NO_CALENDAR_EVENT", "DEMAND_PRODUCT_ONLY"}:
        raise ValueError("Ablation plan variants differ from the prescribed four variants.")
    if variants["FULL_V1"]["expected_feature_count"] != len(all_features):
        raise ValueError("FULL_V1 count does not match actual FEATURE_SET_V1.")
    for name in ("NO_PRICE", "NO_CALENDAR_EVENT"):
        remaining = all_features.difference(variants[name]["remove_features"])
        if len(remaining) != variants[name]["expected_feature_count"]:
            raise ValueError(f"{name} feature count does not match the actual feature set.")
    kept = set(variants["DEMAND_PRODUCT_ONLY"]["keep_features"])
    if len(kept) != variants["DEMAND_PRODUCT_ONLY"]["expected_feature_count"] or not kept.issubset(all_features):
        raise ValueError("DEMAND_PRODUCT_ONLY features or count are invalid.")


def _plot_formal_comparison(comparison: pd.DataFrame, path: Path) -> None:
    figure, axes = plt.subplots(1, 3, figsize=(15, 4.8), constrained_layout=True)
    colors = ["#4C78A8", "#F58518", "#54A24B", "#B279A2"]
    for axis, metric in zip(axes, METRICS, strict=True):
        values = comparison[metric].to_numpy(dtype=float)
        bars = axis.bar(comparison["method"], values, color=colors)
        axis.set_title("WAPE (%)" if metric == "WAPE" else metric)
        axis.set_ylabel("WAPE (%)" if metric == "WAPE" else metric)
        axis.tick_params(axis="x", rotation=16)
        for bar, value in zip(bars, values, strict=True):
            axis.text(bar.get_x() + bar.get_width() / 2, value, f"{value:.3f}", ha="center", va="bottom", fontsize=8)
    figure.suptitle("M5 CA_1/FOODS: Formal Validation Comparison", fontsize=13)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _plot_group_importance(groups: pd.DataFrame, path: Path) -> None:
    pivoted = groups.pivot(index="feature_group", columns="model", values="normalized_gain_percent").loc[list(FEATURE_GROUPS)]
    figure, axis = plt.subplots(figsize=(9, 5), constrained_layout=True)
    pivoted.plot.bar(ax=axis, color=["#54A24B", "#B279A2"], rot=0)
    axis.set_title("Feature-Group Gain Importance by Model")
    axis.set_xlabel("Feature group")
    axis.set_ylabel("Normalized gain importance (%)")
    axis.legend(title="Model")
    axis.grid(axis="y", alpha=0.25)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _plot_performance_runtime(comparison: pd.DataFrame, path: Path) -> None:
    trained = comparison.loc[comparison["training_required"]].copy()
    figure, axis = plt.subplots(figsize=(7, 4.8), constrained_layout=True)
    colors = {"LIGHTGBM_V1": "#54A24B", "XGBOOST_V1": "#B279A2"}
    for _, row in trained.iterrows():
        axis.scatter(row["training_seconds"], row["WAPE"], s=100, color=colors[row["method"]])
        axis.annotate(row["method"], (row["training_seconds"], row["WAPE"]), xytext=(6, 6), textcoords="offset points")
    axis.set_title("Validation WAPE vs Training Runtime (ML Models Only)")
    axis.set_xlabel("Training runtime (seconds)")
    axis.set_ylabel("Validation WAPE (%) — lower is better")
    axis.grid(alpha=0.3)
    figure.text(0.5, 0.01, "Baselines require no model training and are intentionally excluded.", ha="center", fontsize=8)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _write_markdown(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tables-dir", type=Path, default=REPOSITORY_ROOT / "reports/tables")
    parser.add_argument("--figures-dir", type=Path, default=REPOSITORY_ROOT / "reports/figures")
    parser.add_argument("--manifests-dir", type=Path, default=REPOSITORY_ROOT / "data/manifests")
    parser.add_argument("--ablation-config", type=Path, default=REPOSITORY_ROOT / "configs/experiments/xgboost_feature_ablation_v1.yaml")
    args = parser.parse_args()

    baseline = pd.read_csv(args.tables_dir / "baseline_validation_metrics.csv")
    lightgbm_metrics = pd.read_csv(args.tables_dir / "lightgbm_v1_validation_metrics.csv")
    xgboost_metrics = pd.read_csv(args.tables_dir / "xgboost_v1_validation_metrics.csv")
    with (args.manifests_dir / "lightgbm_v1_validation.json").open(encoding="utf-8") as file:
        lightgbm_manifest = json.load(file)
    with (args.manifests_dir / "xgboost_v1_validation.json").open(encoding="utf-8") as file:
        xgboost_manifest = json.load(file)
    comparison = build_formal_comparison(baseline, lightgbm_metrics, xgboost_metrics, lightgbm_manifest, xgboost_manifest)
    _write_csv(comparison, args.tables_dir / "formal_validation_model_comparison.csv")

    lightgbm_horizon = pd.read_csv(args.tables_dir / "lightgbm_v1_horizon_metrics.csv")
    xgboost_horizon = pd.read_csv(args.tables_dir / "xgboost_v1_horizon_metrics.csv")
    if len(lightgbm_horizon) != 28 or len(xgboost_horizon) != 28 or not lightgbm_horizon["horizon"].equals(xgboost_horizon["horizon"]):
        raise ValueError("Both models must provide aligned 28-day horizon evidence.")
    xgb_lower = int((xgboost_horizon["MAE"] < lightgbm_horizon["MAE"]).sum())
    lgb_lower = int((lightgbm_horizon["MAE"] < xgboost_horizon["MAE"]).sum())
    horizon_lines = [
        "# ML Recursive Horizon Comparison", "",
        f"XGBOOST_V1 has lower MAE on {xgb_lower} of 28 horizons; LIGHTGBM_V1 is lower on {lgb_lower}.",
        "", "| Model | h=1 MAE | h=28 MAE | Minimum MAE (horizon) | Maximum MAE (horizon) | First-7 mean MAE | Last-7 mean MAE |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, frame in (("LIGHTGBM_V1", lightgbm_horizon), ("XGBOOST_V1", xgboost_horizon)):
        minimum = frame.loc[frame["MAE"].idxmin()]
        maximum = frame.loc[frame["MAE"].idxmax()]
        horizon_lines.append(f"| {name} | {frame.iloc[0]['MAE']:.6f} | {frame.iloc[-1]['MAE']:.6f} | {minimum['MAE']:.6f} (h={int(minimum['horizon'])}) | {maximum['MAE']:.6f} (h={int(maximum['horizon'])}) | {frame['MAE'].iloc[:7].mean():.6f} | {frame['MAE'].iloc[-7:].mean():.6f} |")
    horizon_lines.extend([
        "", "Both profiles fluctuate, so the evidence does not support a strict monotonic recursive-error increase. Both models have higher MAE on day 28 than day 1, and their largest errors occur at horizon 14; recursively feeding earlier predictions remains a plausible contributor to later-horizon degradation, not proof of its sole cause.",
        "", "TEST SALES VALUES WERE NOT READ, FORECAST, SCORED, SUMMARIZED, OR PLOTTED.",
    ])
    _write_markdown(args.tables_dir / "ml_horizon_comparison_summary.md", horizon_lines)

    lightgbm_importance = pd.read_csv(args.tables_dir / "lightgbm_v1_feature_importance.csv")
    xgboost_importance = pd.read_csv(args.tables_dir / "xgboost_v1_feature_importance.csv")
    groups = build_feature_group_importance(lightgbm_importance, xgboost_importance)
    _write_csv(groups, args.tables_dir / "model_feature_group_importance.csv")
    all_features = set(lightgbm_importance["feature"])
    with args.ablation_config.open(encoding="utf-8") as file:
        ablation_config = yaml.safe_load(file)
    validate_ablation_config(ablation_config, all_features)

    lgb_resource = comparison.loc[comparison["method"] == "LIGHTGBM_V1"].iloc[0]
    xgb_resource = comparison.loc[comparison["method"] == "XGBOOST_V1"].iloc[0]
    runtime_ratio = xgb_resource["training_seconds"] / lgb_resource["training_seconds"]
    size_ratio = xgb_resource["model_size_MiB"] / lgb_resource["model_size_MiB"]
    resource_lines = [
        "# ML Resource Trade-off Summary", "",
        "| Model | Training seconds | Model size (MiB) | Validation WAPE (%) |", "| --- | ---: | ---: | ---: |",
        f"| LIGHTGBM_V1 | {lgb_resource['training_seconds']:.3f} | {lgb_resource['model_size_MiB']:.3f} | {lgb_resource['WAPE']:.6f} |",
        f"| XGBOOST_V1 | {xgb_resource['training_seconds']:.3f} | {xgb_resource['model_size_MiB']:.3f} | {xgb_resource['WAPE']:.6f} |",
        "", f"XGBOOST_V1 took {runtime_ratio:.3f}× the LightGBM training runtime and produced a {size_ratio:.3f}× larger local artifact. LightGBM is computationally lighter in this experiment; XGBoost has better validation forecasting performance. These are separate dimensions, not a combined winner score.",
        "", "TEST SALES VALUES WERE NOT READ, FORECAST, SCORED, SUMMARIZED, OR PLOTTED.",
    ]
    _write_markdown(args.tables_dir / "ml_resource_tradeoff_summary.md", resource_lines)

    leader = comparison.sort_values(["WAPE", "MAE", "RMSE"], kind="stable").iloc[0]
    comparison_lines = [
        "# Formal Validation Model Comparison", "",
        "All results below are existing, tracked validation-only experiment outputs. Forecast quality and resource cost are intentionally reported separately.", "",
        "| Method | MAE | RMSE | WAPE (%) | Training required | Training seconds | Model size (MiB) | Feature count |", "| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |",
    ]
    for _, row in comparison.iterrows():
        runtime = "—" if pd.isna(row["training_seconds"]) else f"{row['training_seconds']:.3f}"
        size = "—" if pd.isna(row["model_size_MiB"]) else f"{row['model_size_MiB']:.3f}"
        features = "—" if pd.isna(row["feature_count"]) else str(int(row["feature_count"]))
        comparison_lines.append(f"| {row['method']} | {row['MAE']:.6f} | {row['RMSE']:.6f} | {row['WAPE']:.6f} | {bool(row['training_required'])} | {runtime} | {size} | {features} |")
    comparison_lines.extend([
        "", "## Interpretation", "",
        "Seasonal Naive is the weakest current method. The 28-day Moving Average is a strong simple reference. LIGHTGBM_V1 improves Seasonal Naive but does not beat Moving Average. XGBOOST_V1 has the lowest validation MAE, RMSE, and WAPE.",
        "", f"**CURRENT VALIDATION LEADER: {leader['method']}** — this is not a final-model declaration because TEST remains sealed and the frozen feature-group ablation has not run.",
        "", "## Frozen Next Experiment", "",
        "NEXT-010A will run controlled XGBoost feature-group ablation only: FULL_V1 (25 features; existing result reused), NO_PRICE (20), NO_CALENDAR_EVENT (16), and DEMAND_PRODUCT_ONLY (11). All retain the same scope, split, 28-day recursive protocol, XGBoost V1 hyperparameters, seed, and sealed TEST. WAPE is the primary comparison metric; MAE and RMSE are secondary.",
        "", "The research questions are whether demand-only history provides most performance, whether calendar/event or price groups improve validation forecasts, and whether 11 features retain comparable or better error. Gain importance is descriptive and does not preselect a top-k feature model.",
        "", "TEST SALES VALUES WERE NOT READ, FORECAST, SCORED, SUMMARIZED, OR PLOTTED.",
    ])
    _write_markdown(args.tables_dir / "formal_validation_model_comparison.md", comparison_lines)
    _plot_formal_comparison(comparison, args.figures_dir / "formal_validation_model_comparison.png")
    _plot_group_importance(groups, args.figures_dir / "model_feature_group_importance.png")
    _plot_performance_runtime(comparison, args.figures_dir / "ml_validation_performance_vs_runtime.png")
    print("Created CHECKPOINT-010 analysis artifacts from tracked validation outputs only.")


if __name__ == "__main__":
    main()
