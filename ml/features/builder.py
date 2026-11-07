"""FEATURE_SET_V1 construction for a global one-step recursive forecast model.

Training rows use historical information before target day ``t``. The same
array helpers also build one-step inference features from an explicit history;
they never load sales data themselves and therefore cannot access future actuals.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml


EVENT_COLUMNS = ("event_name_1", "event_type_1", "event_name_2", "event_type_2")
CALENDAR_NUMERIC_COLUMNS = ("wday", "month", "year", "is_weekend", "snap_CA")


@dataclass(frozen=True)
class FeatureEncodings:
    """Deterministic product and event categorical encodings."""

    item_codes: dict[str, int]
    dept_codes: dict[str, int]
    event_codes: dict[str, dict[str, int]]


@dataclass(frozen=True)
class FeatureBuildResult:
    """Compact training table plus the metadata required for later inference."""

    frame: pd.DataFrame
    feature_names: tuple[str, ...]
    encodings: FeatureEncodings
    warmup_days: int
    dropped_warmup_rows: int


def load_feature_config(config_path: str | Path) -> dict[str, Any]:
    """Load a supported feature schema while keeping FEATURE_SET_V1 immutable.

    FEATURE_SET_V2 is deliberately a separate P23 research schema.  It shares
    the same past-only builder, but its values are validated independently so a
    caller cannot silently alter the frozen V1 definition.
    """
    with Path(config_path).open(encoding="utf-8") as file:
        config = yaml.safe_load(file)
    if not isinstance(config, dict):
        raise ValueError("Feature configuration must be a YAML mapping.")
    required = {
        "feature_set",
        "model_formulation",
        "recursive_forecasting",
        "sales_lags",
        "rolling_mean_windows",
        "rolling_std_windows",
        "calendar_numeric_features",
        "calendar_categorical_features",
        "product_categorical_features",
        "price_features",
        "warmup_days",
        "price_policy",
    }
    missing = required.difference(config)
    if missing:
        raise ValueError(f"Feature configuration missing keys: {sorted(missing)}")
    expected_v1 = {
        "feature_set": "FEATURE_SET_V1",
        "model_formulation": "global_one_step_regression",
        "recursive_forecasting": True,
        "sales_lags": [1, 7, 14, 28],
        "rolling_mean_windows": [7, 14, 28],
        "rolling_std_windows": [7, 28],
        "warmup_days": 28,
        "calendar_numeric_features": ["wday", "month", "year", "is_weekend", "snap_CA"],
        "calendar_categorical_features": ["event_name_1", "event_type_1", "event_name_2", "event_type_2"],
        "product_categorical_features": ["item_id", "dept_id"],
        "price_features": [
            "last_known_sell_price",
            "price_lag_7",
            "price_change_from_7_days_ago",
            "price_available",
            "price_missing",
        ],
        "price_policy": "past_only_forward_fill_within_item_store",
    }
    if config["feature_set"] == "FEATURE_SET_V1":
        for key, value in expected_v1.items():
            if config[key] != value:
                raise ValueError(f"FEATURE_SET_V1 requires {key}={value!r}.")
        return config

    expected_v2 = {
        "feature_set": "FEATURE_SET_V2",
        "model_formulation": "global_one_step_regression",
        "recursive_forecasting": True,
        "sales_lags": [1, 2, 3, 7, 14, 21, 28, 35, 56],
        "rolling_mean_windows": [3, 7, 14, 28, 56],
        "rolling_std_windows": [7, 14, 28, 56],
        "warmup_days": 56,
        "calendar_numeric_features": ["wday", "month", "year", "is_weekend", "snap_CA"],
        "calendar_categorical_features": ["event_name_1", "event_type_1", "event_name_2", "event_type_2"],
        "product_categorical_features": ["item_id", "dept_id"],
        "price_features": [
            "last_known_sell_price", "price_lag_7", "price_change_from_7_days_ago",
            "price_available", "price_missing",
        ],
        "price_policy": "past_only_forward_fill_within_item_store",
    }
    for key, value in expected_v2.items():
        if config["feature_set"] == "FEATURE_SET_V2" and config[key] != value:
            raise ValueError(f"FEATURE_SET_V2 requires {key}={value!r}.")
    if config["feature_set"] == "FEATURE_SET_V2":
        return config

    expected_v3 = {
        **expected_v2,
        "feature_set": "FEATURE_SET_V3",
        "intermittent_features": {
            "zero_rate_windows": [28, 56],
            "nonzero_mean_windows": [28, 56],
            "median_windows": [28],
            "days_since_last_nonzero_cap": 56,
            "trend_pairs": [[7, 28], [28, 56]],
            "all_zero_nonzero_mean_policy": "zero_with_explicit_has_nonzero_flag",
        },
    }
    if config["feature_set"] != "FEATURE_SET_V3":
        raise ValueError(f"Unsupported feature set: {config['feature_set']!r}.")
    if "intermittent_features" not in config:
        raise ValueError("FEATURE_SET_V3 requires intermittent_features.")
    for key, value in expected_v3.items():
        if config.get(key) != value:
            raise ValueError(f"FEATURE_SET_V3 requires {key}={value!r}.")
    return config


def build_encodings(metadata: pd.DataFrame, calendar_metadata: pd.DataFrame) -> FeatureEncodings:
    """Create deterministic integer codes without replacing M5 item identities."""
    item_values = sorted(metadata["item_id"].astype(str).unique())
    dept_values = sorted(metadata["dept_id"].astype(str).unique())
    event_codes: dict[str, dict[str, int]] = {}
    for column in EVENT_COLUMNS:
        values = sorted(calendar_metadata[column].fillna("__NONE__").astype(str).unique())
        event_codes[column] = {value: index for index, value in enumerate(values)}
    return FeatureEncodings(
        item_codes={value: index for index, value in enumerate(item_values)},
        dept_codes={value: index for index, value in enumerate(dept_values)},
        event_codes=event_codes,
    )


def encode_calendar_features(calendar: pd.DataFrame, encodings: FeatureEncodings) -> pd.DataFrame:
    """Encode known-in-advance calendar/event values with stable compact dtypes."""
    required = {"wday", "month", "year", "snap_CA", *EVENT_COLUMNS}
    missing = required.difference(calendar.columns)
    if missing:
        raise ValueError(f"Calendar input missing columns: {sorted(missing)}")
    encoded = pd.DataFrame(index=calendar.index)
    encoded["wday"] = calendar["wday"].astype("int8")
    encoded["month"] = calendar["month"].astype("int8")
    encoded["year"] = calendar["year"].astype("int16")
    encoded["is_weekend"] = calendar["wday"].isin([1, 2]).astype("int8")
    encoded["snap_CA"] = calendar["snap_CA"].astype("int8")
    for column in EVENT_COLUMNS:
        mapping = encodings.event_codes[column]
        values = calendar[column].fillna("__NONE__").astype(str)
        encoded[f"{column}_code"] = values.map(mapping).fillna(-1).astype("int16")
    return encoded


def _forward_fill_past_only(values: np.ndarray) -> np.ndarray:
    """Forward-fill within each row; never back-fill a first missing price."""
    result = np.asarray(values, dtype=np.float32).copy()
    for index in range(1, result.shape[1]):
        missing = np.isnan(result[:, index])
        result[missing, index] = result[missing, index - 1]
    return result


def _validate_history_positions(history: np.ndarray, positions: np.ndarray, warmup_days: int) -> np.ndarray:
    values = np.asarray(history)
    if values.ndim != 2:
        raise ValueError("Historical sales must have shape (series, days).")
    if positions.ndim != 1 or len(positions) == 0:
        raise ValueError("Target positions must be a non-empty one-dimensional array.")
    if positions.min() < warmup_days or positions.max() > values.shape[1]:
        raise ValueError("Target positions require 28 prior observations and cannot exceed supplied history.")
    return values


def _sales_feature_arrays(
    history_sales: np.ndarray, positions: np.ndarray, config: dict[str, Any], lag_dtype: np.dtype = np.int16
) -> dict[str, np.ndarray]:
    """Return past-only lag/rolling feature blocks for target positions.

    Position ``p`` means target day ``p`` in zero-based indexing; only history
    values with indices strictly lower than ``p`` are accessed.
    """
    warmup = int(config["warmup_days"])
    sales = _validate_history_positions(history_sales, positions, warmup).astype(np.float32, copy=False)
    features: dict[str, np.ndarray] = {}
    for lag in config["sales_lags"]:
        features[f"lag_{lag}"] = sales[:, positions - lag].astype(lag_dtype, copy=False)

    cumulative = np.concatenate([np.zeros((sales.shape[0], 1), dtype=np.float64), np.cumsum(sales, axis=1, dtype=np.float64)], axis=1)
    squared_cumulative = np.concatenate(
        [np.zeros((sales.shape[0], 1), dtype=np.float64), np.cumsum(sales**2, axis=1, dtype=np.float64)], axis=1
    )
    for window in config["rolling_mean_windows"]:
        sums = cumulative[:, positions] - cumulative[:, positions - window]
        features[f"rolling_mean_{window}"] = (sums / window).astype(np.float32)
    for window in config["rolling_std_windows"]:
        sums = cumulative[:, positions] - cumulative[:, positions - window]
        squared_sums = squared_cumulative[:, positions] - squared_cumulative[:, positions - window]
        variance = np.maximum(squared_sums / window - (sums / window) ** 2, 0)
        features[f"rolling_std_{window}"] = np.sqrt(variance).astype(np.float32)
    return features


def _intermittent_feature_arrays(
    history_sales: np.ndarray, positions: np.ndarray, config: dict[str, Any]
) -> dict[str, np.ndarray]:
    """Build deterministic past-only intermittent-demand signals for V3.

    A position is a target day, so every slice ends at ``position`` and cannot
    include the target or a future sale.  Non-zero means use 0 when no sale was
    observed in the requested window; a paired flag makes that policy explicit
    instead of using an imputed hidden value.
    """
    definition = config.get("intermittent_features")
    if not definition:
        return {}
    sales = _validate_history_positions(history_sales, positions, int(config["warmup_days"])).astype(np.float32, copy=False)
    result: dict[str, np.ndarray] = {}
    for window in definition["zero_rate_windows"]:
        values = sales[:, positions[:, None] - window + np.arange(window)]
        result[f"zero_demand_rate_{window}"] = (values == 0).mean(axis=2).astype(np.float32)
    for window in definition["nonzero_mean_windows"]:
        values = sales[:, positions[:, None] - window + np.arange(window)]
        observed = values != 0
        count = observed.sum(axis=2)
        totals = np.where(observed, values, 0).sum(axis=2)
        result[f"nonzero_demand_mean_{window}"] = np.divide(
            totals, count, out=np.zeros_like(totals, dtype=np.float32), where=count > 0
        ).astype(np.float32)
        result[f"has_nonzero_demand_{window}"] = (count > 0).astype(np.int8)
    for window in definition["median_windows"]:
        values = sales[:, positions[:, None] - window + np.arange(window)]
        result[f"rolling_median_{window}"] = np.median(values, axis=2).astype(np.float32)
    cap = int(definition["days_since_last_nonzero_cap"])
    values = sales[:, positions[:, None] - cap + np.arange(cap)]
    reverse_nonzero = (values != 0)[:, :, ::-1]
    has_nonzero = reverse_nonzero.any(axis=2)
    since = np.where(has_nonzero, reverse_nonzero.argmax(axis=2), cap).astype(np.int16)
    result[f"days_since_last_nonzero_capped_{cap}"] = since
    for short, long in definition["trend_pairs"]:
        short_values = sales[:, positions[:, None] - short + np.arange(short)]
        long_values = sales[:, positions[:, None] - long + np.arange(long)]
        result[f"rolling_mean_trend_{short}_vs_{long}"] = (
            short_values.mean(axis=2) - long_values.mean(axis=2)
        ).astype(np.float32)
    return result


def _price_feature_arrays(price_history: np.ndarray, positions: np.ndarray, config: dict[str, Any]) -> dict[str, np.ndarray]:
    """Return price features from price observations strictly before each target."""
    prices = _validate_history_positions(price_history, positions, int(config["warmup_days"]))
    known_prices = _forward_fill_past_only(prices)
    last_known = known_prices[:, positions - 1]
    lag_7 = known_prices[:, positions - 7]
    change = last_known - lag_7
    return {
        "last_known_sell_price": last_known.astype(np.float32),
        "price_lag_7": lag_7.astype(np.float32),
        "price_change_from_7_days_ago": change.astype(np.float32),
        "price_available": (~np.isnan(last_known)).astype(np.int8),
        "price_missing": np.isnan(last_known).astype(np.int8),
    }


def build_daily_price_matrix(
    price_rows: pd.DataFrame, item_ids: tuple[str, ...], train_calendar: pd.DataFrame
) -> np.ndarray:
    """Map weekly M5 prices to daily train dates for the selected store/items."""
    required_prices = {"item_id", "wm_yr_wk", "sell_price"}
    if required_prices.difference(price_rows.columns):
        raise ValueError("Price rows are missing a required M5 price column.")
    weekly = price_rows.pivot(index="item_id", columns="wm_yr_wk", values="sell_price")
    daily_weeks = train_calendar["wm_yr_wk"].to_numpy()
    matrix = weekly.reindex(index=list(item_ids), columns=daily_weeks).to_numpy(dtype=np.float32)
    return matrix


def load_train_price_rows(raw_directory: str | Path, item_ids: tuple[str, ...], train_calendar: pd.DataFrame) -> pd.DataFrame:
    """Read only selected CA_1 items/weeks needed for training price history."""
    price_path = Path(raw_directory) / "sell_prices.csv"
    if not price_path.is_file():
        raise FileNotFoundError(f"Required local M5 file is missing: {price_path}")
    selected_items = set(item_ids)
    selected_weeks = set(train_calendar["wm_yr_wk"].astype(int))
    pieces: list[pd.DataFrame] = []
    for chunk in pd.read_csv(price_path, chunksize=100_000):
        selected = chunk.loc[
            (chunk["store_id"] == "CA_1")
            & (chunk["item_id"].isin(selected_items))
            & (chunk["wm_yr_wk"].isin(selected_weeks)),
            ["item_id", "wm_yr_wk", "sell_price"],
        ]
        if not selected.empty:
            pieces.append(selected)
    if not pieces:
        raise ValueError("No CA_1 price rows were found for the frozen training scope.")
    prices = pd.concat(pieces, ignore_index=True)
    if prices.duplicated(["item_id", "wm_yr_wk"]).any():
        raise ValueError("M5 price keys are unexpectedly duplicated for the frozen scope.")
    return prices


def _feature_names(config: dict[str, Any]) -> tuple[str, ...]:
    names = (
        [f"lag_{lag}" for lag in config["sales_lags"]]
        + [f"rolling_mean_{window}" for window in config["rolling_mean_windows"]]
        + [f"rolling_std_{window}" for window in config["rolling_std_windows"]]
        + list(CALENDAR_NUMERIC_COLUMNS)
        + [f"{column}_code" for column in EVENT_COLUMNS]
        + ["item_code", "dept_code"]
        + list(config["price_features"])
    )
    definition = config.get("intermittent_features")
    if definition:
        names += (
            [f"zero_demand_rate_{window}" for window in definition["zero_rate_windows"]]
            + [f"nonzero_demand_mean_{window}" for window in definition["nonzero_mean_windows"]]
            + [f"has_nonzero_demand_{window}" for window in definition["nonzero_mean_windows"]]
            + [f"rolling_median_{window}" for window in definition["median_windows"]]
            + [f"days_since_last_nonzero_capped_{definition['days_since_last_nonzero_cap']}"]
            + [f"rolling_mean_trend_{short}_vs_{long}" for short, long in definition["trend_pairs"]]
        )
    return tuple(names)


def build_training_features(
    metadata: pd.DataFrame,
    train_sales: np.ndarray,
    train_calendar: pd.DataFrame,
    calendar_metadata: pd.DataFrame,
    daily_prices: np.ndarray,
    config: dict[str, Any],
) -> FeatureBuildResult:
    """Build compact long-form training rows without target/current/future leakage."""
    warmup = int(config["warmup_days"])
    if train_sales.shape != daily_prices.shape:
        raise ValueError("Sales and daily-price matrices must have the same shape.")
    if len(metadata) != train_sales.shape[0] or len(train_calendar) != train_sales.shape[1]:
        raise ValueError("Metadata, calendar, and sales dimensions do not align.")
    encodings = build_encodings(metadata, calendar_metadata)
    positions = np.arange(warmup, train_sales.shape[1], dtype=np.int32)
    sales_features = _sales_feature_arrays(train_sales, positions, config)
    intermittent_features = _intermittent_feature_arrays(train_sales, positions, config)
    price_features = _price_feature_arrays(daily_prices, positions, config)
    calendar_features = encode_calendar_features(train_calendar, encodings).iloc[positions].reset_index(drop=True)
    item_codes = metadata["item_id"].astype(str).map(encodings.item_codes).to_numpy(dtype=np.int16)
    dept_codes = metadata["dept_id"].astype(str).map(encodings.dept_codes).to_numpy(dtype=np.int8)
    series_count, target_count = train_sales.shape[0], len(positions)

    columns: dict[str, np.ndarray] = {
        "d_index": np.tile(train_calendar["d_index"].to_numpy(dtype=np.int16)[positions], series_count),
        "date": np.tile(pd.to_datetime(train_calendar["date"]).to_numpy()[positions], series_count),
        "item_code": np.repeat(item_codes, target_count),
        "dept_code": np.repeat(dept_codes, target_count),
    }
    for name, values in sales_features.items():
        columns[name] = values.reshape(-1)
    for name, values in intermittent_features.items():
        columns[name] = values.reshape(-1)
    for name in CALENDAR_NUMERIC_COLUMNS:
        columns[name] = np.tile(calendar_features[name].to_numpy(), series_count)
    for column in EVENT_COLUMNS:
        name = f"{column}_code"
        columns[name] = np.tile(calendar_features[name].to_numpy(), series_count)
    for name, values in price_features.items():
        columns[name] = values.reshape(-1)
    columns["sales_target"] = train_sales[:, positions].reshape(-1).astype(np.int16)
    frame = pd.DataFrame(columns)
    feature_names = _feature_names(config)
    return FeatureBuildResult(
        frame=frame,
        feature_names=feature_names,
        encodings=encodings,
        warmup_days=warmup,
        dropped_warmup_rows=series_count * warmup,
    )


def build_single_step_inference_features(
    history_sales: np.ndarray,
    history_prices: np.ndarray,
    target_calendar: pd.DataFrame,
    metadata: pd.DataFrame,
    encodings: FeatureEncodings,
    config: dict[str, Any],
) -> pd.DataFrame:
    """Build one target-day feature row per SKU from explicit past histories only.

    Callers append prior recursive predictions to ``history_sales`` before the
    next step. This function never reads a raw file or validation/test actuals.
    """
    sales = np.asarray(history_sales, dtype=np.float32)
    prices = np.asarray(history_prices, dtype=np.float32)
    if sales.shape != prices.shape or sales.shape[0] != len(metadata):
        raise ValueError("History sales, prices, and metadata must align by series.")
    if len(target_calendar) != 1:
        raise ValueError("Single-step inference requires exactly one target calendar row.")
    positions = np.array([sales.shape[1]], dtype=np.int32)
    sales_features = _sales_feature_arrays(sales, positions, config, lag_dtype=np.float32)
    intermittent_features = _intermittent_feature_arrays(sales, positions, config)
    price_features = _price_feature_arrays(prices, positions, config)
    calendar_features = encode_calendar_features(target_calendar, encodings).iloc[0]
    frame: dict[str, np.ndarray] = {
        "item_code": metadata["item_id"].astype(str).map(encodings.item_codes).to_numpy(dtype=np.int16),
        "dept_code": metadata["dept_id"].astype(str).map(encodings.dept_codes).to_numpy(dtype=np.int8),
    }
    frame.update({name: values[:, 0] for name, values in sales_features.items()})
    frame.update({name: values[:, 0] for name, values in intermittent_features.items()})
    frame.update({name: values[:, 0] for name, values in price_features.items()})
    for name in CALENDAR_NUMERIC_COLUMNS:
        frame[name] = np.repeat(calendar_features[name], len(metadata))
    for column in EVENT_COLUMNS:
        name = f"{column}_code"
        frame[name] = np.repeat(calendar_features[name], len(metadata))
    result = pd.DataFrame(frame)
    return result.loc[:, list(_feature_names(config))]
