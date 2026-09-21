from __future__ import annotations

import pandas as pd
import yaml

from scripts.ml.run_xgboost_feature_ablation import _read_full_per_sku, recommend_candidate, select_variant_features
from ml.evaluation.metrics import aggregate_metrics


FULL_FEATURES = [
    "lag_1", "lag_7", "lag_14", "lag_28", "rolling_mean_7", "rolling_mean_14", "rolling_mean_28", "rolling_std_7", "rolling_std_28",
    "wday", "month", "year", "is_weekend", "snap_CA", "event_name_1_code", "event_type_1_code", "event_name_2_code", "event_type_2_code",
    "item_code", "dept_code", "last_known_sell_price", "price_lag_7", "price_change_from_7_days_ago", "price_available", "price_missing",
]


def _plan() -> dict:
    with open("configs/experiments/xgboost_feature_ablation_v1.yaml", encoding="utf-8") as file:
        return yaml.safe_load(file)


def test_frozen_ablation_variants_select_exact_feature_counts() -> None:
    variants = _plan()["variants"]
    selected = {name: select_variant_features(name, definition, FULL_FEATURES) for name, definition in variants.items()}

    assert {name: len(features) for name, features in selected.items()} == {
        "FULL_V1": 25, "NO_PRICE": 20, "NO_CALENDAR_EVENT": 16, "DEMAND_PRODUCT_ONLY": 11,
    }
    assert set(FULL_FEATURES).difference(selected["NO_PRICE"]) == set(variants["NO_PRICE"]["remove_features"])
    assert selected["DEMAND_PRODUCT_ONLY"] == variants["DEMAND_PRODUCT_ONLY"]["keep_features"]


def test_wape_first_candidate_recommendation_uses_secondary_metrics_as_tiebreakers() -> None:
    results = pd.DataFrame({
        "variant": ["FULL_V1", "NO_PRICE", "DEMAND_PRODUCT_ONLY"],
        "WAPE": [66.0, 65.0, 65.0], "MAE": [1.4, 1.5, 1.3], "RMSE": [2.5, 2.6, 2.4],
    })

    assert recommend_candidate(results) == "DEMAND_PRODUCT_ONLY"


def test_existing_full_summary_parser_does_not_include_terminal_punctuation(tmp_path) -> None:
    summary = tmp_path / "summary.md"
    summary.write_text("Per-SKU XGBoost MAE median/mean/p90: 1.0 / 1.2 / 2.5.\nUndefined per-SKU WAPE: 81 of 1437.\n", encoding="utf-8")

    assert _read_full_per_sku(summary) == (1.0, 1.2, 2.5, 81)


def test_shared_metric_wape_percent_is_mapped_to_the_ablation_wape_column() -> None:
    metrics = aggregate_metrics([[1.0]], [[2.0]])
    metrics["WAPE"] = metrics.pop("WAPE_percent")

    assert metrics["WAPE"] == 100.0
