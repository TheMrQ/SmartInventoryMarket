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

## Definition of Done

The completed engine must have documented inputs and assumptions, verified calculations and tests, explainable recommendations, and an experiment-backed comparison with the minimum-stock policy.
