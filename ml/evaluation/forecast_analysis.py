"""Validation comparison and horizon metrics without model-specific logic."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ml.evaluation.metrics import aggregate_metrics


def compare_to_moving_average(metrics: pd.DataFrame) -> pd.DataFrame:
    """Add absolute deltas and percentage improvement against Moving Average."""
    result = metrics.copy()
    baseline = result.loc[result["Method"] == "28-day Moving Average"]
    if len(baseline) != 1:
        raise ValueError("Exactly one 28-day Moving Average baseline row is required.")
    for metric in ("MAE", "RMSE", "WAPE_percent"):
        reference = float(baseline.iloc[0][metric])
        result[f"{metric}_difference_vs_moving_average"] = result[metric] - reference
        result[f"{metric}_improvement_pct_vs_moving_average"] = (reference - result[metric]) / reference * 100
    return result


def compare_candidate_to_references(
    metrics: pd.DataFrame, candidate_name: str, reference_names: tuple[str, ...]
) -> pd.DataFrame:
    """Add candidate deltas and improvement percentages versus named references."""
    result = metrics.copy()
    candidate = result.loc[result["Method"] == candidate_name]
    if len(candidate) != 1:
        raise ValueError(f"Exactly one {candidate_name} candidate row is required.")
    for reference_name in reference_names:
        reference = result.loc[result["Method"] == reference_name]
        if len(reference) != 1:
            raise ValueError(f"Exactly one {reference_name} reference row is required.")
        slug = reference_name.lower().replace(" ", "_").replace("-", "_")
        for metric in ("MAE", "RMSE", "WAPE_percent"):
            reference_value = float(reference.iloc[0][metric])
            result[f"{metric}_difference_vs_{slug}"] = np.nan
            result[f"{metric}_improvement_pct_vs_{slug}"] = np.nan
            index = candidate.index[0]
            result.loc[index, f"{metric}_difference_vs_{slug}"] = float(candidate.iloc[0][metric]) - reference_value
            result.loc[index, f"{metric}_improvement_pct_vs_{slug}"] = (reference_value - float(candidate.iloc[0][metric])) / reference_value * 100
    return result


def horizon_metrics(actual: np.ndarray, forecast: np.ndarray, dates: tuple[str, ...]) -> pd.DataFrame:
    """Calculate aggregate MAE/RMSE/WAPE separately for each recursive horizon."""
    actual_values = np.asarray(actual)
    forecast_values = np.asarray(forecast)
    if actual_values.shape != forecast_values.shape or actual_values.shape[1] != len(dates):
        raise ValueError("Actuals, forecasts, and horizon dates must align.")
    rows = []
    for index, date in enumerate(dates, start=1):
        row = aggregate_metrics(actual_values[:, index - 1], forecast_values[:, index - 1])
        rows.append({"horizon": index, "date": date, **row})
    return pd.DataFrame(rows)
