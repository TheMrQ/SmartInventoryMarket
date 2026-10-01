# Inventory Management

Status: `TODO` — planned only.

## Purpose

Maintain reliable current inventory for the single-store MVP so later risk analysis and reorder recommendations have trustworthy operational inputs.

## Planned Capabilities

- Stock in
- Stock out
- Adjustments
- Current inventory monitoring
- Supplier records
- Purchase orders and incoming-stock visibility

## Frozen Business Rules — CHECKPOINT-011

- Current inventory must remain nonnegative under normal transaction handling.
- Every stock change must have an immutable, auditable transaction: `RECEIPT`, `SALE`, `ADJUSTMENT_IN`, or `ADJUSTMENT_OUT`.
- Open purchase-order quantities contribute to incoming/on-order state, but only a receipt increases on-hand inventory.
- Recommendation acceptance does not itself alter stock. Cancelled purchase orders do not count as incoming inventory.
- P13 will decide database representation; P11 does not create a database, migrations, or CRUD implementation.

## Definition of Done

The feature is done only after documented requirements, validated stock-transaction behavior, relevant tests, database/API integration, and updated project memory exist. It must supply current stock and incoming stock to the future inventory decision engine.
