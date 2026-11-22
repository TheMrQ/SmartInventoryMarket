# P24 Final - End-to-End Business Workflow Acceptance

Status: `IN_PROGRESS` - automated and read-only live-MySQL evidence is complete; required browser acceptance evidence remains outstanding. This report does not authorize a scenario reset or repeat a completed mutation.

## Scope and live baseline

- Branch/start: `experiment/inventory-control-room` at `a72600cfe9cd50f8741f9203f425025da6c3b8ac`.
- MySQL migration head and schema check: `c7e3a8d1f4b6`; no drift reported.
- Scenario: `SIM_M5_CA1_FOODS_V1`, 36 mapped products, selection hash `2284aced3531888a0d4b38cd6a7216fcd2c6e1aaae3773b6456c168e6ddc9e95`.
- Observed M5 sales rows: 68,868. Current database contains 12 forecast runs and 1,484 saved forecast values; the scenario's observed sales and saved forecast artifacts remain read-only in this audit.
- No database, scenario, forecast, model, or P22 business record was changed by P24-FINAL.

## Business workflow map

```text
Historical sales -> saved XGBoost V1 forecast -> reliability evidence
-> inventory decision -> reviewed recommendation -> linked draft PO
-> ORDERED / IN_TRANSIT incoming supply -> receipt -> on-hand + stock audit

Operational sale -> on-hand decreases -> inventory position decreases
-> next decision is calculated from the new current state
```

Historical sales are analytical source history. They do not decrement current on-hand inventory when imported. An operational sale is a separate idempotent current-state event: it updates the daily aggregate, decrements on-hand, creates one `OperationalSale`, and creates one `SALE` stock transaction in one transaction.

## Evidence and acceptance matrix

| Workflow | Expected behavior | Evidence | Status | Remaining verification |
| --- | --- | --- | --- | --- |
| Product/inventory read flow | Search, SKU/name, unit, on-hand, incoming, position, history, and empty/error states are read-only | API/frontend regression tests; P24 guide | PASS - automated only | Browser screenshots for search/table/error states |
| Forecast and reliability | Saved `XGBOOST_V1` 7/14/28 views retain point values; 80% range is read-only; 95%/run ID are technical details | P25 reliability tests and P25-03b frontend tests | PASS - automated only | Browser review of chart, wording, disclosure, and stale-demo note |
| Inventory decision | `on_hand + incoming = inventory_position`; unchanged forecast/lead-time/safety-stock formulas determine risk and quantity | Decision-service tests and read-only live distribution: 6 STOCKOUT, 12 REORDER, 6 OVERSTOCK, 12 HEALTHY | PASS - automated and live read-only | Browser calculation explanation |
| Recommendation review | NEW -> ACCEPTED/MODIFIED/REJECTED/EXPIRED semantics, actor/timestamp, approved quantity, one linked draft only | P21 decision/business tests | PASS - automated only | Browser review action/error evidence without mutating scenario |
| Linked draft PO | `SIM_M5_CA1_FOODS_V1-LINKED-DRAFT` remains DRAFT, FOODS_1_002, 6 ordered/0 received/6 remaining, linked recommendation | Live read-only snapshot | PASS - live read-only | Open Manage and close; do not transition/edit/receive/cancel |
| PO state machine | DRAFT -> APPROVED -> ORDERED -> IN_TRANSIT -> RECEIVED; cancellation and invalid transitions rejected | Business API tests | PASS - automated only | Browser action ordering/dialog behavior without confirmation |
| Receipt invariant | Receipt increases on-hand and reduces incoming by the same amount, leaving position unchanged; one audit row per receipt call | Business API tests; completed P24 controlled receipt | PASS - prior manual evidence | Do not repeat `FOODS_2_006` receipt |
| Operational sale | One logical sale decrements stock once, writes one operational sale and one SALE audit; retry key replays safely | Sales API tests | PASS - automated only | Controlled one-unit browser sale for FOODS_3_012, only after fresh baseline |
| Supplier mapping rules | Preferred/active mapping selection and conflicts are deterministic; mapping write never changes stock | Decision/business tests | PASS - automated only | Browser validation/error-state evidence |
| Eligibility/error behavior | Missing/inactive/ambiguous/no-history/no-forecast cases reject clearly | Decision and forecast API tests | PASS - automated only | Browser direct-detail error/retry evidence |
| Timezone, confirmation, account | UTC display helper, application confirmation, profile/avatar/password-session policy | Auth/frontend regression tests | PASS - automated only | Browser visual/accessibility verification; two-session password test is optional |

## Confirmed live scenario facts

- `FOODS_2_006` / `SIM_M5_CA1_FOODS_V1-PARTIAL`: RECEIVED; ordered 8, received 8, remaining 0; on-hand 11, incoming 0, inventory position 11. Do not receive it again.
- Its stock history includes the owner-completed final receipt of quantity 2 as one `RECEIPT` audit row. Earlier legitimate scenario/P24 receipt rows of quantity 3 are retained; total receipt-row count for this SKU is therefore 3, not a reason to re-run or repair anything.
- `FOODS_1_002` / linked draft: on-hand 0, incoming 0, inventory position 0; current decision is STOCKOUT_RISK with recommended quantity 6. Its DRAFT PO does **not** contribute incoming supply.
- Incoming supply includes only `ORDERED` and `IN_TRANSIT` PO lines. DRAFT, APPROVED, RECEIVED, and CANCELLED lines do not contribute incoming quantity.
- `FOODS_3_012` is safe only as a prepared manual target: on-hand 17, incoming 0, inventory position 17, zero operational-sale rows, and zero SALE stock-transaction rows at this snapshot. A manual sale must re-query these values immediately before any mutation.

## Controlled manual acceptance checklist

1. **Read-only pages:** search a SKU/name in Products and Inventory; inspect no-results, units, on-hand/incoming/position, and transaction history. Do not submit edits.
2. **Forecasts:** open a compatible saved forecast. Confirm 7/14/28 summaries, Forecast estimate, typical 80% range, manager-friendly reliability explanation, model/cutoff/period, and technical 95% range/run ID. Confirm the fixed historical-demo limitation is visible.
3. **Inventory Insight:** open a decision and confirm position, lead-time demand, safety stock, reorder point, target stock, and recommendation are explained without creating a recommendation or PO.
4. **Linked draft:** search `SIM_M5_CA1_FOODS_V1-LINKED-DRAFT`, open Manage, inspect FOODS_1_002/recommendation/quantities/status, then close. Do not act on it.
5. **Completed receipt:** inspect `SIM_M5_CA1_FOODS_V1-PARTIAL` only. Confirm RECEIVED and 8/8/0 plus 11/0/11; do not click receipt/workflow controls.
6. **Sale preparation:** before any sale, re-query FOODS_3_012. Proceed only if it is still 17/0/17 with no operational sale/SALE row. Record exactly one unit once, retain the idempotency key, and retry only that same logical request to verify it does not double-decrement. Then record one operational sale and one SALE transaction, and inspect the recalculated decision without assuming its risk must change.
7. **Responsive/accessibility:** at desktop and narrow widths verify search toolbars, tables, PO Manage, Inventory Insight, reliability disclosure/tooltips, keyboard focus, Escape/backdrop dialog behavior, no clipping, and reduced-motion behavior.

## Limitations and defense statement

P22 uses observed M5 historical demand mapped to a synthetic supermarket operational layer. Forecasts and reliability intervals are decision support, not a guarantee or automatic purchasing authority. A new retailer needs its own POS, product, price, calendar, inventory, and supplier data with retraining/validation. P24 cannot be marked `DONE` until the remaining browser interactions and controlled sale evidence are captured without disturbing the preserved scenario baseline.
