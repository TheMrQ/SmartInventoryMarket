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
