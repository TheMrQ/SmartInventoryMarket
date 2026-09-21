"""Reusable initial LightGBM global forecasting model utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd
import yaml


CATEGORICAL_FEATURES = [
    "item_code",
    "dept_code",
    "wday",
    "month",
    "year",
    "is_weekend",
    "snap_CA",
    "event_name_1_code",
    "event_type_1_code",
    "event_name_2_code",
    "event_type_2_code",
]


def load_model_config(config_path: str | Path) -> dict[str, Any]:
    """Load the intentionally initial, untuned LIGHTGBM_V1 configuration."""
    with Path(config_path).open(encoding="utf-8") as file:
        config = yaml.safe_load(file)
    expected = {
        "model_name": "LIGHTGBM_V1",
        "feature_set": "FEATURE_SET_V1",
        "objective": "poisson",
        "boosting_type": "gbdt",
        "n_estimators": 400,
        "learning_rate": 0.05,
        "num_leaves": 31,
        "max_depth": -1,
        "min_child_samples": 100,
        "reg_alpha": 0.0,
        "reg_lambda": 0.1,
        "random_state": 42,
        "n_jobs": -1,
        "deterministic": True,
        "force_col_wise": True,
    }
    if not isinstance(config, dict):
        raise ValueError("LightGBM configuration must be a YAML mapping.")
    for key, value in expected.items():
        if config.get(key) != value:
            raise ValueError(f"LIGHTGBM_V1 requires {key}={value!r}.")
    return config


def validate_feature_columns(feature_names: list[str] | tuple[str, ...]) -> list[str]:
    """Return categorical columns and reject missing required model inputs."""
    names = list(feature_names)
    missing = set(CATEGORICAL_FEATURES).difference(names)
    if missing:
        raise ValueError(f"FEATURE_SET_V1 is missing categorical model features: {sorted(missing)}")
    return [column for column in CATEGORICAL_FEATURES if column in names]


def create_model(config: dict[str, Any]) -> lgb.LGBMRegressor:
    """Create a CPU-only, deterministic, no-subsampling LightGBM regressor."""
    return lgb.LGBMRegressor(
        objective=config["objective"],
        boosting_type=config["boosting_type"],
        n_estimators=config["n_estimators"],
        learning_rate=config["learning_rate"],
        num_leaves=config["num_leaves"],
        max_depth=config["max_depth"],
        min_child_samples=config["min_child_samples"],
        reg_alpha=config["reg_alpha"],
        reg_lambda=config["reg_lambda"],
        random_state=config["random_state"],
        n_jobs=config["n_jobs"],
        deterministic=config["deterministic"],
        force_col_wise=config["force_col_wise"],
        verbosity=-1,
    )


def fit_global_model(
    features: pd.DataFrame, target: pd.Series | np.ndarray, config: dict[str, Any]
) -> tuple[lgb.LGBMRegressor, list[str]]:
    """Fit exactly one global model using training rows only."""
    categorical_features = validate_feature_columns(list(features.columns))
    model = create_model(config)
    model.fit(features, target, categorical_feature=categorical_features)
    return model, categorical_features


def predict_checked(model: lgb.LGBMRegressor, features: pd.DataFrame) -> np.ndarray:
    """Predict continuous nonnegative demand and fail loudly on invalid output."""
    predictions = np.asarray(model.predict(features), dtype=np.float64)
    if not np.isfinite(predictions).all():
        raise ValueError("LightGBM produced non-finite predictions.")
    if (predictions < 0).any():
        raise ValueError("LightGBM produced negative predictions; investigate before clipping.")
    return predictions
