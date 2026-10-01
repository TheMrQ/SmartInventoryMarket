"""Aggregate and per-SKU metrics for frozen inventory-policy comparisons."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ml.inventory_simulation.models import InventorySimulationResult


def policy_metrics(result: InventorySimulationResult, cost_weights: dict[str, float]) -> dict[str, float | int | str]:
    """Calculate pre-registered operational metrics and normalized cost proxy."""
    realized = float(result.realized_demand.sum())
    fulfilled = float(result.fulfilled_units.sum())
    lost = float(result.lost_sales_units.sum())
    holding = float(result.on_hand_unit_days.sum()) * cost_weights["holding"]
    lost_cost = lost * cost_weights["lost_sales"]
    reorder_cost = float(result.reorder_count.sum()) * cost_weights["reorder_event"]
    per_sku_fill = np.full(len(result.realized_demand), np.nan, dtype=float)
    np.divide(result.fulfilled_units, result.realized_demand, out=per_sku_fill, where=result.realized_demand > 0)
    return {
        "policy": result.policy_name,
        "total_realized_demand": realized,
        "fulfilled_units": fulfilled,
        "total_lost_sales_units": lost,
        "stockout_days": int(result.stockout_days.sum()),
        "fill_rate": fulfilled / realized if realized > 0 else float("nan"),
        "average_on_hand_inventory": float(result.on_hand_unit_days.mean() / result.daily_fill_rates.shape[1]),
        "reorder_count": int(result.reorder_count.sum()),
        "total_ordered_quantity": float(result.ordered_quantity.sum()),
        "sku_count_with_any_stockout": int((result.stockout_days > 0).sum()),
        "sku_percentage_with_any_stockout": float((result.stockout_days > 0).mean() * 100),
        "median_per_sku_fill_rate": float(np.nanmedian(per_sku_fill)),
        "holding_inventory_cost_proxy": holding,
        "lost_sales_cost_proxy": lost_cost,
        "order_event_cost_proxy": reorder_cost,
        "normalized_cost_proxy": holding + lost_cost + reorder_cost,
    }


def per_sku_summary(item_ids: tuple[str, ...], baseline: InventorySimulationResult, forecast: InventorySimulationResult) -> pd.DataFrame:
    """Return compact tracked comparison evidence without daily state rows."""
    if baseline.realized_demand.shape != forecast.realized_demand.shape or len(item_ids) != len(baseline.realized_demand):
        raise ValueError("Per-SKU result dimensions do not align.")
    baseline_fill = np.full(len(item_ids), np.nan)
    forecast_fill = np.full(len(item_ids), np.nan)
    np.divide(baseline.fulfilled_units, baseline.realized_demand, out=baseline_fill, where=baseline.realized_demand > 0)
    np.divide(forecast.fulfilled_units, forecast.realized_demand, out=forecast_fill, where=forecast.realized_demand > 0)
    days = baseline.daily_fill_rates.shape[1]
    return pd.DataFrame({
        "sku": item_ids,
        "realized_demand": baseline.realized_demand,
        "baseline_lost_sales": baseline.lost_sales_units,
        "forecast_lost_sales": forecast.lost_sales_units,
        "baseline_fill_rate": baseline_fill,
        "forecast_fill_rate": forecast_fill,
        "baseline_avg_on_hand": baseline.on_hand_unit_days / days,
        "forecast_avg_on_hand": forecast.on_hand_unit_days / days,
        "baseline_reorders": baseline.reorder_count,
        "forecast_reorders": forecast.reorder_count,
    })
