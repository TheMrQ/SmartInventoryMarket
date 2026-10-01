"""Deterministic lost-sales inventory simulation with chronological replay."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from ml.inventory_simulation.models import InventorySimulationResult, PolicyDecision


DecisionFunction = Callable[[np.ndarray, np.ndarray], PolicyDecision]


def initial_on_hand(history: np.ndarray, lead_time_days: int, review_period_days: int, z_value: float) -> np.ndarray:
    """Frozen common initial stock based only on the 28 days before the window."""
    values = np.asarray(history, dtype=float)
    if values.ndim != 2 or values.shape[1] < 28:
        raise ValueError("Initial inventory requires 28 observed demand days.")
    recent = values[:, -28:]
    safety = z_value * np.std(recent, axis=1, ddof=0) * np.sqrt(lead_time_days)
    return np.ceil(np.mean(recent, axis=1) * (lead_time_days + review_period_days) + safety)


def simulate_lost_sales_policy(
    policy_name: str,
    initial_history: np.ndarray,
    realized_demand: np.ndarray,
    lead_time_days: int,
    review_period_days: int,
    z_value: float,
    decision_function: DecisionFunction,
) -> InventorySimulationResult:
    """Run one policy while structurally exposing demand only after each day begins.

    ``decision_function`` is called only after the current day is fulfilled and
    appended to ``observed_history``. It receives no future realized demand.
    """
    history = np.asarray(initial_history, dtype=np.float32).copy()
    demand = np.asarray(realized_demand, dtype=float)
    if history.ndim != 2 or demand.ndim != 2 or history.shape[0] != demand.shape[0]:
        raise ValueError("History and realized demand must align as (SKU, day) matrices.")
    if lead_time_days <= 0 or review_period_days <= 0 or z_value <= 0:
        raise ValueError("Lead time, review period, and safety z must be positive.")
    if not np.isfinite(demand).all() or (demand < 0).any():
        raise ValueError("Realized demand must be finite and nonnegative.")

    series_count, day_count = demand.shape
    on_hand = initial_on_hand(history, lead_time_days, review_period_days, z_value).astype(float)
    on_order = np.zeros(series_count, dtype=float)
    receipts = np.zeros((day_count + lead_time_days + 1, series_count), dtype=float)
    initial_stock = on_hand.copy()

    fulfilled_total = np.zeros(series_count, dtype=float)
    lost_total = np.zeros(series_count, dtype=float)
    stockout_days = np.zeros(series_count, dtype=int)
    on_hand_unit_days = np.zeros(series_count, dtype=float)
    reorder_count = np.zeros(series_count, dtype=int)
    ordered_total = np.zeros(series_count, dtype=float)
    daily_fill_rates = np.full((series_count, day_count), np.nan, dtype=float)

    for day_index in range(day_count):
        received = receipts[day_index]
        on_hand += received
        on_order -= received
        if (on_hand < -1e-9).any() or (on_order < -1e-9).any():
            raise ValueError("Receipt processing violated nonnegative inventory invariants.")
        on_hand = np.maximum(on_hand, 0.0)
        on_order = np.maximum(on_order, 0.0)

        available = on_hand.copy()
        today = demand[:, day_index]
        fulfilled = np.minimum(available, today)
        lost = today - fulfilled
        on_hand = np.maximum(0.0, available - today)
        if not np.allclose(lost, np.maximum(0.0, today - available)):
            raise ValueError("Lost-sales calculation invariant failed.")
        fulfilled_total += fulfilled
        lost_total += lost
        stockout_days += (lost > 0).astype(int)
        on_hand_unit_days += on_hand
        np.divide(fulfilled, today, out=daily_fill_rates[:, day_index], where=today > 0)

        # Only now can this day's realized demand become history for the next decision.
        history = np.concatenate([history, today.astype(np.float32)[:, None]], axis=1)
        inventory_position = on_hand + on_order
        decision = decision_function(history, inventory_position)
        order = np.asarray(decision.order_quantity, dtype=float)
        if order.shape != (series_count,) or not np.isfinite(order).all() or (order < 0).any():
            raise ValueError("Policy returned invalid order quantities.")
        if not np.allclose(order, np.ceil(order)):
            raise ValueError("Physical order quantities must be upward-rounded integer units.")
        on_order += order
        receipts[day_index + lead_time_days] += order
        reorder_count += (order > 0).astype(int)
        ordered_total += order
        if (on_hand < -1e-9).any() or (on_order < -1e-9).any():
            raise ValueError("End-of-day inventory invariant failed.")

    return InventorySimulationResult(
        policy_name=policy_name,
        realized_demand=demand.sum(axis=1),
        fulfilled_units=fulfilled_total,
        lost_sales_units=lost_total,
        stockout_days=stockout_days,
        on_hand_unit_days=on_hand_unit_days,
        reorder_count=reorder_count,
        ordered_quantity=ordered_total,
        final_on_hand=on_hand,
        final_on_order=on_order,
        initial_on_hand=initial_stock,
        initial_on_order=np.zeros(series_count, dtype=float),
        daily_fill_rates=daily_fill_rates,
    )
