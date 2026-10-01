# Inventory Decision Engine

Status: `TODO` — conceptual design only.

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
