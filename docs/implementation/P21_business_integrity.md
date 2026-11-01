# P21 — Business Integrity & Workflow Completion

Status: `DONE` — implementation, isolated regression evidence, local additive MySQL migration verification, and frontend static checks are complete. Browser-driven end-to-end evidence remains a P24 activity.

## Scope and invariants

P21 closes the operational gaps found by P20 without changing the frozen XGBOOST_V1 experiment, M5 source data, or the approved Inventory Control Room visual direction.

| Concern | P21 guarantee |
| --- | --- |
| Audit attribution | Mutating operational routes resolve the actor from the authenticated server session. Client `created_by_user_id`, `approved_by_user_id`, and `reviewed_by_user_id` fields are accepted only for backward-compatible request parsing and are ignored. |
| Authorization and request integrity | The existing session, manager/admin role check, and CSRF validation continue to guard operational writes. |
| Operational sale replay | Every sale requires a stable idempotency key. The `operational_sales` table has a database-unique key and retains the exact logical sale payload. An identical retry returns the original daily aggregate; a changed payload with the same key is rejected. |
| Stock consistency | A new sale's daily aggregation, inventory decrement, `SALE` transaction, and durable sale event commit together. Historical CSV import remains inventory-neutral. |
| Recommendation conversion | Only `ACCEPTED` or `MODIFIED` recommendations with a positive approved quantity may become a draft PO, and only after explicit `confirm: true`. The order uses the reviewed quantity, not the old recommendation quantity. |
| Duplicate purchase orders | `purchase_orders.reorder_recommendation_id` is nullable and unique, so manual orders remain supported while one recommendation cannot create two linked POs, including race conditions. |
| Inventory movement | Draft-PO creation never changes on-hand stock. Only existing receipt logic changes inventory, with locked rows, remaining-quantity validation, and immutable `RECEIPT` transactions. |

## Database migration and compatibility

Revision `d4e9a6c21f35_add_p21_integrity_workflows` revises `a91c2e6f4b20`. It creates `operational_sales` and adds nullable `purchase_orders.reorder_recommendation_id`, an FK to `reorder_recommendations`, and its unique constraint. This is additive: no application rows, M5 data, model artifacts, or demo records are overwritten.

The local MySQL migration was advanced forward with `alembic upgrade head`. `alembic current` reports `d4e9a6c21f35 (head)` and `alembic check` reports no new upgrade operations.

## API and frontend workflow changes

- API routes pass the authenticated actor into inventory adjustments, operational sales, PO creation/line changes/transitions/receipts, and recommendation review. Services persist that identity rather than trusting request input.
- `POST /api/reorder-recommendations/{recommendation_id}/purchase-order` creates one explicitly confirmed draft PO from the approved recommendation quantity and selected valid supplier mapping.
- `GET /api/forecasts/eligibility` exposes active product compatibility with the frozen M5 CA_1/FOODS vocabulary. This is a preflight indicator; forecast generation still authoritatively validates required history, price/calendar metadata, and the requested 7/14/28-day horizon.
- The Sales modal creates one idempotency key for its lifetime, so retrying the same still-open logical sale reuses it; reopening the modal starts a new sale with a new key.
- Purchase-order management exposes remaining quantity, draft-line update/delete, partial receipt entry, permitted cancellation, and confirmation prompts for destructive actions. Server validation remains authoritative for over-receipt, repeated receipt, and invalid transitions.
- Inventory Insights can create the linked draft PO only after review and confirmation, and shows an existing linked PO instead of offering a duplicate conversion.
- Dashboard, Products, Inventory, Suppliers, Purchase Orders, Sales, Forecasts, and Inventory Insights distinguish failed queries from empty results and provide a retry action without discarding open form input.

## Verification evidence

`pytest` completed with **68 passed** (two third-party TestClient deprecation warnings). The isolated suite covers operational-sale replay and conflicting replay, one inventory decrement/`SALE` audit record, forged actor-field resistance, recommendation-to-draft-PO linkage and duplicate prevention, valid/invalid PO transitions, partial receipt, over-receipt rejection, repeated final receipt rejection, and existing session/RBAC/CSRF checks. SQLite is intentionally disposable for those tests; it does not replace database-engine concurrency/load testing. The unique database constraint is the production concurrency guard.

The frontend's dependency-free `npm test` covers stable caller-held sale-key generation, eligibility gating, client-side receipt-line bounds, and the distinction between an initial-load failure (blocking) and a background refetch failure with cached data (non-blocking, so open input stays mounted). `npm run lint` and `npm run build` pass. The build retains the pre-existing Vite advisory about a bundle over 500 kB. `git diff --check` passes before commit.

## Remaining limitations and P24 manual checklist

No browser automation is available, so P21 does not claim a fully observed browser workflow. P24 must capture and retain evidence for:

1. Sign in as a manager, verify an inventory adjustment/a sale/PO receipt/recommendation review show the session actor, then attempt a forged actor field and confirm it cannot impersonate another user.
2. Submit the same sale twice with the same key and verify stock and `SALE` audit history change once; submit the same key with a changed quantity and verify a conflict.
3. Review a recommendation, explicitly create its draft PO, retry creation, and verify one linked PO and no inventory change before receipt.
4. Edit and remove draft lines; transition through allowed states; partially receive and then complete a PO; verify remaining quantity, stock transactions, and over-receipt/repeat-receipt errors.
5. Select an M5-compatible and a non-compatible SKU on Forecasts. Verify unsupported products are labelled/disabled, existing saved forecasts remain visible, and 7/14/28-day generation works only for eligible products with complete required history.
6. Simulate a query/network failure on each of the eight operational pages, use Retry, and confirm empty states are not shown as failed data and unsaved modal input is preserved.

P22 may now build the separately marked, traceable M5-grounded supermarket simulation. It must not treat P21's synthetic operational records as observed Walmart inventory or claim that arbitrary new SKUs are forecastable without retraining.
