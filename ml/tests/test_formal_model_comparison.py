from __future__ import annotations

import pandas as pd
import yaml

from scripts.ml.formal_model_comparison import (
    FEATURE_GROUPS, build_feature_group_importance, build_formal_comparison, validate_ablation_config,
)


def test_formal_comparison_uses_existing_metrics_and_resource_metadata() -> None:
    baseline = pd.DataFrame({"Method": ["Seasonal Naive (lag 7)", "28-day Moving Average"], "MAE": [3.0, 2.0], "RMSE": [4.0, 3.0], "WAPE_percent": [60.0, 50.0]})
    lightgbm = pd.DataFrame({"Method": ["LIGHTGBM_V1"], "MAE": [1.8], "RMSE": [2.8], "WAPE_percent": [45.0]})
    xgboost = pd.DataFrame({"Method": ["XGBOOST_V1"], "MAE": [1.5], "RMSE": [2.5], "WAPE_percent": [40.0]})
    manifest = {"training": {"duration_seconds": 10.0, "feature_count": 25}, "model_artifact": {"size_bytes": 1024**2}}
    result = build_formal_comparison(baseline, lightgbm, xgboost, manifest, manifest)

    assert len(result) == 4
    assert result.loc[result["method"] == "XGBOOST_V1", "MAE_improvement_pct_vs_moving_average"].iloc[0] == 25.0
    assert result.loc[result["method"] == "LIGHTGBM_V1", "feature_count"].iloc[0] == 25


def test_feature_groups_and_frozen_ablation_counts_match_actual_feature_names() -> None:
    features = [feature for values in FEATURE_GROUPS.values() for feature in values]
    importance = pd.DataFrame({"feature": features, "normalized_gain_percent": [100 / len(features)] * len(features)})
    groups = build_feature_group_importance(importance, importance)
    with open("configs/experiments/xgboost_feature_ablation_v1.yaml", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    validate_ablation_config(config, set(features))
    assert groups.groupby("model")["normalized_gain_percent"].sum().eq(100).all()
    assert config["variants"]["NO_PRICE"]["expected_feature_count"] == 20
    assert config["variants"]["NO_CALENDAR_EVENT"]["expected_feature_count"] == 16
    assert config["variants"]["DEMAND_PRODUCT_ONLY"]["expected_feature_count"] == 11
