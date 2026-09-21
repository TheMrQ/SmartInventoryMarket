from __future__ import annotations

import numpy as np
import pandas as pd

from ml.evaluation.forecast_analysis import compare_candidate_to_references, horizon_metrics
from ml.models.lightgbm_model import CATEGORICAL_FEATURES
from ml.models.xgboost_model import (
    fit_global_model, load_model_config, load_saved_model, predict_checked,
)


def _config() -> dict[str, object]:
    return {
        "objective": "count:poisson", "tree_method": "hist", "n_estimators": 5,
        "learning_rate": 0.05, "max_depth": 3, "min_child_weight": 1,
        "subsample": 1.0, "colsample_bytree": 1.0, "reg_alpha": 0.0,
        "reg_lambda": 1.0, "random_state": 42, "n_jobs": 1,
    }


def _features(rows: int = 128) -> pd.DataFrame:
    frame = pd.DataFrame({column: np.arange(rows, dtype=np.int16) % 4 for column in CATEGORICAL_FEATURES})
    frame["lag_1"] = np.arange(rows, dtype=float) % 6
    frame["last_known_sell_price"] = np.where(np.arange(rows) % 5 == 0, np.nan, 2.5)
    return frame


def test_xgboost_wrapper_fits_predicts_and_reloads_native_categorical_json(tmp_path) -> None:
    features = _features()
    model, schema = fit_global_model(features, np.arange(len(features)) % 7, _config())
    prediction = predict_checked(model, features.iloc[:4], schema)
    model_path = tmp_path / "xgboost_v1.json"
    model.save_model(model_path)
    reloaded = load_saved_model(_config(), model_path)

    assert prediction.shape == (4,)
    assert np.isfinite(prediction).all() and (prediction >= 0).all()
    assert np.allclose(prediction, predict_checked(reloaded, features.iloc[:4], schema))


def test_xgboost_config_and_four_method_comparison() -> None:
    config = load_model_config("configs/models/xgboost_v1.yaml")
    metrics = pd.DataFrame({
        "Method": ["28-day Moving Average", "LIGHTGBM_V1", "XGBOOST_V1"],
        "MAE": [2.0, 1.5, 1.0], "RMSE": [3.0, 2.0, 1.0], "WAPE_percent": [50.0, 40.0, 25.0],
    })
    compared = compare_candidate_to_references(metrics, "XGBOOST_V1", ("28-day Moving Average", "LIGHTGBM_V1"))

    assert config["model_name"] == "XGBOOST_V1"
    assert compared.loc[2, "MAE_improvement_pct_vs_28_day_moving_average"] == 50.0
    assert compared.loc[2, "MAE_improvement_pct_vs_lightgbm_v1"] == (1.5 - 1.0) / 1.5 * 100


def test_xgboost_wrapper_supports_a_frozen_categorical_feature_subset() -> None:
    features = _features().loc[:, ["lag_1", "item_code", "dept_code"]]
    model, schema = fit_global_model(features, np.arange(len(features)) % 5, _config())

    assert set(schema) == {"item_code", "dept_code"}
    assert predict_checked(model, features.iloc[:2], schema).shape == (2,)


def test_horizon_metrics_support_xgboost_validation_shape() -> None:
    actual = np.tile(np.array([[1.0, 2.0]]), (2, 1))
    forecast = np.tile(np.array([[1.0, 1.0]]), (2, 1))
    result = horizon_metrics(actual, forecast, ("2016-01-01", "2016-01-02"))

    assert len(result) == 2
    assert result.loc[0, "MAE"] == 0.0
    assert result.loc[1, "MAE"] == 1.0
