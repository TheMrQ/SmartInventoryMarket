"""Pure, pre-TEST utilities for empirical forecast-reliability evidence."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd


FINAL_TEST_START_DAY = 1914


def day_number(day: str) -> int:
    if not isinstance(day, str) or not day.startswith("d_"):
        raise ValueError(f"invalid M5 day key: {day!r}")
    return int(day.removeprefix("d_"))


def assert_pretest_folds(folds: Iterable[dict]) -> None:
    """Reject any reliability fold that could touch consumed final-TEST sales."""
    for fold in folds:
        if day_number(str(fold["validation_end_d"])) >= FINAL_TEST_START_DAY:
            raise ValueError("forecast reliability may not load final-TEST actuals d_1914 onward")


def residuals(actual: np.ndarray, forecast: np.ndarray) -> np.ndarray:
    actual = np.asarray(actual, dtype=float)
    forecast = np.asarray(forecast, dtype=float)
    if actual.shape != forecast.shape or actual.ndim != 2:
        raise ValueError("actual and forecast must be matching two-dimensional matrices")
    if not np.isfinite(actual).all() or not np.isfinite(forecast).all():
        raise ValueError("residual inputs must be finite")
    return actual - forecast


def sparsity_band(zero_rate: np.ndarray | float) -> np.ndarray | str:
    values = np.asarray(zero_rate, dtype=float)
    if np.any(~np.isfinite(values)) or np.any((values < 0) | (values > 1)):
        raise ValueError("zero-demand rate must be within [0, 1]")
    labels = np.select(
        [values <= .25, values <= .50, values <= .75],
        ["0-25% zero", "25-50% zero", "50-75% zero"],
        default="75-100% zero",
    )
    return str(labels.item()) if values.ndim == 0 else labels


def _quantile_bounds(values: pd.Series, coverage: float) -> tuple[float, float]:
    if not 0 < coverage < 1:
        raise ValueError("coverage must be between zero and one")
    alpha = (1 - coverage) / 2
    return float(values.quantile(alpha)), float(values.quantile(1 - alpha))


def calibration_table(residual_rows: pd.DataFrame, coverages: Iterable[float], minimum_sample_size: int) -> pd.DataFrame:
    """Build asymmetric empirical residual quantiles at each fallback tier."""
    required = {"horizon_day", "sparsity_band", "residual"}
    if required.difference(residual_rows.columns):
        raise ValueError("residual rows lack interval-calibration columns")
    if minimum_sample_size < 1:
        raise ValueError("minimum calibration sample size must be positive")
    rows: list[dict] = []
    groups = [
        ("horizon_and_sparsity", ["horizon_day", "sparsity_band"]),
        ("horizon", ["horizon_day"]),
        ("global", []),
    ]
    for coverage in coverages:
        for level, columns in groups:
            grouped = [((), residual_rows)] if not columns else residual_rows.groupby(columns, observed=True)
            for keys, values in grouped:
                keys = keys if isinstance(keys, tuple) else (keys,)
                lower, upper = _quantile_bounds(values["residual"], coverage)
                row = {
                    "coverage": float(coverage), "level": level, "sample_size": int(len(values)),
                    "residual_lower": lower, "residual_upper": upper,
                    "usable": bool(len(values) >= minimum_sample_size),
                    "horizon_day": None, "sparsity_band": None,
                }
                for column, value in zip(columns, keys, strict=True):
                    row[column] = int(value) if column == "horizon_day" else str(value)
                rows.append(row)
    return pd.DataFrame(rows)


def resolve_interval(calibration: pd.DataFrame, horizon_day: int, band: str, coverage: float) -> pd.Series:
    """Resolve horizon+regime, then horizon, then global—never a tiny bucket."""
    base = calibration.loc[(calibration["coverage"] == float(coverage)) & calibration["usable"]]
    ordered = [
        base.loc[(base["level"] == "horizon_and_sparsity") & (base["horizon_day"] == horizon_day) & (base["sparsity_band"] == band)],
        base.loc[(base["level"] == "horizon") & (base["horizon_day"] == horizon_day)],
        base.loc[base["level"] == "global"],
    ]
    for candidate in ordered:
        if len(candidate) == 1:
            return candidate.iloc[0]
    raise ValueError("no usable residual interval is available")


def physical_interval(point_forecast: float, residual_lower: float, residual_upper: float) -> tuple[float, float]:
    """Clamp only the final lower physical-demand bound, never residuals."""
    if not np.isfinite([point_forecast, residual_lower, residual_upper]).all():
        raise ValueError("interval inputs must be finite")
    lower = max(0.0, float(point_forecast) + float(residual_lower))
    upper = max(lower, float(point_forecast) + float(residual_upper))
    return lower, upper


def apply_intervals(rows: pd.DataFrame, calibration: pd.DataFrame, coverage: float) -> pd.DataFrame:
    """Return nonnegative forecast intervals without altering point estimates."""
    required = {"horizon_day", "sparsity_band", "point_forecast"}
    if required.difference(rows.columns):
        raise ValueError("forecast rows lack interval-application columns")
    output = rows.copy()
    resolved = [resolve_interval(calibration, int(row.horizon_day), str(row.sparsity_band), coverage) for row in output.itertuples()]
    output["interval_level"] = [str(row.level) for row in resolved]
    output["residual_lower"] = [float(row.residual_lower) for row in resolved]
    output["residual_upper"] = [float(row.residual_upper) for row in resolved]
    bounds = [physical_interval(row.point_forecast, row.residual_lower, row.residual_upper) for row in output.itertuples()]
    output["lower_bound"] = [pair[0] for pair in bounds]
    output["upper_bound"] = [pair[1] for pair in bounds]
    output["interval_width"] = output["upper_bound"] - output["lower_bound"]
    return output


def evidence_level(zero_rate: float, mae: float, width: float, mae_p50: float, mae_p75: float, width_p50: float, width_p75: float) -> str:
    """Qualitative labels derived from backtest distribution thresholds."""
    if zero_rate >= .65 or mae >= mae_p75 or width >= width_p75:
        return "LIMITED"
    if zero_rate <= .25 and mae <= mae_p50 and width <= width_p50:
        return "HIGHER"
    return "MODERATE"
