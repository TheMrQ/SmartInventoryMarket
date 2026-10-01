from copy import deepcopy
from pathlib import Path

import pytest

from ml.inventory_simulation.protocol import load_and_validate_inventory_protocol, validate_inventory_protocol


ROOT = Path(__file__).resolve().parents[2]


def test_frozen_inventory_protocol_matches_selected_forecasting_model():
    simulation, comparison, selection = load_and_validate_inventory_protocol(ROOT)

    assert simulation["lead_time_days"] == 7
    assert simulation["review_period_days"] == 1
    assert simulation["safety_stock"]["service_factor_z"] == 1.645
    assert simulation["test_isolation"]["test_sales_access"] == "sealed"
    assert comparison["policies"]["FORECAST_REORDER_XGBOOST_V1"]["selected_model"] == "XGBOOST_V1"
    assert selection["feature_count"] == 25


def test_inventory_protocol_rejects_a_nonpositive_lead_time():
    simulation, comparison, selection = load_and_validate_inventory_protocol(ROOT)
    invalid = deepcopy(simulation)
    invalid["lead_time_days"] = 0

    with pytest.raises(ValueError, match="lead_time_days"):
        validate_inventory_protocol(invalid, comparison, selection)


def test_inventory_protocol_rejects_a_forecast_policy_pointer_mismatch():
    simulation, comparison, selection = load_and_validate_inventory_protocol(ROOT)
    invalid = deepcopy(comparison)
    invalid["policies"]["FORECAST_REORDER_XGBOOST_V1"]["selected_feature_set"] = "OTHER_FEATURES"

    with pytest.raises(ValueError, match="feature set"):
        validate_inventory_protocol(simulation, invalid, selection)
