from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.features.builder import load_feature_config
from scripts.ml.run_xgboost_v2_research import _error_profile, candidate_config, feature_names, select_candidate


def test_v2_feature_schema_is_separate_and_expanded() -> None:
    config = load_feature_config("configs/features/ml_features_v2.yaml")

    assert config["feature_set"] == "FEATURE_SET_V2"
    assert config["warmup_days"] == 56
    assert len(feature_names(config)) == 34
    assert "lag_56" in feature_names(config)


def test_v2_candidate_config_is_deterministic_and_rejects_unknown_objective() -> None:
    candidate = {
        "name": "SMALL", "objective": "count:poisson", "n_estimators": 5,
        "learning_rate": 0.1, "max_depth": 3, "min_child_weight": 1,
        "subsample": 0.9, "colsample_bytree": 0.8, "reg_alpha": 0.0, "reg_lambda": 1.0,
    }

    assert candidate_config(candidate, 42)["random_state"] == 42
    with pytest.raises(ValueError, match="invalid V2 candidate"):
        candidate_config({**candidate, "objective": "binary:logistic"}, 42)


def test_v2_selection_requires_primary_wape_improvement_and_secondary_non_regression() -> None:
    rows = pd.DataFrame([
        {"candidate": "XGBOOST_V1", "MAE": 1.4, "RMSE": 2.5, "WAPE_percent": 66.0},
        {"candidate": "BETTER_WAPE_WORSE_MAE", "MAE": 1.5, "RMSE": 2.4, "WAPE_percent": 65.0},
        {"candidate": "LOWEST_WAPE", "MAE": 1.3, "RMSE": 2.4, "WAPE_percent": 64.0},
    ])

    best, selected = select_candidate(rows)

    assert best["candidate"] == "LOWEST_WAPE"
    assert selected is True


def test_v1_error_profile_handles_numpy_sales_arrays() -> None:
    actual = np.array([[0.0, 0.0, 2.0, 0.0], [1.0, 1.0, 1.0, 1.0]])
    forecast = np.array([[0.0, 1.0, 1.0, 0.0], [1.0, 2.0, 1.0, 0.0]])
    horizon = pd.DataFrame({"MAE": [0.0, 1.0, 0.5, 0.5]})

    profile, volume = _error_profile(actual, forecast, ("a", "b"), horizon)

    assert profile["intermittent_skus_at_least_75pct_zero"] == 1
    assert profile["zero_total_validation_skus"] == 0
    assert list(volume["volume_band"]) == ["low", "high"]
