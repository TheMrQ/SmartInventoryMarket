from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.features.builder import (
    build_encodings,
    build_single_step_inference_features,
    build_training_features,
    encode_calendar_features,
    load_feature_config,
)


def _config() -> dict[str, object]:
    return {
        "feature_set": "FEATURE_SET_V1",
        "model_formulation": "global_one_step_regression",
        "recursive_forecasting": True,
        "sales_lags": [1, 7, 14, 28],
        "rolling_mean_windows": [7, 14, 28],
        "rolling_std_windows": [7, 28],
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
        "warmup_days": 28,
        "price_policy": "past_only_forward_fill_within_item_store",
    }


def _calendar(days: int = 32) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "d_index": np.arange(1, days + 1),
            "d": [f"d_{index}" for index in range(1, days + 1)],
            "date": pd.date_range("2011-01-29", periods=days, freq="D").astype(str),
            "wm_yr_wk": np.repeat(np.arange(100, 100 + (days + 6) // 7), 7)[:days],
            "wday": (np.arange(days) % 7) + 1,
            "month": 1,
            "year": 2011,
            "snap_CA": 0,
            "event_name_1": [None] * days,
            "event_type_1": [None] * days,
            "event_name_2": [None] * days,
            "event_type_2": [None] * days,
        }
    )


def _metadata() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "item_id": ["item_b", "item_a"],
            "dept_id": ["FOODS_2", "FOODS_1"],
            "cat_id": ["FOODS", "FOODS"],
            "store_id": ["CA_1", "CA_1"],
        }
    )


def _result(sales: np.ndarray | None = None, prices: np.ndarray | None = None):
    sales = np.vstack([np.arange(32), np.arange(100, 132)]).astype(np.int16) if sales is None else sales
    prices = np.vstack([np.full(32, 2.0), np.full(32, 3.0)]).astype(np.float32) if prices is None else prices
    calendar = _calendar()
    return build_training_features(_metadata(), sales, calendar, calendar, prices, _config())


def test_lags_and_rolling_features_are_past_only_and_correct() -> None:
    result = _result()
    first = result.frame.iloc[0]

    assert first["sales_target"] == 28
    assert first["lag_1"] == 27
    assert first["lag_7"] == 21
    assert first["lag_14"] == 14
    assert first["lag_28"] == 0
    assert first["rolling_mean_7"] == 24
    assert first["rolling_mean_28"] == 13.5
    assert np.isclose(first["rolling_std_7"], np.std(np.arange(21, 28), ddof=0))


def test_target_and_future_sales_mutations_do_not_change_existing_features() -> None:
    base = _result().frame
    sales_target_mutated = np.vstack([np.arange(32), np.arange(100, 132)]).astype(np.int16)
    sales_target_mutated[0, 28] = 777
    target_mutated = _result(sales=sales_target_mutated).frame
    feature_columns = [column for column in base.columns if column not in {"d_index", "date", "sales_target"}]
    assert base.loc[0, feature_columns].equals(target_mutated.loc[0, feature_columns])
    assert base.loc[0, "sales_target"] != target_mutated.loc[0, "sales_target"]

    sales_future_mutated = np.vstack([np.arange(32), np.arange(100, 132)]).astype(np.int16)
    sales_future_mutated[0, 30:] = 999
    future_mutated = _result(sales=sales_future_mutated).frame
    earlier = base["d_index"] <= 29
    assert base.loc[earlier, feature_columns].equals(future_mutated.loc[earlier, feature_columns])


def test_price_features_exclude_target_day_and_future_prices() -> None:
    base = _result().frame
    changed_prices = np.vstack([np.full(32, 2.0), np.full(32, 3.0)]).astype(np.float32)
    changed_prices[0, 28:] = 99.0
    changed = _result(prices=changed_prices).frame
    price_columns = [
        "last_known_sell_price",
        "price_lag_7",
        "price_change_from_7_days_ago",
        "price_available",
        "price_missing",
    ]
    assert base.loc[0, price_columns].equals(changed.loc[0, price_columns])
    assert base.loc[0, "last_known_sell_price"] == 2.0


def test_deterministic_encodings_and_calendar_mapping() -> None:
    metadata = _metadata()
    calendar = _calendar()
    first = build_encodings(metadata, calendar)
    second = build_encodings(metadata.iloc[::-1], calendar)

    assert first.item_codes == second.item_codes == {"item_a": 0, "item_b": 1}
    encoded = encode_calendar_features(calendar.iloc[[0]], first)
    assert encoded.loc[0, "event_name_1_code"] == first.event_codes["event_name_1"]["__NONE__"]
    assert encoded.loc[0, "is_weekend"] == 1


def test_recursive_inference_features_use_only_explicit_history() -> None:
    metadata = _metadata()
    calendar = _calendar()
    config = _config()
    encodings = build_encodings(metadata, calendar)
    history_sales = np.vstack([np.arange(28), np.arange(100, 128)]).astype(np.int16)
    history_prices = np.vstack([np.full(28, 2.0), np.full(28, 3.0)]).astype(np.float32)

    inference = build_single_step_inference_features(
        history_sales, history_prices, calendar.iloc[[28]], metadata, encodings, config
    )

    assert inference.shape == (2, 25)
    assert inference.loc[0, "lag_1"] == 27
    assert inference.loc[0, "lag_28"] == 0
    assert inference.loc[0, "rolling_mean_7"] == 24


def test_feature_config_validation_rejects_changed_frozen_definition(tmp_path) -> None:
    config = _config()
    config["sales_lags"] = [1, 7]
    path = tmp_path / "invalid.yaml"
    import yaml

    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(ValueError, match="sales_lags"):
        load_feature_config(path)
