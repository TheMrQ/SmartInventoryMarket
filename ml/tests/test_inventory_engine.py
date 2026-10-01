import numpy as np

from ml.inventory_simulation.engine import initial_on_hand, simulate_lost_sales_policy
from ml.inventory_simulation.metrics import policy_metrics
from ml.inventory_simulation.policies import forecast_reorder_decision, min_stock_ma28_decision


def _history(series=1):
    return np.full((series, 28), 2.0)


def test_initial_inventory_uses_frozen_eight_day_target_and_common_state():
    first = initial_on_hand(_history(2), 7, 1, 1.645)
    second = initial_on_hand(_history(2), 7, 1, 1.645)
    assert np.array_equal(first, second)
    assert np.array_equal(first, np.array([16.0, 16.0]))


def test_min_stock_policy_reorder_trigger_and_upward_rounding():
    decision = min_stock_ma28_decision(_history(), np.array([14.0]), 7, 1, 1.645)
    assert decision.order_quantity[0] == 2.0
    no_order = min_stock_ma28_decision(_history(), np.array([17.0]), 7, 1, 1.645)
    assert no_order.order_quantity[0] == 0.0


def test_forecast_policy_uses_seven_day_reorder_and_eight_day_target():
    forecast = np.full((1, 8), 3.0)
    decision = forecast_reorder_decision(_history(), forecast, np.array([20.0]), 7, 1, 1.645)
    assert decision.reorder_point[0] == 21.0
    assert decision.target_stock[0] == 24.0
    assert decision.order_quantity[0] == 4.0


def test_lost_sales_nonnegative_inventory_and_metrics():
    def no_order(history, position):
        return min_stock_ma28_decision(history, np.full_like(position, 1_000.0), 7, 1, 1.645)

    result = simulate_lost_sales_policy("TEST", _history(), np.array([[20.0, 1.0]]), 7, 1, 1.645, no_order)
    assert result.lost_sales_units[0] == 5.0
    assert result.fulfilled_units[0] == 16.0
    assert result.final_on_hand[0] == 0.0
    assert result.stockout_days[0] == 2
    metrics = policy_metrics(result, {"holding": 1.0, "lost_sales": 5.0, "reorder_event": 1.0})
    assert metrics["fill_rate"] == 16 / 21
    assert metrics["normalized_cost_proxy"] >= 25.0


def test_receipt_arrives_after_exactly_seven_days_and_updates_on_order():
    calls = []

    def one_order_then_none(history, position):
        calls.append(len(calls))
        order = np.array([10.0 if len(calls) == 1 else 0.0])
        from ml.inventory_simulation.models import PolicyDecision
        return PolicyDecision(np.zeros(1), np.zeros(1), order)

    result = simulate_lost_sales_policy("TEST", _history(), np.zeros((1, 8)), 7, 1, 1.645, one_order_then_none)
    assert result.final_on_hand[0] == 26.0
    assert result.final_on_order[0] == 0.0
    assert result.reorder_count[0] == 1


def test_current_day_becomes_history_only_after_realization_and_future_demand_is_not_exposed():
    observed_lengths = []
    observed_last_values = []

    def inspect(history, position):
        observed_lengths.append(history.shape[1])
        observed_last_values.append(float(history[0, -1]))
        return min_stock_ma28_decision(history, np.full_like(position, 1_000.0), 7, 1, 1.645)

    simulate_lost_sales_policy("TEST", _history(), np.array([[5.0, 9.0]]), 7, 1, 1.645, inspect)
    assert observed_lengths == [29, 30]
    assert observed_last_values == [5.0, 9.0]


def test_simulation_is_deterministic_for_identical_inputs():
    def policy(history, position):
        return min_stock_ma28_decision(history, position, 7, 1, 1.645)

    demand = np.array([[1.0, 4.0, 2.0], [3.0, 0.0, 5.0]])
    first = simulate_lost_sales_policy("A", _history(2), demand, 7, 1, 1.645, policy)
    second = simulate_lost_sales_policy("A", _history(2), demand, 7, 1, 1.645, policy)
    assert np.array_equal(first.lost_sales_units, second.lost_sales_units)
    assert np.array_equal(first.ordered_quantity, second.ordered_quantity)
