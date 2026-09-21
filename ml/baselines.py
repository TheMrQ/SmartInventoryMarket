"""Fixed-origin forecasting baselines for the frozen 28-day M5 protocol."""

from __future__ import annotations

import numpy as np


def _validate_train_sales(train_sales: np.ndarray, minimum_days: int) -> np.ndarray:
    values = np.asarray(train_sales, dtype=float)
    if values.ndim != 2:
        raise ValueError("train_sales must have shape (series, days).")
    if values.shape[1] < minimum_days:
        raise ValueError(f"train_sales needs at least {minimum_days} days.")
    return values


def seasonal_naive_weekly(train_sales: np.ndarray, horizon_days: int = 28) -> np.ndarray:
    """Repeat the final seven known training days across a fixed forecast horizon.

    The function accepts no validation observations, which prevents rolling-origin
    leakage when producing the four-week validation forecast.
    """
    if horizon_days <= 0:
        raise ValueError("horizon_days must be positive.")
    values = _validate_train_sales(train_sales, minimum_days=7)
    final_week = values[:, -7:]
    repetitions = int(np.ceil(horizon_days / 7))
    return np.tile(final_week, (1, repetitions))[:, :horizon_days]


def moving_average_28_day(train_sales: np.ndarray, horizon_days: int = 28) -> np.ndarray:
    """Use each series' final 28 known training days as a fixed mean forecast."""
    if horizon_days <= 0:
        raise ValueError("horizon_days must be positive.")
    values = _validate_train_sales(train_sales, minimum_days=28)
    final_window_mean = values[:, -28:].mean(axis=1, keepdims=True)
    return np.repeat(final_window_mean, horizon_days, axis=1)
