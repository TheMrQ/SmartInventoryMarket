# P20 Functional Audit — Smart Inventory Market

Audit date: 2026-11-01
Branch audited: `experiment/inventory-control-room`
Audit scope: source review, isolated automated tests, read-only local-MySQL migration/data checks, frontend build checks, and available automation inventory. No business records, users, model artifacts, or raw M5 data were changed.

## Evidence and confidence labels

| Label | Meaning |
| --- | --- |
| **IMPLEMENTED AND TESTED** | Source exists and an automated test exercises the relevant rule on disposable SQLite state. |
| **IMPLEMENTED BUT NOT LIVE-VERIFIED** | Source and/or build evidence exists, but P20 did not perform the mutation against local MySQL or a browser. |
| **PARTIALLY IMPLEMENTED** | A useful API or screen exists, but a required workflow step, integration, validation, or truthful error path is missing. |
| **MISSING** | No supported implementation was found. |
| **BROKEN** | P20 reproduced a failure. No feature was classified BROKEN in this audit. |

The SQLite suite proves service and route behavior without touching local MySQL. It is not evidence that a real browser flow or every MySQL concurrency behavior was exercised.

## Environment and immutable prerequisites

- Current branch is `experiment/inventory-control-room`; only `.agents/` and `skills-lock.json` were untracked and they were preserved.
- The local `.env` exists; only the names `APP_ENV` and `DATABASE_URL` were inspected. No secret values were read or reported.
- The configured database uses MySQL/PyMySQL. Read-only Alembic checks report revision `a91c2e6f4b20 (head)` and **no schema drift**.
- M5 calendar, sales, prices, feature manifest, and the ignored selected XGBoost artifact are present locally. The artifact SHA-256 matches the pinned application checksum. It was not regenerated or loaded for a new forecast during P20.
- A read-only count observed existing local operational records: 5 products, 2 suppliers, 1 purchase order, 9 forecast runs, and 2 recommendations. This establishes that a local demo footprint exists, not that every workflow was re-executed.
- Browser access host/native pipe were unavailable. No browser interaction, route click, responsive inspection, or live UI mutation is claimed.

## Per-page functionality matrix

| Page | Actual APIs called | Implemented operations and persistence | Validation/RBAC/refresh evidence | Status and audit finding |
| --- | --- | --- | --- | --- |
| Dashboard | `inventory`, `products`, `inventory-decisions`, `reorder-recommendations`, `purchase-orders` | Read-only live-data composition; no invented dashboard metric in source. | React Query loading is present. No page-level `isError` surface was found; reads were not browser-verified. | **IMPLEMENTED BUT NOT LIVE-VERIFIED** — truthful empty states exist, but fetch failure can look like an empty/partial dashboard. |
| Products | `products`, `categories`, create/patch product | Creates product and an inventory row atomically; edits product fields. | SQLite API tests prove a new product starts at zero stock and uniqueness/foreign-key errors return domain failures. Manager/server dependency applies; successful mutation invalidates products and inventory. | **IMPLEMENTED AND TESTED** for API; **IMPLEMENTED BUT NOT LIVE-VERIFIED** for UI. Category creation/maintenance has an API but no page control. |
| Inventory | `inventory`, `stock-transactions`, `products`, adjustment endpoint | Lists position and audit rows; records in/out adjustment with a reason. | Service locks inventory, rejects negative balance, writes one adjustment transaction, and tests cover it. UI invalidates inventory/transactions/decisions and shows mutation errors as toasts. | **IMPLEMENTED AND TESTED** for integrity; actor ID is not bound from the authenticated session (see HIGH finding). |
| Suppliers | `suppliers`, `supplier-products`, `products`, create supplier/mapping | Creates suppliers and supplier-product mappings; supports preferred supplier and lead time. | API tests cover duplicate mapping and one preferred mapping; UI refreshes mappings/decisions. Server rejects inactive supplier/product for new mapping. | **PARTIALLY IMPLEMENTED** — UI has no supplier edit/deactivate or mapping edit; browser flow not verified. |
| Purchase Orders | `purchase-orders`, `suppliers`, `products`, create/transition/receive | Creates draft, advances DRAFT → APPROVED → ORDERED → IN_TRANSIT, receives goods. API also supports draft item add/update/delete and cancellation. | SQLite tests prove eligible incoming states, partial receipt accounting, atomic receipt audit, and rejection after final receipt. UI refreshes orders/inventory/transactions. | **PARTIALLY IMPLEMENTED** — UI exposes only sequential forward transitions and full remaining receipt; it lacks partial receipt entry, cancellation, and draft line editing despite API support. |
| Sales | `sales`, `products`, record/import sales | Imports historical CSV by upsert without stock mutation; records operational sale, reduces stock, and writes `SALE` transaction. | SQLite tests cover malformed/unknown/duplicate import rows, no stock change from import, insufficient stock rejection, and sale/audit transaction. UI invalidates sales/inventory/transactions/decisions. | **IMPLEMENTED AND TESTED** for a single request; **PARTIALLY IMPLEMENTED** operationally because it has no idempotency/external-sale reference and actor ID is not session-bound. |
| Forecasts | `products`, `forecasts/latest`, `forecasts`, `forecast-runs`, sales history for chart | Saves frozen XGBOOST_V1 7/14/28-day runs and retrieves latest per product; shows saved historical/forecast context. | Schema restricts horizons; isolated tests prove compatible-history, unknown-SKU, hash-failure, and past-only recursive behavior. Artifact hash matched locally. | **IMPLEMENTED BUT NOT LIVE-VERIFIED** — P20 did not invoke the artifact against MySQL. The UI lists all active products, including incompatible SKUs that the API then rejects. |
| Inventory Insights | `inventory-decisions`, `reorder-recommendations`, `products`, `forecasts/latest`; generate/review recommendation | Explains real persisted forecast, on-hand, incoming, lead time, safety stock, risk, and recommendation; supports accept/modify/reject. | Tests prove no inventory change during recommendation generation, incoming treatment, supplier selection, expiry, and valid review transitions. UI invalidates decisions/recommendations/inventory. | **PARTIALLY IMPLEMENTED** — human review is preserved, but reviewer attribution is not server-bound and accepted/modified recommendations cannot safely create a linked PO. |

### Cross-page frontend observations

- Mutations consistently use a shared API client, HTTP error normalization, toast errors, and targeted React Query invalidation.
- Query loading indicators exist. The eight pages generally do not render a dedicated query-error state; a read failure can therefore leave an empty table/panel without a direct explanation. This is a P21 usability/reliability item, not proof of a backend failure.
- The API client sends cookie credentials and the CSRF header for non-FormData mutations. Authentication and route protection remain separate from visual P19 work.

## End-to-end invariant trace

| Required invariant | Finding | Evidence |
| --- | --- | --- |
| New product starts at zero stock | Satisfied. | `BusinessService.product_create` flushes Product then adds `Inventory(on_hand=0)`; `test_category_product_creation_inventory_and_conflicts`. |
| One recorded sale decreases stock once | Satisfied per successful request. | Inventory row is locked, quantity is decremented, and one `SALE` transaction is inserted in one commit; `test_operational_sale_is_atomic_inventory_and_audit`. |
| Insufficient stock prevents sale | Satisfied. | Service checks requested quantity before decrement; same P15 test. |
| Historical CSV import does not reduce stock | Satisfied. | Import only upserts `sales_daily`; `test_historical_import_upserts_and_never_changes_inventory`. |
| Adjustments create audit movements | Satisfied. | Adjustment uses a locked inventory row, reason, and `ADJUSTMENT_IN/OUT` transaction; P14 test. |
| Incoming stock counts only eligible PO states | Satisfied. | Repository sums remaining quantities only for `ORDERED` and `IN_TRANSIT`; P14/API and P16 decision tests. |
| Partial receipt updates accurately | API satisfied; UI incomplete. | Receipt locks PO/items/inventory, enforces remaining quantity, and keeps status `IN_TRANSIT` until all lines are received; P14 partial-receipt test. UI always submits all remaining quantities. |
| A second final receipt cannot double-count | Satisfied. | Final receipt changes state to `RECEIVED`; later receipt is rejected; P14 test. |
| Recommendations do not change stock | Satisfied. | Decision generate persists recommendation only; P16 test asserts unchanged inventory. |
| Accept/modify/reject transitions are valid | Satisfied. | Only `NEW` can be reviewed; ACCEPT/MODIFY/REJECT quantity rules are enforced; P16 transition test. |
| Human review is preserved | Satisfied as a state transition; incomplete as audit attribution. | UI and service require explicit review; review does not auto-create PO. Reviewer can be omitted or client-supplied. |
| Recommendation → PO integration | Missing by design; duplicate-order risk remains. | UI explicitly says review does not create PO; no recommendation foreign key on `PurchaseOrder`; manual PO creation has no accepted-recommendation deduplication. |
| Role restrictions are server-side | Satisfied at coarse role level; attribution needs correction. | All operational routers use `operational_user`; non-manager registration session receives 403 on operational POST in auth test. GET remains authenticated-reader access. |

## Findings, severity, and data-integrity risks

| ID | Severity | Finding | Impact | Required direction |
| --- | --- | --- | --- | --- |
| P20-01 | **HIGH** | Actor fields (`created_by_user_id`, `approved_by_user_id`, `reviewed_by_user_id`) are optional request fields rather than derived from the authenticated user. The UI sends none; a manager client can name another existing user. | Audit records can be empty or falsely attributed even though authorization remains manager-only. | Inject `current_user` into write routes/services; remove client authority over actor IDs; add role/attribution tests. |
| P20-02 | **HIGH** | An accepted or modified recommendation cannot create a linked PO, and manual PO creation has no recommendation link or duplicate guard. | Manager must re-enter products/quantities; repeated orders for the same decision are possible; traceability stops at review. | Add explicit review-to-draft-PO command with a recommendation/PO relationship, one active PO guard, and transactional validation. |
| P20-03 | **MEDIUM** | Operational sale recording has no idempotency key or POS event reference. | A retried client request can be interpreted as a second legitimate sale and reduce stock twice. | Add an immutable external sale reference/idempotency constraint and retry-safe API behavior. |
| P20-04 | **MEDIUM** | Purchase Order UI cannot enter partial receipt quantities, cancel an order, or edit DRAFT lines although the API supports these workflows. | The core process is usable only for full receipts and does not expose all safe backend controls. | Add PO detail/draft editor, cancellation action, and line-level receipt form; preserve server state machine. |
| P20-05 | **MEDIUM** | Forecast selector offers arbitrary active products, while frozen model only accepts compatible M5 CA_1/FOODS SKU vocabulary. | Expected API error is exposed late; application can appear to promise universal forecasting. | Expose eligibility metadata/read endpoint, filter or mark selector choices, and give an explicit M5-simulation message before generate. |
| P20-06 | **MEDIUM** | No dedicated query-error states across the operational pages. | Database/network failures can resemble empty data, reducing truthful operational feedback. | Add shared query-error recovery panel with retry and retain existing mutation toasts. |
| P20-07 | **LOW** | Automated backend tests use SQLite dependency overrides and role stubs for most business endpoints. | They are strong rule tests but do not prove MySQL locking or a real browser workflow. | Keep isolated tests; add carefully marked, opt-in live-MySQL smoke tests and browser E2E as P24 integration evidence after P21/P22 implementation is stable. |

No source-confirmed defect was changed during P20 because the findings require coordinated design and new tests rather than an isolated audit-only fix.

## Forecasting limitations and safe operational meaning

The original `XGBOOST_V1` artifact is unchanged: its current local SHA-256 matches the pinned application value. Forecast creation accepts only 7, 14, or 28 days; only active SKUs in the frozen M5 vocabulary with valid department encoding, 28 contiguous daily sales ending on 2016-04-24, M5-compatible prices, and required calendar metadata may run. The recursive feature path consumes only this fixed past history and future calendar context, not future TEST actuals. Unit tests cover past-only features and recursive behavior; P20 did not rerun inference against MySQL.

Saved forecasts are reproducible only in this M5-grounded simulated context. The current system cannot forecast a newly invented supermarket SKU. The Forecasts page must therefore make eligibility visible before action, and the simulated operating catalog must use eligible M5 SKU identities with the required fixed-origin history. Production use for another supermarket requires retraining on that store's POS/product/calendar/price context.

## Proposed safe M5 supermarket simulation — not implemented in P20

### Scope

Create a small named scenario using five eligible `FOODS` CA_1 SKUs already known to the frozen model. Import only the fixed 28 historical days ending at 2016-04-24 and their historical prices; use the frozen model to persist a single 28-day forecast run. Create synthetic operational entities separately: a clearly named demo category, suppliers, supplier mappings/lead times, on-hand inventory, one incoming PO, and engine-generated recommendations. Synthetic records must never be labeled as observed Walmart inventory or as M5 forecast output.

### Repeatability and reset strategy

1. Require explicit scenario ID/prefix, for example `SIM_M5_CA1_FOODS_V1`, plus a dry-run report first.
2. Record every created ID in a local ignored scenario manifest and tag synthetic texts/PO numbers/reasons with that scenario ID.
3. Preflight all frozen prerequisites and forecast eligibility before the first operational write; never train or substitute predictions.
4. Make setup idempotent by reusing only records with the exact scenario marker and verifying their expected state. Do not modify unmarked products, users, suppliers, sales, POs, or forecasts.
5. Reset only after an explicit command: resolve the manifest IDs, check each still has the marker, then delete in foreign-key-safe order. Never use broad prefix-only deletes, never delete users, and refuse reset if an item was externally modified or linked outside the scenario.
6. Separate the historical M5 import from simulated inventory/PO records in UI copy, source fields, and documentation.

The existing `scripts/db/setup_ui_demo.py` demonstrates several useful principles (artifact preflight, M5 import, service-only writes, idempotent markers), but P20 did not run it because it is state-changing. It must be redesigned around an explicit scenario manifest/reset guard before becoming the recommended repeatable demo tool.

## Prioritized implementation backlog

### P21 — Business Integrity & Workflow Fixes

1. Bind all write/audit actor IDs to authenticated server-side identity; remove client-controlled actor attribution and add API tests.
2. Add a reviewed-recommendation-to-draft-PO workflow, relationship/audit fields, idempotent duplicate guard, and explicit human confirmation.
3. Add sale idempotency/POS reference support and regression tests for duplicate delivery.
4. Complete PO UI: draft line editing, cancellation, controlled partial receipts, and clear stock/audit refresh.
5. Add shared query-error/retry UI and explicit M5 forecast eligibility feedback before forecast action.
6. Acceptance evidence: server-side attribution cannot be client-spoofed; a sale retry is safe; an accepted/modified recommendation produces at most one explicitly confirmed linked draft PO; PO lifecycle controls retain transactional inventory/audit rules; and UI eligibility/error states are truthful.

### P22 — M5-Grounded Supermarket Simulation

1. Implement the marker- and manifest-scoped M5 scenario setup/reset design above, with dry-run, non-destructive preflight, exact created-ID recording, and reset refusal for externally modified or unmarked records.
2. Use real M5 CA_1/FOODS historical sales, calendar/events, and sell-price inputs only for frozen-model-eligible SKUs. Persist a traceable application-product-to-M5 item/store/SKU mapping and scenario provenance.
3. Create only clearly marked synthetic operational inventory, suppliers, supplier mappings/lead times, and purchase orders. Do not label those records as observed M5/Walmart inventory or procurement facts.
4. Generate real predictions only with the unchanged frozen XGBOOST_V1 artifact and only after eligibility preflight. Do not forecast arbitrary new SKUs; retain a future POS ingestion boundary and require retraining/evaluation for a new supermarket.
5. Acceptance evidence: rerun setup safely, prove provenance labels/mapping, show the separated observed and synthetic domains, and prove safe reset affects only manifest-scoped scenario records.

### P23 — XGBoost V2 research and evaluation

1. Preserve all original XGBOOST_V1 configuration, artifacts, validation metrics, and one-time TEST evaluation as immutable historical evidence.
2. Define a separately versioned research hypothesis, data/config manifest, validation protocol, artifact, and comparison table; do not use the V1 TEST window for V2 tuning or selection.
3. Report any V2 result as a separate experiment, not as a revision of V1 or a forecast claim for arbitrary supermarket SKUs.

### P24 — End-to-End Testing & Evaluation

1. Add regression coverage for the P21 workflow invariants and P22 scenario boundary, including actor attribution, PO duplicate prevention, sale idempotency, inventory transaction correctness, provenance, and reset safety.
2. Run opt-in marker-scoped live-MySQL smoke checks and browser E2E/manual acceptance across all eight pages, expanded/collapsed sidebar, error/empty/loading/focus/narrow states, and the complete workflow.
3. Evaluate inventory outcomes only against documented simulation assumptions and keep them distinct from observed M5 inventory facts and from forecasting model-selection evidence.

## Test results

| Check | Result | Scope/limitation |
| --- | --- | --- |
| `pytest` | **65 passed**, 2 deprecation warnings | Backend API/business tests use disposable SQLite; ML tests are deterministic/unit-level. |
| Alembic `current`, `heads`, `check` | **Passed** | Local MySQL is at `a91c2e6f4b20 (head)` with no detected drift. |
| Artifact checksum | **Passed** | Local frozen XGBoost artifact matches pinned SHA-256. No retraining/inference was run. |
| `npm run lint` | **Passed** | Source lint only. |
| `npm run build` | **Passed** | Existing Vite large-chunk advisory remains non-failing. |
| `git diff --check` | **Passed** before documentation commit | No whitespace error in audit changes. |
| Browser/local UI E2E | **Unavailable** | Browser access host/native pipe unavailable; use the manual checklist and integration evidence planned for P24. |

## P20 conclusion

The application has a credible, tested transactional core for inventory, historical sales, frozen forecasting, risk decisions, and human-reviewed recommendations. It is not yet a complete operational loop. P21 must close the attribution, idempotency, recommendation-to-PO, PO-control, eligibility-feedback, and error-recovery gaps. P22 must then establish a safe, traceable M5-grounded simulation without conflating observed M5 history with synthetic operations. P24 is the point for end-to-end live-environment and browser evidence; P23 remains separate research and cannot revise the original XGBOOST_V1 historical results.
