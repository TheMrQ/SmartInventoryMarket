"""Recursive validation inference that never accepts validation actual sales."""

from __future__ import annotations

from typing import Any, Callable

import numpy as np
import pandas as pd

from ml.features.builder import FeatureEncodings, build_single_step_inference_features


def recursive_forecast(
    predict: Callable[[pd.DataFrame], np.ndarray],
    history_sales: np.ndarray,
    history_prices: np.ndarray,
    validation_calendar: pd.DataFrame,
    metadata: pd.DataFrame,
    encodings: FeatureEncodings,
    feature_config: dict[str, Any],
    feature_names: list[str] | tuple[str, ...],
) -> np.ndarray:
    """Predict every validation step from explicit history and prior predictions.

    ``validation_actuals`` is deliberately absent from this API. Unknown future
    price observations are appended as NaN, retaining the frozen past-only policy.
    """
    sales_state = np.asarray(history_sales, dtype=np.float32).copy()
    price_state = np.asarray(history_prices, dtype=np.float32).copy()
    forecasts: list[np.ndarray] = []
    for _, calendar_row in validation_calendar.iterrows():
        features = build_single_step_inference_features(
            sales_state, price_state, calendar_row.to_frame().T, metadata, encodings, feature_config
        )
        features = features.loc[:, list(feature_names)]
        prediction = np.asarray(predict(features), dtype=np.float64)
        if prediction.shape != (len(metadata),):
            raise ValueError("Recursive prediction must provide one value per SKU.")
        if not np.isfinite(prediction).all() or (prediction < 0).any():
            raise ValueError("Recursive prediction contains non-finite or negative demand.")
        forecasts.append(prediction)
        sales_state = np.concatenate([sales_state, prediction.astype(np.float32)[:, None]], axis=1)
        price_state = np.concatenate(
            [price_state, np.full((price_state.shape[0], 1), np.nan, dtype=np.float32)], axis=1
        )
    return np.column_stack(forecasts)
