"""Reusable initial XGBoost global forecasting model utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xgboost as xgb
import yaml

from ml.models.lightgbm_model import CATEGORICAL_FEATURES


CategoricalSchema = dict[str, list[int]]


def load_model_config(config_path: str | Path) -> dict[str, Any]:
    """Load and validate the fixed initial XGBOOST_V1 configuration."""
    with Path(config_path).open(encoding="utf-8") as file:
        config = yaml.safe_load(file)
    expected = {
        "model_name": "XGBOOST_V1", "feature_set": "FEATURE_SET_V1",
        "objective": "count:poisson", "tree_method": "hist", "n_estimators": 400,
        "learning_rate": 0.05, "max_depth": 8, "min_child_weight": 10,
        "subsample": 1.0, "colsample_bytree": 1.0, "reg_alpha": 0.0,
        "reg_lambda": 1.0, "random_state": 42, "n_jobs": -1,
    }
    if not isinstance(config, dict):
        raise ValueError("XGBoost configuration must be a YAML mapping.")
    for key, value in expected.items():
        if config.get(key) != value:
            raise ValueError(f"XGBOOST_V1 requires {key}={value!r}.")
    return config


def build_categorical_schema(
    features: pd.DataFrame, extra_levels: dict[str, list[int]] | None = None
) -> CategoricalSchema:
    """Freeze categorical code levels for consistent train/inference dtypes."""
    missing = set(CATEGORICAL_FEATURES).difference(features.columns)
    if missing:
        raise ValueError(f"FEATURE_SET_V1 is missing categorical model features: {sorted(missing)}")
    extra_levels = extra_levels or {}
    schema: CategoricalSchema = {}
    for column in CATEGORICAL_FEATURES:
        values = {int(value) for value in features[column].dropna().unique()}
        values.update(int(value) for value in extra_levels.get(column, []))
        schema[column] = sorted(values)
    return schema


def prepare_features(features: pd.DataFrame, schema: CategoricalSchema) -> pd.DataFrame:
    """Use native categorical dtypes while preserving the frozen integer values."""
    result = features.copy()
    for column in CATEGORICAL_FEATURES:
        if column not in result.columns or column not in schema:
            raise ValueError(f"Missing categorical feature/schema entry: {column}")
        original = result[column]
        result[column] = pd.Categorical(original, categories=schema[column])
        if original.notna().any() and result[column].isna().any():
            raise ValueError(f"Unexpected categorical code for {column} at inference.")
    return result


def create_model(config: dict[str, Any]) -> xgb.XGBRegressor:
    """Create the CPU-only initial XGBoost regressor without stochastic sampling."""
    return xgb.XGBRegressor(
        objective=config["objective"], tree_method=config["tree_method"],
        n_estimators=config["n_estimators"], learning_rate=config["learning_rate"],
        max_depth=config["max_depth"], min_child_weight=config["min_child_weight"],
        subsample=config["subsample"], colsample_bytree=config["colsample_bytree"],
        reg_alpha=config["reg_alpha"], reg_lambda=config["reg_lambda"],
        random_state=config["random_state"], n_jobs=config["n_jobs"],
        enable_categorical=True, verbosity=0,
    )


def fit_global_model(
    features: pd.DataFrame, target: pd.Series | np.ndarray, config: dict[str, Any],
    extra_category_levels: dict[str, list[int]] | None = None,
) -> tuple[xgb.XGBRegressor, CategoricalSchema]:
    """Fit exactly one global model on the frozen feature matrix."""
    schema = build_categorical_schema(features, extra_category_levels)
    model = create_model(config)
    model.fit(prepare_features(features, schema), target)
    return model, schema


def predict_checked(model: xgb.XGBRegressor, features: pd.DataFrame, schema: CategoricalSchema) -> np.ndarray:
    """Predict continuous nonnegative demand and fail loudly on invalid output."""
    predictions = np.asarray(model.predict(prepare_features(features, schema)), dtype=np.float64)
    if not np.isfinite(predictions).all():
        raise ValueError("XGBoost produced non-finite predictions.")
    if (predictions < 0).any():
        raise ValueError("XGBoost produced negative predictions; investigate before clipping.")
    return predictions


def load_saved_model(config: dict[str, Any], model_path: str | Path) -> xgb.XGBRegressor:
    """Reload the JSON artifact while retaining the native categorical capability."""
    model = create_model(config)
    model.load_model(Path(model_path))
    return model
