import numpy as np
import pandas as pd
import pytest

from ml.evaluation.forecast_reliability import (
    apply_intervals,
    assert_pretest_folds,
    calibration_table,
    evidence_level,
    physical_interval,
    residuals,
    sparsity_band,
)


def _rows():
    return pd.DataFrame({
        "horizon_day": [1] * 8 + [2] * 8,
        "sparsity_band": ["0-25% zero"] * 4 + ["75-100% zero"] * 4 + ["0-25% zero"] * 8,
        "residual": [-2, -1, 0, 1, -4, -2, 2, 4, -3, -2, -1, 0, 1, 2, 3, 4],
    })


def test_final_test_dates_are_rejected_before_calibration():
    with pytest.raises(ValueError, match="final-TEST"):
        assert_pretest_folds([{"validation_end_d": "d_1914"}])


def test_residual_is_actual_minus_point_forecast():
    np.testing.assert_array_equal(residuals(np.array([[3, 1]]), np.array([[2, 4]])), np.array([[1.0, -3.0]]))


def test_asymmetric_quantiles_and_hierarchy_are_deterministic():
    table = calibration_table(_rows(), [.80], minimum_sample_size=5)
    # Horizon+band has only four rows, so resolution falls back to the 8-row horizon bucket.
    applied = apply_intervals(pd.DataFrame({"horizon_day": [1], "sparsity_band": ["0-25% zero"], "point_forecast": [1.0]}), table, .80)
    assert applied.iloc[0].interval_level == "horizon"
    assert applied.iloc[0].lower_bound == 0.0
    assert applied.iloc[0].upper_bound >= applied.iloc[0].lower_bound


def test_only_final_physical_lower_bound_is_clamped():
    assert physical_interval(1, -4, 3) == (0.0, 4.0)


def test_sparse_bands_and_evidence_labels_are_documented_and_deterministic():
    assert list(sparsity_band(np.array([.25, .5, .75, 1.0]))) == ["0-25% zero", "25-50% zero", "50-75% zero", "75-100% zero"]
    assert evidence_level(.75, 1, 1, 1, 2, 1, 2) == "LIMITED"
    assert evidence_level(.10, .5, .5, 1, 2, 1, 2) == "HIGHER"
    assert evidence_level(.40, 1.5, 1.5, 1, 2, 1, 2) == "MODERATE"
