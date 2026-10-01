"""Validation-only helpers for the frozen inventory simulation protocol.

These helpers load configuration metadata only. They never read M5 sales,
load a model artifact, forecast demand, or execute an inventory simulation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    """Load one version-controlled YAML configuration."""
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Configuration at {path} must be a mapping.")
    return data


def validate_inventory_protocol(
    simulation: dict[str, Any], comparison: dict[str, Any], selection: dict[str, Any]
) -> None:
    """Validate frozen P11 policy controls without accessing data or models."""
    if simulation.get("status") != "DONE":
        raise ValueError("Inventory simulation protocol is not frozen.")
    if simulation.get("lead_time_days", 0) <= 0:
        raise ValueError("lead_time_days must be positive.")
    if simulation.get("review_period_days", 0) <= 0:
        raise ValueError("review_period_days must be positive.")
    if simulation.get("safety_stock", {}).get("service_factor_z", 0) <= 0:
        raise ValueError("Safety-stock service factor must be positive.")
    if simulation.get("test_isolation", {}).get("test_sales_access") != "sealed":
        raise ValueError("TEST sales access must remain sealed.")
    if simulation.get("demand_replay", {}).get("simulated_stockout_updates_forecasting_history"):
        raise ValueError("Simulated stockouts must not modify forecasting history.")

    policies = comparison.get("policies", {})
    baseline = policies.get("MIN_STOCK_MA28", {})
    forecast = policies.get("FORECAST_REORDER_XGBOOST_V1", {})
    if comparison.get("only_intended_difference") != "demand_estimation_source":
        raise ValueError("Policy comparison must vary only demand estimation.")
    if baseline.get("demand_estimation_source") != "trailing_28_day_observed_demand_mean":
        raise ValueError("Baseline must use the frozen trailing 28-day mean.")
    if forecast.get("selected_model") != selection.get("selected_model"):
        raise ValueError("Forecast policy model does not match selected model.")
    if forecast.get("selected_feature_set") != selection.get("selected_feature_set"):
        raise ValueError("Forecast policy feature set does not match selection.")
    if forecast.get("feature_count") != selection.get("feature_count"):
        raise ValueError("Forecast policy feature count does not match selection.")
    if forecast.get("selected_variant") != selection.get("selected_variant"):
        raise ValueError("Forecast policy variant does not match selection.")

    shared = comparison.get("shared_controls", {})
    for control in ("initial_inventory", "realized_demand_replay", "safety_stock_formula", "lost_sales_rule"):
        if shared.get(control) not in {"identical", "identical_exogenous_m5_sales_proxy"}:
            raise ValueError(f"Shared control {control} must be identical between policies.")


def load_and_validate_inventory_protocol(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Load and validate the P11 configuration files from a repository root."""
    simulation = load_yaml(root / "configs/inventory/inventory_simulation_v1.yaml")
    comparison = load_yaml(root / "configs/inventory/inventory_policy_comparison_v1.yaml")
    selection = load_yaml(root / "configs/models/selected_forecasting_model.yaml")
    validate_inventory_protocol(simulation, comparison, selection)
    return simulation, comparison, selection
