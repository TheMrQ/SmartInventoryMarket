from __future__ import annotations

import numpy as np
import pandas as pd

from ml.baselines import moving_average_28_day, seasonal_naive_weekly
from ml.data.m5_ca1_foods import select_frozen_scope
from ml.evaluation.metrics import aggregate_metrics, per_series_metrics, wape_percent


def test_frozen_scope_filtering_returns_expected_scope() -> None:
    protocol = {
        "store_id": "CA_1",
        "category_id": "FOODS",
        "departments": ["FOODS_1", "FOODS_2"],
        "expected_item_store_series": 2,
    }
    metadata = pd.DataFrame(
        {
            "item_id": ["item_a", "item_b", "item_c", "item_d"],
            "dept_id": ["FOODS_1", "FOODS_2", "FOODS_3", "FOODS_1"],
            "cat_id": ["FOODS", "FOODS", "FOODS", "HOBBIES"],
            "store_id": ["CA_1", "CA_1", "CA_1", "CA_1"],
        }
    )

    selected = select_frozen_scope(metadata, protocol)

    assert selected["item_id"].tolist() == ["item_a", "item_b"]


def test_seasonal_naive_shape_and_fixed_origin_leakage_safety() -> None:
    train = np.array([list(range(1, 15)), list(range(21, 35))], dtype=float)
    forecast = seasonal_naive_weekly(train, horizon_days=28)
    changed_validation_actuals = np.full((2, 28), 9999.0)

    assert forecast.shape == (2, 28)
    assert np.array_equal(forecast[0], np.tile(train[0, -7:], 4))
    assert np.array_equal(forecast, seasonal_naive_weekly(train, horizon_days=changed_validation_actuals.shape[1]))


def test_moving_average_shape_and_value() -> None:
    train = np.vstack([np.arange(1, 29), np.arange(29, 57)]).astype(float)

    forecast = moving_average_28_day(train, horizon_days=28)

    assert forecast.shape == (2, 28)
    assert np.allclose(forecast[0], np.mean(train[0]))
    assert np.allclose(forecast[1], np.mean(train[1]))


def test_metrics_on_known_arrays_and_undefined_per_sku_wape() -> None:
    actual = np.array([[1.0, 3.0], [0.0, 0.0]])
    forecast = np.array([[2.0, 1.0], [1.0, 1.0]])

    aggregate = aggregate_metrics(actual, forecast)
    per_sku = per_series_metrics(actual, forecast, ["item_a", "item_b"])

    assert aggregate["MAE"] == 1.25
    assert np.isclose(aggregate["RMSE"], np.sqrt(1.75))
    assert aggregate["WAPE_percent"] == 125.0
    assert np.isnan(per_sku.loc[1, "WAPE_percent"])
    assert np.isnan(wape_percent(np.zeros(2), np.ones(2)))
