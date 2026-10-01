# Inventory Simulation Protocol V1

Status: **DONE — CHECKPOINT-011.** P12 may execute this frozen protocol; P11 does not run an inventory simulation.

## Purpose and Scope

This protocol compares a simple historical-demand reorder policy with a forecast-based reorder policy for all 1,437 `CA_1` / `FOODS` M5 SKU series. It is a reproducible decision-support simulation: the output is a reorder recommendation for human approval, not an automatic supplier purchase.

Machine-readable sources are `configs/inventory/inventory_simulation_v1.yaml` and `configs/inventory/inventory_policy_comparison_v1.yaml`.

## Data Limitation

M5 supplies observed retail sales plus price/calendar context; it does not supply reliable Walmart on-hand inventory, purchase orders, replenishment receipts, supplier lead time, lost sales, or stock-out flags. Observed M5 sales are therefore the exogenous realized-demand proxy. A zero sale does not prove zero demand, zero inventory, or a stock-out.

All inventory positions, replenishment timing, lost sales, and costs are simulation outcomes under explicit assumptions. They must never be reported as observed Walmart inventory performance or real Walmart lead-time behavior.

## Frozen State and Event Timing

Each SKU-day tracks `on_hand`, `on_order`, `inventory_position`, `received_today`, `demand_today`, `fulfilled_today`, `lost_sales_today`, and `order_quantity_today`.

`inventory_position = on_hand + on_order`. The protocol uses lost sales rather than backorders, and physical inventory cannot become negative.

Every simulated day follows this sequence:

1. Receive orders due today at the **start of day**.
2. Add receipts to on-hand inventory.
3. Observe the exogenous realized-demand proxy.
4. Fulfill demand up to available on-hand inventory.
5. Record unfulfilled demand as lost sales.
6. Update ending on-hand inventory.
7. Update information known by end of day.
8. Compute the next reorder decision.
9. Create any order with an arrival only after the fixed lead time.

No order arrives earlier than its 7-day lead time. The daily review period is one day.

## Lost-Sales Assumption

For realized demand `D` and on-hand stock `H` before fulfillment:

```text
fulfilled_demand = min(H, D)
lost_sales       = max(0, D - H)
ending_on_hand   = max(0, H - D)
```

This represents a supermarket setting where an unavailable grocery item does not create an individual backorder. It is a modeling assumption, not an observed M5 property.

## Lead Time, Safety Stock, and Initial Inventory

- **Lead time:** fixed deterministic 7 days; this is a transparent simulation assumption, not a claim about Walmart.
- **Review period:** 1 day.
- **Safety stock:** `1.645 * population_std(previous 28 observed demand days) * sqrt(7)`.
- **Service factor:** `z = 1.645`, an approximately one-sided 95% normal-service proxy. Demand is not claimed to be normally distributed.
- **Initial on-hand:** `ceil(historical_daily_mean_28 * (7 + 1) + initial_safety_stock)`.
- **Initial on-order:** 0.

The safety-stock and initialization histories use only demand known before the decision/simulation window. Both policies begin with precisely the same simulated state.

## Policies

### MIN_STOCK_MA28

This baseline does not use ML forecasts. It uses `historical_daily_demand_estimate = mean(previous 28 observed demand days)`.

```text
expected_lead_time_demand = historical_daily_demand_estimate * 7
reorder_point             = expected_lead_time_demand + safety_stock
target_stock              = historical_daily_demand_estimate * (7 + 1) + safety_stock
```

When `inventory_position <= reorder_point`, order `ceil(max(0, target_stock - inventory_position))`; otherwise order zero.

### FORECAST_REORDER_XGBOOST_V1

This policy uses validation-selected `XGBOOST_V1` + `FEATURE_SET_V1` / `FULL_V1` (25 features). At a decision date it may use only sales/features already known on that date and recursively forecasts forward.

```text
expected_lead_time_demand = sum(forecast days 1..7)
target_demand             = sum(forecast days 1..8)
reorder_point             = expected_lead_time_demand + safety_stock
target_stock              = target_demand + safety_stock
```

The reorder trigger and upward integer rounding are identical to the baseline policy.

## Fairness and Demand Replay Controls

Both policies use the same SKU universe, simulated initial inventory, realized M5 demand replay, lead time, safety-stock formula, review cadence, receipt timing, lost-sales rule, inventory-position formula, and order rounding. The **only intended difference is the demand-estimation source**: a trailing 28-day observed mean versus an XGBoost recursive forecast.

Hypothetical stock-outs under either policy must not alter the M5 sales history used by the forecasting policy. Feeding synthetic lost sales back into demand history would create policy-dependent demand paths and obscure the policy comparison. This also means the study cannot recover latent demand censored by real historical stock-outs.

## Metrics

Primary operational metrics, frozen before execution, are:

1. total lost-sales units;
2. stockout days;
3. fill rate (`fulfilled_units / realized_demand_units` when the denominator is positive);
4. average on-hand inventory;
5. reorder count; and
6. total ordered quantity.

P12 must additionally report the number and percentage of SKUs with any stock-out, median per-SKU fill rate, and useful inventory distributions. Zero-demand cases must be visible rather than hidden.

### Secondary Normalized Cost Proxy

The protocol retains a secondary **normalized cost proxy**, not USD or supermarket accounting cost:

```text
holding_inventory_cost = 1.0 * unit-days on hand
lost_sales_cost        = 5.0 * lost units
order_event_cost       = 1.0 * reorder events
cost_proxy             = holding_inventory_cost + lost_sales_cost + order_event_cost
```

Physical inventory metrics remain primary. The coefficients are frozen before TEST and must not be tuned after seeing results.

## Forecasting Boundaries and TEST Rule

Two activities are intentionally distinct:

1. **Final fixed-origin forecasting evaluation:** after the protocol is frozen, the selected XGBoost configuration may be retrained once on train plus validation sales through `d_1913`, then make one fixed-origin `d_1914`–`d_1941` forecast before TEST actuals are loaded for MAE/RMSE/WAPE scoring.
2. **Rolling inventory decisions:** at each simulated date, reorder forecasts use only information that would already be known at that date. Future TEST actuals must never enter a feature, forecast, or reorder decision.

P11 performs neither activity. TEST remains sealed until the P12 execution protocol is invoked; it must not influence model selection, policy design, safety stock, cost coefficients, or any other frozen assumption.

## Limitations

- Simulated inventory and lead time are not observed Walmart operations.
- Observed sales are an imperfect proxy for demand because M5 has no stock-out/censoring signal.
- The deterministic lead time, normal-service safety-stock proxy, lost-sales assumption, and normalized cost weights are transparent modeling choices.
- Results will compare policy behavior under these common assumptions, not establish causal operational performance for Walmart or every supermarket.
