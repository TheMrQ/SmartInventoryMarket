# Inventory Management

Status: `DONE` — P15 adds auditable operational sales; decision recommendations remain later work.

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
- P13 decided the database representation; P14 implements the matching operational API without changing the schema.

## P14 Implemented Inventory Operations

- Product creation creates its single inventory row with `on_hand = 0` atomically.
- `POST /api/inventory/{product_id}/adjustments` accepts only `ADJUSTMENT_IN` or `ADJUSTMENT_OUT`, requires a positive quantity/reason, locks inventory, and writes an immutable matching stock transaction. Outgoing adjustments that would make stock negative return a conflict.
- `GET /api/inventory` and `GET /api/inventory/{product_id}` return `on_hand`, derived `incoming_quantity`, and `inventory_position = on_hand + incoming_quantity`.
- Incoming quantity counts remaining PO-item quantity only while the PO is `ORDERED` or `IN_TRANSIT`; `DRAFT`, `APPROVED`, `RECEIVED`, and `CANCELLED` are deliberately excluded.
- A receipt is the only P14 procurement operation that increases on-hand inventory. It validates/locks each line, increments `received_quantity` and inventory, and writes `RECEIPT` transactions in one commit. A partial receipt remains `IN_TRANSIT`; complete receipt becomes `RECEIVED` with UTC `received_at`.

There is no generic inventory PUT/PATCH endpoint or automatic purchasing. P15 adds `POST /api/sales/record`: it verifies an active product and sufficient locked stock, increments/creates the normalized daily-sales row, decreases `on_hand`, and writes an immutable `SALE` transaction in one commit. A failed sale leaves all three states unchanged. Historical CSV backfill is intentionally different: it changes only `sales_daily`, never current inventory. If a supplied operational price replaces a daily price, it is the latest observed price for that daily aggregate; an omitted price preserves it.

## Definition of Done

The feature is done only after documented requirements, validated stock-transaction behavior, relevant tests, database/API integration, and updated project memory exist. It must supply current stock and incoming stock to the future inventory decision engine.
