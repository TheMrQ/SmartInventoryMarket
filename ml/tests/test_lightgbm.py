from __future__ import annotations

import numpy as np
import pandas as pd

from ml.evaluation.forecast_analysis import compare_to_moving_average, horizon_metrics
from ml.features.builder import build_encodings
from ml.models.lightgbm_model import CATEGORICAL_FEATURES, fit_global_model, predict_checked
from ml.models.recursive import recursive_forecast


def _feature_config() -> dict[str, object]:
    return {
        "sales_lags": [1, 7, 14, 28],
        "rolling_mean_windows": [7, 14, 28],
        "rolling_std_windows": [7, 28],
        "warmup_days": 28,
        "price_features": ["last_known_sell_price", "price_lag_7", "price_change_from_7_days_ago", "price_available", "price_missing"],
    }


def _calendar(days: int) -> pd.DataFrame:
    return pd.DataFrame({
        "wday": (np.arange(days) % 7) + 1, "month": 1, "year": 2011, "snap_CA": 0,
        "event_name_1": [None] * days, "event_type_1": [None] * days,
        "event_name_2": [None] * days, "event_type_2": [None] * days,
    })


def test_lightgbm_wrapper_fits_and_predicts_synthetic_nonnegative_target() -> None:
    features = pd.DataFrame({column: np.arange(120, dtype=np.int16) % 4 for column in CATEGORICAL_FEATURES})
    features["lag_1"] = np.arange(120, dtype=float) % 5
    config = {"objective": "poisson", "boosting_type": "gbdt", "n_estimators": 5, "learning_rate": 0.05, "num_leaves": 31, "max_depth": -1, "min_child_samples": 100, "reg_alpha": 0.0, "reg_lambda": 0.1, "random_state": 42, "n_jobs": 1, "deterministic": True, "force_col_wise": True}

    model, categorical = fit_global_model(features, np.arange(120) % 6, config)
    prediction = predict_checked(model, features.iloc[:3])

    assert categorical == CATEGORICAL_FEATURES
    assert prediction.shape == (3,)
    assert np.isfinite(prediction).all() and (prediction >= 0).all()


def test_recursive_forecast_uses_predictions_not_unavailable_actuals() -> None:
    metadata = pd.DataFrame({"item_id": ["item_a", "item_b"], "dept_id": ["FOODS_1", "FOODS_2"]})
    calendar = _calendar(28)
    encodings = build_encodings(metadata, calendar)
    feature_names = [
        "lag_1", "lag_7", "lag_14", "lag_28", "rolling_mean_7", "rolling_mean_14", "rolling_mean_28", "rolling_std_7", "rolling_std_28",
        "wday", "month", "year", "is_weekend", "snap_CA", "event_name_1_code", "event_type_1_code", "event_name_2_code", "event_type_2_code",
        "item_code", "dept_code", "last_known_sell_price", "price_lag_7", "price_change_from_7_days_ago", "price_available", "price_missing",
    ]
    history_sales = np.zeros((2, 28), dtype=float)
    history_prices = np.ones((2, 28), dtype=float)

    forecast = recursive_forecast(lambda frame: frame["lag_1"].to_numpy() + 1, history_sales, history_prices, calendar, metadata, encodings, _feature_config(), feature_names)

    assert forecast.shape == (2, 28)
    assert np.array_equal(forecast[0], np.arange(1, 29))


def test_comparison_improvement_and_horizon_metrics() -> None:
    metrics = pd.DataFrame({"Method": ["28-day Moving Average", "LIGHTGBM_V1"], "MAE": [2.0, 1.0], "RMSE": [3.0, 1.5], "WAPE_percent": [50.0, 25.0]})
    compared = compare_to_moving_average(metrics)
    horizon = horizon_metrics(np.array([[1.0, 2.0], [3.0, 4.0]]), np.array([[1.0, 1.0], [3.0, 5.0]]), ("2016-01-01", "2016-01-02"))

    assert compared.loc[1, "MAE_improvement_pct_vs_moving_average"] == 50.0
    assert len(horizon) == 2
    assert horizon.loc[0, "MAE"] == 0.0
    assert horizon.loc[1, "MAE"] == 1.0
