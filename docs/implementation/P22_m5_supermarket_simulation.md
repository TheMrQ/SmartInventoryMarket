# P22 — M5-Grounded Supermarket Simulation

Status: `BLOCKED` — the provenance schema, deterministic 36-SKU selection, dry-run setup, and local migration are implemented and verified. The script deliberately refuses its first state-changing apply because no active local `MANAGER` or `ADMIN` account exists. No scenario data was imported or fabricated.

## Data boundary and deterministic selection

`configs/data/m5_ca1_foods_demo.yaml` defines scenario `SIM_M5_CA1_FOODS_V1`: 12 lexically ordered eligible items from each of `FOODS_1`, `FOODS_2`, and `FOODS_3` at store `CA_1` (36 products total). The resulting ordered selection has SHA-256 `2284aced3531888a0d4b38cd6a7216fcd2c6e1aaae3773b6456c168e6ddc9e95`.

The setup reads only:

- `sales_train_evaluation.csv`: original `item_id`, `dept_id`, `store_id`, and daily `d_1` through `d_1913` sales;
- `calendar.csv`: `d`, calendar date, `wm_yr_wk`, event name/type, and `snap_CA` context;
- `sell_prices.csv`: `store_id`, `item_id`, `wm_yr_wk`, and `sell_price`.

Observed history stops at `d_1913` / 2016-04-24. The frozen model consumes those 28 preceding observed days and future M5 calendar context only; it never reads `d_1914`–`d_1941` TEST actual demand. The setup therefore demonstrates a historical M5 forecast, not live 2026 supermarket demand.

## Provenance schema

Additive Alembic revision `f6b8c4d92a10` creates:

- `demo_scenarios`: scenario key, source filenames, CA_1 store, fixed day boundary, selected size, and selection hash;
- `demo_product_sources`: one scenario-to-product mapping retaining original M5 item and department IDs, marked `OBSERVED_M5`;
- `demo_scenario_forecasts`: the real persisted frozen XGBOOST_V1 forecast run attached to the scenario.

`products.sku` remains the original M5 item identifier. Friendly names use the intentionally generic form `Food Item <department>-<number> (M5 simulation)` and never assert a branded Walmart identity. Historical sales carry source `M5_OBSERVED_CA1_FOODS_V1`. Inventory, suppliers, mappings, POs, receipts, stock adjustments, and recommendation-review notes are explicitly prefixed with `SIM_M5_CA1_FOODS_V1` and are synthetic operational assumptions.

## Safe setup behavior

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe scripts\db\setup_m5_supermarket_scenario.py
```

This is dry-run only. It verifies raw-data presence, 36-SKU selection, dates, and hash without writes.

After an active manager/admin exists, run:

```powershell
.\.venv\Scripts\python.exe scripts\db\setup_m5_supermarket_scenario.py --apply
```

The apply path is idempotent for the scenario key: it reuses its manifest/provenance mappings, M5 products/history, synthetic suppliers/mappings, forecast-run link, and fixed PO numbers instead of duplicating them. It does not create users, reset/truncate tables, replace raw data/model artifacts, or touch unrelated product records. A conflicting pre-existing SKU or daily-sales record is refused rather than overwritten.

It uses the existing services for synthetic stock adjustments, PO transitions/receipts, recommendation review, and linked-draft PO conversion. Intended coverage is healthy, reorder-needed, stockout-risk, overstock, incoming stock, pending/accepted/modified recommendations, linked draft PO, partially received PO, and completed PO. Those states remain pending until a manager authorizes apply.

## Blocker and safe resolution

The apply attempt stopped before importing data with: `P22 apply requires an existing active manager or admin; it will not create a user`. This preserves P21 server-bound attribution rather than inserting synthetic records under an invented or unauthorized actor.

The owner may provision or promote a local thesis-demo manager with the existing password-prompting utility (credentials must not be supplied to the agent or committed):

```powershell
.\.venv\Scripts\python.exe scripts\db\provision_manager.py --email <manager-email> --full-name <manager-name>
```

Then rerun dry-run, run `--apply`, verify the real persisted forecast/decision/PO results, rerun `--apply` to prove idempotency, and complete P22/P24 browser walkthrough evidence.

## Verification to date

- Deterministic selection and generic honest display-name tests pass on disposable data.
- The local raw-M5 dry run completed: 36 CA_1/FOODS SKUs, `d_1`–`d_1913`, stable hash above.
- Local MySQL safely upgraded to `f6b8c4d92a10`; `alembic current` and `alembic check` pass with no schema drift.
- No scenario products, historical sales, forecasts, suppliers, POs, inventory movements, or recommendations were written because apply stopped at the actor preflight.

P22 cannot be marked `DONE` until the explicit apply succeeds under a real existing manager/admin and verifies the persisted frozen forecast and engine-derived scenarios.
