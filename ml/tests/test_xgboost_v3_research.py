from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.data.m5_ca1_foods import _rolling_fold_days
from ml.features.builder import _feature_names, _intermittent_feature_arrays, load_feature_config
from ml.models.recursive import recursive_forecast
from scripts.ml.run_xgboost_v3_research import candidate_config, select_candidate, validate_research_config


def test_v3_schema_is_separate_deterministic_and_intermittent_aware() -> None:
    config = load_feature_config("configs/features/ml_features_v3.yaml")

    assert config["feature_set"] == "FEATURE_SET_V3"
    assert len(_feature_names(config)) == 44
    assert "zero_demand_rate_56" in _feature_names(config)
    assert "days_since_last_nonzero_capped_56" in _feature_names(config)
    assert "rolling_mean_trend_7_vs_28" in _feature_names(config)


def test_v3_intermittent_features_are_past_only_and_define_all_zero_windows() -> None:
    config = load_feature_config("configs/features/ml_features_v3.yaml")
    history = np.zeros((1, 60), dtype=float)
    history[0, 4] = 3
    history[0, 30] = 2
    positions = np.array([56], dtype=np.int32)

    features = _intermittent_feature_arrays(history, positions, config)
    mutated = history.copy()
    mutated[0, 56:] = 99
    after = _intermittent_feature_arrays(mutated, positions, config)

    assert features["zero_demand_rate_28"][0, 0] == pytest.approx(27 / 28)
    assert features["nonzero_demand_mean_28"][0, 0] == 2
    assert features["has_nonzero_demand_28"][0, 0] == 1
    assert features["days_since_last_nonzero_capped_56"][0, 0] == 25
    for name in features:
        np.testing.assert_allclose(features[name], after[name])


def test_rolling_fold_boundaries_reject_test_and_noncontiguous_spans() -> None:
    train, validation = _rolling_fold_days("d_1885", "d_1886", "d_1913")
    assert train[-1] == "d_1885" and validation[0] == "d_1886" and len(validation) == 28
    with pytest.raises(ValueError, match="end no later"):
        _rolling_fold_days("d_1913", "d_1914", "d_1941")
    with pytest.raises(ValueError, match="immediately"):
        _rolling_fold_days("d_1801", "d_1803", "d_1830")


def test_v3_candidate_and_selection_rule_are_deterministic() -> None:
    candidate = {"name": "V3", "objective": "count:poisson", "n_estimators": 10, "learning_rate": .1, "max_depth": 4, "min_child_weight": 2, "subsample": .9, "colsample_bytree": .9, "reg_alpha": 0, "reg_lambda": 1}
    assert candidate_config(candidate, 42, "FEATURE_SET_V3")["random_state"] == 42
    with pytest.raises(ValueError, match="invalid V3 candidate"):
        candidate_config({**candidate, "objective": "binary:logistic"}, 42, "FEATURE_SET_V3")
    summary = pd.DataFrame([
        {"candidate": "XGBOOST_V1_ROLLING_RETRAINED", "feature_set": "FEATURE_SET_V1", "folds": 4, "mean_WAPE_percent": 66, "mean_MAE": 1.4, "mean_RMSE": 2.5, "wape_folds_improved_vs_v1": 0},
        {"candidate": "GOOD", "feature_set": "FEATURE_SET_V3", "folds": 4, "mean_WAPE_percent": 65, "mean_MAE": 1.3, "mean_RMSE": 2.4, "wape_folds_improved_vs_v1": 3},
        {"candidate": "ONE_FOLD", "feature_set": "FEATURE_SET_V3", "folds": 4, "mean_WAPE_percent": 64, "mean_MAE": 1.3, "mean_RMSE": 2.4, "wape_folds_improved_vs_v1": 1},
    ])
    winner, assessed = select_candidate(summary, {"minimum_wape_fold_improvements": 3}, "XGBOOST_V1_ROLLING_RETRAINED")
    assert winner == "GOOD"
    assert not assessed.loc[assessed["candidate"].eq("ONE_FOLD"), "credible_by_predeclared_rule"].item()


def test_recursive_forecast_rejects_negative_v3_demand_without_clipping() -> None:
    config = load_feature_config("configs/features/ml_features_v3.yaml")
    metadata = pd.DataFrame({"item_id": ["A"], "dept_id": ["FOODS_1"]})
    calendar = pd.DataFrame({"wday": [1], "month": [1], "year": [2016], "snap_CA": [0], "event_name_1": [None], "event_type_1": [None], "event_name_2": [None], "event_type_2": [None]})
    from ml.features.builder import build_encodings
    encodings = build_encodings(metadata, calendar)
    with pytest.raises(ValueError, match="negative"):
        recursive_forecast(lambda _: np.array([-1.0]), np.zeros((1, 56)), np.full((1, 56), np.nan), calendar, metadata, encodings, config, _feature_names(config))


def test_research_config_keeps_exact_pretest_folds() -> None:
    import yaml
    with open("configs/experiments/xgboost_v3_research.yaml", encoding="utf-8") as handle:
        validate_research_config(yaml.safe_load(handle))
