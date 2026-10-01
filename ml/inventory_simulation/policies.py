"""Frozen P11 reorder formulas, independent from the simulation engine."""

from __future__ import annotations

import numpy as np

from ml.inventory_simulation.models import PolicyDecision


def safety_stock(history: np.ndarray, lead_time_days: int, z_value: float) -> np.ndarray:
    """Population-std safety stock from the last 28 observed demand days."""
    values = np.asarray(history, dtype=float)
    if values.ndim != 2 or values.shape[1] < 28:
        raise ValueError("Safety stock requires at least 28 observed demand days per SKU.")
    return z_value * np.std(values[:, -28:], axis=1, ddof=0) * np.sqrt(lead_time_days)


def _order_decision(
    inventory_position: np.ndarray, reorder_point: np.ndarray, target_stock: np.ndarray
) -> PolicyDecision:
    trigger = inventory_position <= reorder_point
    order_quantity = np.where(trigger, np.ceil(np.maximum(0.0, target_stock - inventory_position)), 0.0)
    return PolicyDecision(reorder_point=reorder_point, target_stock=target_stock, order_quantity=order_quantity)


def min_stock_ma28_decision(
    observed_history: np.ndarray, inventory_position: np.ndarray, lead_time_days: int,
    review_period_days: int, z_value: float,
) -> PolicyDecision:
    """MIN_STOCK_MA28: trailing observed-demand mean plus common safety stock."""
    values = np.asarray(observed_history, dtype=float)
    estimate = np.mean(values[:, -28:], axis=1)
    stock = safety_stock(values, lead_time_days, z_value)
    reorder_point = estimate * lead_time_days + stock
    target_stock = estimate * (lead_time_days + review_period_days) + stock
    return _order_decision(np.asarray(inventory_position, dtype=float), reorder_point, target_stock)


def forecast_reorder_decision(
    observed_history: np.ndarray, future_forecast: np.ndarray, inventory_position: np.ndarray,
    lead_time_days: int, review_period_days: int, z_value: float,
) -> PolicyDecision:
    """FORECAST_REORDER_XGBOOST_V1 using forecast days 1..7 and 1..8."""
    forecast = np.asarray(future_forecast, dtype=float)
    if forecast.ndim != 2 or forecast.shape[1] < lead_time_days + review_period_days:
        raise ValueError("Forecast policy requires lead-time plus review-period forecast days.")
    if not np.isfinite(forecast).all() or (forecast < 0).any():
        raise ValueError("Forecast policy requires finite nonnegative forecasts.")
    stock = safety_stock(observed_history, lead_time_days, z_value)
    reorder_point = forecast[:, :lead_time_days].sum(axis=1) + stock
    target_stock = forecast[:, : lead_time_days + review_period_days].sum(axis=1) + stock
    return _order_decision(np.asarray(inventory_position, dtype=float), reorder_point, target_stock)
