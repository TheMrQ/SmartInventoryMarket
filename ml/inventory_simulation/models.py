"""Data structures for the deterministic P12 inventory simulation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PolicyDecision:
    """A vectorized end-of-day replenishment decision."""

    reorder_point: np.ndarray
    target_stock: np.ndarray
    order_quantity: np.ndarray


@dataclass(frozen=True)
class InventorySimulationResult:
    """Per-SKU aggregates for one policy over the fixed replay window."""

    policy_name: str
    realized_demand: np.ndarray
    fulfilled_units: np.ndarray
    lost_sales_units: np.ndarray
    stockout_days: np.ndarray
    on_hand_unit_days: np.ndarray
    reorder_count: np.ndarray
    ordered_quantity: np.ndarray
    final_on_hand: np.ndarray
    final_on_order: np.ndarray
    initial_on_hand: np.ndarray
    initial_on_order: np.ndarray
    daily_fill_rates: np.ndarray
