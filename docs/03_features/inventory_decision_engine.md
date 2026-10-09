# Inventory Decision Engine

Status: `DONE` — P16 runtime implementation verified.

## Purpose

Translate predicted demand and inventory context into stockout/overstock risk and reorder recommendations.

## Initial Concepts

```text
Reorder Point = Forecast Demand During Lead Time + Safety Stock

Recommended Quantity = max(0, Target Stock - Current Stock - Incoming Stock)
```

The decision engine will compare a traditional minimum-stock replenishment rule with a forecast-based reorder policy. Rules, assumptions, target stock, lead time, and safety stock are expected to evolve after the inventory experiment protocol is designed and documented.

## Frozen Policy Design — CHECKPOINT-011

`MIN_STOCK_MA28` and `FORECAST_REORDER_XGBOOST_V1` are frozen for later P12 execution. Both use a 1-day review, deterministic 7-day lead time, start-of-day receipts, lost sales, identical initialization, and `1.645 * population_std(previous 28 observed demand days) * sqrt(7)` safety stock. Only demand estimation differs.

Recommendations are human decision support with conceptual statuses `NEW`, `ACCEPTED`, `MODIFIED`, `REJECTED`, and `EXPIRED`; they do not automatically buy from suppliers. See `docs/09_inventory_simulation_protocol.md` and `docs/08_business_processes.md` for the authoritative protocol and workflow design.

## P12 Evidence

The frozen TEST replay found that forecast-based reordering reduced simulated lost sales from 5,362 to 4,365 and stockout SKU-days from 1,565 to 1,222, increasing fill rate from 94.097% to 95.194%. It also raised average on-hand inventory from 11.806 to 12.569 and normalized cost proxy from 515,039 to 540,233. This mixed trade-off is experimental evidence for later decision-service design, not authorization to alter the frozen policy or automate purchases.

## Definition of Done

The completed engine must have documented inputs and assumptions, verified calculations and tests, explainable recommendations, and an experiment-backed comparison with the minimum-stock policy.

## P16 Runtime Policy

For a valid persisted forecast and selected supplier lead time `L`, P16 calculates:

```text
inventory_position        = on_hand + incoming_quantity
expected_lead_time_demand = sum(forecast days 1..L)
safety_stock              = ceil(1.645 * population_std(previous 28 observed sales days) * sqrt(L))
reorder_point             = ceil(expected_lead_time_demand + safety_stock)
target_stock              = ceil(sum(forecast days 1..L+1) + safety_stock)
recommended_quantity      = ceil(max(0, target_stock - inventory_position)) when position <= reorder_point; otherwise 0
```

The service factor and one-day review period come from the frozen P11/P12 protocol. Lead time comes from the selected supplier mapping, not the experiment's fixed seven-day assumption. It requires 28 contiguous observed sales days ending at the forecast boundary and consecutive forecast values through `L + 1`; missing data returns a clear business error.

Supplier selection is deterministic: exactly one active preferred mapping wins; otherwise exactly one active mapping is used. None or multiple non-preferred mappings fail instead of making an arbitrary choice. `STOCKOUT_RISK` means position is below expected lead-time demand; `REORDER_NEEDED` means it is at/below the reorder point; `OVERSTOCK_RISK` means it exceeds target stock plus next-day forecast demand; otherwise it is `HEALTHY`. These are business-rule labels, not ML classifications.

`GET /api/inventory-decisions` is side-effect free. `POST /api/reorder-recommendations/generate` saves a one-day `NEW` snapshot only if quantity is positive and expires earlier `NEW` snapshots atomically. Explicit ACCEPT/MODIFY/REJECT review actions are terminal. P16 deliberately defers recommendation-to-PO conversion: no P16 operation changes inventory, creates a purchase order, or contacts a supplier.

The forecast model remains M5-specific. The decision engine is reusable business logic, but this deployment can decide only for products with compatible persisted forecasts until a target-supermarket model exists.
