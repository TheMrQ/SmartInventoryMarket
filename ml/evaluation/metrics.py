"""Reusable aggregate and per-series metrics for nonnegative demand forecasts."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd


def _validated_arrays(actual: np.ndarray, forecast: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    actual_values = np.asarray(actual, dtype=float)
    forecast_values = np.asarray(forecast, dtype=float)
    if actual_values.shape != forecast_values.shape:
        raise ValueError("actual and forecast must have the same shape.")
    if actual_values.size == 0:
        raise ValueError("actual and forecast cannot be empty.")
    return actual_values, forecast_values


def mae(actual: np.ndarray, forecast: np.ndarray) -> float:
    """Mean absolute error."""
    actual_values, forecast_values = _validated_arrays(actual, forecast)
    return float(np.mean(np.abs(actual_values - forecast_values)))


def rmse(actual: np.ndarray, forecast: np.ndarray) -> float:
    """Root mean squared error."""
    actual_values, forecast_values = _validated_arrays(actual, forecast)
    return float(np.sqrt(np.mean((actual_values - forecast_values) ** 2)))


def wape_percent(actual: np.ndarray, forecast: np.ndarray) -> float:
    """Weighted absolute percentage error, or NaN when actual demand sums to zero."""
    actual_values, forecast_values = _validated_arrays(actual, forecast)
    denominator = float(np.sum(np.abs(actual_values)))
    if denominator == 0:
        return float("nan")
    return float(np.sum(np.abs(actual_values - forecast_values)) / denominator * 100)


def aggregate_metrics(actual: np.ndarray, forecast: np.ndarray) -> dict[str, float]:
    """Calculate frozen thesis-level metrics across every SKU-day observation."""
    return {"MAE": mae(actual, forecast), "RMSE": rmse(actual, forecast), "WAPE_percent": wape_percent(actual, forecast)}


def per_series_metrics(
    actual: np.ndarray, forecast: np.ndarray, item_ids: Iterable[str]
) -> pd.DataFrame:
    """Calculate MAE/RMSE/WAPE per SKU, retaining undefined zero-demand WAPE as NaN."""
    actual_values, forecast_values = _validated_arrays(actual, forecast)
    if actual_values.ndim != 2:
        raise ValueError("Per-series metrics require two-dimensional (series, days) arrays.")
    identifiers = list(item_ids)
    if len(identifiers) != actual_values.shape[0]:
        raise ValueError("item_ids count must match the number of series.")
    errors = actual_values - forecast_values
    denominator = np.sum(np.abs(actual_values), axis=1)
    numerators = np.sum(np.abs(errors), axis=1)
    wape = np.full(actual_values.shape[0], np.nan, dtype=float)
    np.divide(numerators * 100, denominator, out=wape, where=denominator != 0)
    return pd.DataFrame(
        {
            "item_id": identifiers,
            "MAE": np.mean(np.abs(errors), axis=1),
            "RMSE": np.sqrt(np.mean(errors**2, axis=1)),
            "WAPE_percent": wape,
            "validation_actual_sum": denominator,
        }
    )
