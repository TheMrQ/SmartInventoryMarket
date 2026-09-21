"""Run validation-only fixed-origin baselines for the frozen M5 protocol.

This script intentionally loads sales values through validation d_1913 only.
It does not read, forecast, score, summarize, or plot test sales values.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT))

from ml.baselines import moving_average_28_day, seasonal_naive_weekly
from ml.data.m5_ca1_foods import load_validation_dataset
from ml.evaluation.metrics import aggregate_metrics, per_series_metrics


def _format_metric(value: float) -> str:
    return "N/A" if np.isnan(value) else f"{value:.6f}"


def _write_metrics_csv(rows: list[dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    columns = ["Method", "MAE", "RMSE", "WAPE_percent", "SKU_count", "Validation_days", "Undefined_per_SKU_WAPE_count"]
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _write_summary(
    rows: list[dict[str, object]], per_sku: dict[str, pd.DataFrame], dataset, output_path: Path
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Validation Baseline Summary",
        "",
        "This is a fixed-origin 28-day validation experiment for the frozen M5 `CA_1` / `FOODS` scope.",
        f"Forecast origin: `{dataset.train_day_keys[-1]}`. Validation: `{dataset.validation_day_keys[0]}`–`{dataset.validation_day_keys[-1]}` ({dataset.validation_dates[0]}–{dataset.validation_dates[-1]}).",
        "TEST SALES VALUES WERE NOT READ OR EVALUATED.",
        "",
        "| Method | MAE | RMSE | WAPE (%) | SKUs | Validation days | Undefined per-SKU WAPE |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['Method']} | {_format_metric(float(row['MAE']))} | {_format_metric(float(row['RMSE']))} | "
            f"{_format_metric(float(row['WAPE_percent']))} | {row['SKU_count']} | {row['Validation_days']} | "
            f"{row['Undefined_per_SKU_WAPE_count']} |"
        )
    winners = {
        metric: min(rows, key=lambda row: float(row[metric]))["Method"]
        for metric in ("MAE", "RMSE", "WAPE_percent")
    }
    lines.extend(
        [
            "",
            f"Validation result: **{winners['MAE']}** has the lower MAE; **{winners['RMSE']}** has the lower RMSE; and **{winners['WAPE_percent']}** has the lower WAPE.",
        ]
    )
    lines.extend(["", "## Definitions", "", "- Seasonal Naive repeats each SKU's final seven known train days four times; validation actuals are never used as inputs.", "- 28-day Moving Average repeats each SKU's mean over its final 28 known train days; validation actuals are never used to update it.", "- WAPE = sum(abs(actual - forecast)) / sum(abs(actual)) * 100. Per-SKU WAPE is recorded as undefined when a SKU's validation actual sum is zero.", "", "## Per-SKU Error Findings", ""])
    for method, table in per_sku.items():
        undefined = int(table["WAPE_percent"].isna().sum())
        lines.extend(
            [
                f"### {method}",
                "",
                f"- Median per-SKU MAE: {table['MAE'].median():.6f}",
                f"- Mean per-SKU MAE: {table['MAE'].mean():.6f}",
                f"- 90th-percentile per-SKU MAE: {table['MAE'].quantile(0.9):.6f}",
                f"- Undefined per-SKU WAPE: {undefined} of {len(table)} (zero validation-demand denominator).",
                "",
            ]
        )
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _plot_comparison(rows: list[dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    methods = [str(row["Method"]) for row in rows]
    metrics = [("MAE", "MAE"), ("RMSE", "RMSE"), ("WAPE_percent", "WAPE (%)")]
    figure, axes = plt.subplots(1, 3, figsize=(13, 4.5), constrained_layout=True)
    for axis, (key, label) in zip(axes, metrics, strict=True):
        values = [float(row[key]) for row in rows]
        bars = axis.bar(methods, values, color=["#4C78A8", "#F58518"])
        axis.set_title(label)
        axis.set_ylabel(label)
        axis.tick_params(axis="x", rotation=15)
        for bar, value in zip(bars, values, strict=True):
            axis.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{value:.3f}", ha="center", va="bottom", fontsize=8)
    figure.suptitle("M5 CA_1/FOODS: Fixed-Origin Validation Baseline Comparison", fontsize=13)
    figure.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def _plot_per_sku_distribution(per_sku: dict[str, pd.DataFrame], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    values = [table["MAE"].to_numpy() for table in per_sku.values()]
    maximum = max(float(array.max()) for array in values)
    bins = np.linspace(0, maximum, 36) if maximum > 0 else 10
    figure, axis = plt.subplots(figsize=(8, 5), constrained_layout=True)
    for (method, table), color in zip(per_sku.items(), ["#4C78A8", "#F58518"], strict=True):
        axis.hist(table["MAE"], bins=bins, alpha=0.55, label=method, color=color, edgecolor="white")
    axis.set_title("Per-SKU Validation MAE Distribution")
    axis.set_xlabel("28-day per-SKU MAE (units/day)")
    axis.set_ylabel("Number of SKUs")
    axis.legend(title="Baseline")
    figure.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=REPOSITORY_ROOT / "data/raw/m5")
    parser.add_argument("--config", type=Path, default=REPOSITORY_ROOT / "configs/data/m5_ca1_foods.yaml")
    parser.add_argument("--tables-dir", type=Path, default=REPOSITORY_ROOT / "reports/tables")
    parser.add_argument("--figures-dir", type=Path, default=REPOSITORY_ROOT / "reports/figures")
    args = parser.parse_args()

    dataset = load_validation_dataset(args.raw_dir, args.config)
    horizon = len(dataset.validation_day_keys)
    methods = {
        "Seasonal Naive (lag 7)": seasonal_naive_weekly(dataset.train_sales, horizon),
        "28-day Moving Average": moving_average_28_day(dataset.train_sales, horizon),
    }
    rows: list[dict[str, object]] = []
    per_sku: dict[str, pd.DataFrame] = {}
    for method, forecast in methods.items():
        aggregate = aggregate_metrics(dataset.validation_actuals, forecast)
        series_metrics = per_series_metrics(dataset.validation_actuals, forecast, dataset.item_ids)
        per_sku[method] = series_metrics
        rows.append(
            {
                "Method": method,
                **aggregate,
                "SKU_count": len(dataset.item_ids),
                "Validation_days": horizon,
                "Undefined_per_SKU_WAPE_count": int(series_metrics["WAPE_percent"].isna().sum()),
            }
        )

    _write_metrics_csv(rows, args.tables_dir / "baseline_validation_metrics.csv")
    _write_summary(rows, per_sku, dataset, args.tables_dir / "baseline_validation_summary.md")
    _plot_comparison(rows, args.figures_dir / "baseline_validation_comparison.png")
    _plot_per_sku_distribution(per_sku, args.figures_dir / "baseline_per_sku_error_distribution.png")
    print(f"Evaluated {len(dataset.item_ids)} SKUs over {horizon} validation days.")
    print("TEST SALES VALUES WERE NOT READ OR EVALUATED.")


if __name__ == "__main__":
    main()
