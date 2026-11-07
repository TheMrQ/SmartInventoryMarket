from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import yaml

from ml.evaluation.metrics import aggregate_metrics
from ml.models.intermittent import classify_intermittent, croston_rate, intermittent_forecast, sba_rate, tsb_rate
from scripts.ml.run_hybrid_intermittent_research import _summary, hybrid_forecast, validate_research_config


def test_zero_rate_regime_is_deterministic_and_uses_final_history_window_only() -> None:
    history = np.ones((2, 60), dtype=float)
    history[0, -56:] = 0
    history[1, -56:-15] = 0
    result = classify_intermittent(history, 0.75)
    assert result.tolist() == [True, False]
    changed_prefix = history.copy()
    changed_prefix[:, :4] = 0
    assert classify_intermittent(changed_prefix, 0.75).tolist() == result.tolist()


def test_croston_and_sba_update_math_is_explicit() -> None:
    history = np.array([[3.0, 0.0, 0.0, 3.0]])
    # The second demand arrives after three days: size remains 3, while the
    # smoothed interval becomes 1 + 0.1 * (3 - 1) = 1.2.
    assert croston_rate(history, 0.1)[0] == pytest.approx(2.5)
    assert sba_rate(history, 0.1)[0] == pytest.approx(2.375)


def test_tsb_all_zero_and_single_demand_histories_are_nonnegative() -> None:
    history = np.array([[0.0, 0.0, 0.0], [0.0, 5.0, 0.0]])
    rates = tsb_rate(history, 0.1, 0.1)
    assert rates[0] == 0
    # Occurrence probability rises to 0.1 on the sale, then decays to 0.09.
    assert rates[1] == pytest.approx(0.09 * 5.0)
    forecast = intermittent_forecast(history, "TSB", 28, alpha_probability=0.1, alpha_size=0.1)
    assert forecast.shape == (2, 28)
    assert (forecast >= 0).all()


def test_hybrid_routes_only_selected_series_and_keeps_v1_elsewhere() -> None:
    history = np.ones((2, 56), dtype=float)
    history[0] = 0
    v1 = np.full((2, 28), 2.0)
    candidate = {"name": "TEST", "method": "SBA", "zero_rate_threshold": 0.75, "alpha": 0.1}
    forecast, mask = hybrid_forecast(v1, history, candidate, 28)
    assert mask.tolist() == [True, False]
    assert np.all(forecast[0] == 0)
    assert np.all(forecast[1] == 2)


def test_hybrid_metrics_are_standard_nonnegative_demand_metrics() -> None:
    values = aggregate_metrics(np.array([[0.0, 2.0]]), np.array([[0.0, 1.0]]))
    assert values == {"MAE": 0.5, "RMSE": pytest.approx(np.sqrt(0.5)), "WAPE_percent": 50.0}


def test_hybrid_config_preserves_exact_pretest_folds() -> None:
    with open("configs/experiments/hybrid_intermittent_research.yaml", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    validate_research_config(config)
    assert config["stage_1"]["folds"] == ["fold_2", "fold_4"]


def test_hybrid_rejects_invalid_routing_shape() -> None:
    history = np.zeros((1, 56))
    candidate = {"name": "TEST", "method": "SBA", "zero_rate_threshold": 0.75, "alpha": 0.1}
    with pytest.raises(ValueError, match="matching"):
        hybrid_forecast(np.zeros((1, 27)), history, candidate, 28)


def test_hybrid_summary_aligns_fold_metrics_by_name_not_record_order() -> None:
    metrics = pd.DataFrame([
        {"candidate": "XGBOOST_V1_ROLLING_RETRAINED", "feature_set": "FEATURE_SET_V1", "stage": "baseline", "fold": fold, "MAE": 1, "RMSE": 1, "WAPE_percent": 10, "training_seconds": 1, "prediction_seconds": 1, "model_size_MiB": 1}
        for fold in ["fold_1", "fold_2", "fold_3", "fold_4"]
    ] + [
        {"candidate": "HYBRID", "feature_set": "HYBRID_V1_INTERMITTENT", "stage": "stage_2", "fold": fold, "MAE": 1, "RMSE": 1, "WAPE_percent": 9, "training_seconds": 1, "prediction_seconds": 1, "model_size_MiB": 1}
        for fold in ["fold_2", "fold_4", "fold_1", "fold_3"]
    ])
    result = _summary(metrics, "XGBOOST_V1_ROLLING_RETRAINED")
    assert result.loc[result["candidate"].eq("HYBRID"), "wape_folds_improved_vs_v1"].item() == 4
