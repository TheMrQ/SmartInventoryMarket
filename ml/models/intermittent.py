"""Transparent, deterministic intermittent-demand forecast methods.

These functions use only a supplied historical sales matrix.  They deliberately
return one nonnegative expected *daily* demand rate per series; callers may
repeat it over a fixed planning horizon without inventing daily variation.
"""

from __future__ import annotations

import numpy as np


def classify_intermittent(history: np.ndarray, zero_rate_threshold: float, window: int = 56) -> np.ndarray:
    """Route a series using only its final pre-origin history window."""
    values = np.asarray(history, dtype=float)
    if values.ndim != 2 or values.shape[1] < window:
        raise ValueError("Regime classification requires a two-dimensional history at least as long as its window.")
    if not 0 <= zero_rate_threshold <= 1:
        raise ValueError("zero_rate_threshold must be between zero and one.")
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Demand history must be finite and nonnegative.")
    return (values[:, -window:] == 0).mean(axis=1) >= zero_rate_threshold


def _validate_history(history: np.ndarray) -> np.ndarray:
    values = np.asarray(history, dtype=float)
    if values.ndim != 2 or values.shape[1] == 0:
        raise ValueError("Intermittent forecasting requires non-empty two-dimensional history.")
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Demand history must be finite and nonnegative.")
    return values


def _validate_alpha(alpha: float, name: str) -> float:
    value = float(alpha)
    if not 0 < value <= 1:
        raise ValueError(f"{name} must be in (0, 1].")
    return value


def croston_rate(history: np.ndarray, alpha: float) -> np.ndarray:
    """Return classic Croston's expected daily demand rate for each series.

    At the first non-zero observation, size is initialized to that demand and
    the interval estimate to one day.  On later non-zero observations, the
    size and elapsed inter-demand interval receive simple exponential updates.
    All-zero histories return zero rather than an undefined rate.
    """
    values = _validate_history(history)
    alpha = _validate_alpha(alpha, "alpha")
    rates = np.zeros(values.shape[0], dtype=np.float64)
    for index, series in enumerate(values):
        size = 0.0
        interval = 1.0
        elapsed = 1
        observed = False
        for demand in series:
            if demand > 0:
                if not observed:
                    size = float(demand)
                    interval = 1.0
                    observed = True
                else:
                    size += alpha * (float(demand) - size)
                    interval += alpha * (elapsed - interval)
                elapsed = 1
            elif observed:
                elapsed += 1
        if observed:
            rates[index] = size / interval
    return rates


def sba_rate(history: np.ndarray, alpha: float) -> np.ndarray:
    """Return Syntetos-Boylan Approximation (SBA) bias-corrected Croston rate."""
    alpha = _validate_alpha(alpha, "alpha")
    return (1 - alpha / 2) * croston_rate(history, alpha)


def tsb_rate(history: np.ndarray, alpha_probability: float, alpha_size: float) -> np.ndarray:
    """Return the Teunter-Syntetos-Babai expected daily rate for each series.

    TSB exponentially updates occurrence probability on every day and the
    non-zero demand-size estimate only when an occurrence happens.  A series
    with no demand remains exactly zero.
    """
    values = _validate_history(history)
    alpha_probability = _validate_alpha(alpha_probability, "alpha_probability")
    alpha_size = _validate_alpha(alpha_size, "alpha_size")
    rates = np.zeros(values.shape[0], dtype=np.float64)
    for index, series in enumerate(values):
        probability = 0.0
        size = 0.0
        observed = False
        for demand in series:
            occurrence = 1.0 if demand > 0 else 0.0
            probability += alpha_probability * (occurrence - probability)
            if occurrence:
                if not observed:
                    size = float(demand)
                    observed = True
                else:
                    size += alpha_size * (float(demand) - size)
        if observed:
            rates[index] = probability * size
    return rates


def intermittent_forecast(history: np.ndarray, method: str, horizon_days: int, **parameters: float) -> np.ndarray:
    """Create a constant, nonnegative daily forecast from a named method."""
    if horizon_days <= 0:
        raise ValueError("horizon_days must be positive.")
    normalized = method.upper()
    if normalized == "CROSTON_CLASSIC":
        rates = croston_rate(history, parameters["alpha"])
    elif normalized == "SBA":
        rates = sba_rate(history, parameters["alpha"])
    elif normalized == "TSB":
        rates = tsb_rate(history, parameters["alpha_probability"], parameters["alpha_size"])
    else:
        raise ValueError(f"Unsupported intermittent method: {method!r}.")
    if not np.isfinite(rates).all() or (rates < 0).any():
        raise ValueError("Intermittent method produced invalid demand rates.")
    return np.repeat(rates[:, None], horizon_days, axis=1)
