# Changelog

All notable project changes are recorded here chronologically.

## 2026-10-10 — P18 auth coin render hotfix

- Replaced the opaque single conic-gradient 3D plane with two backface-hidden, radially masked front/back perimeter rings, preventing it from covering the Register face while preserving the 780 ms coin flip and moving blue/cyan/indigo edge.
- Restored the requested dark-navy authentication canvas, integrated the SmartInventory brand pill with that palette, and adjusted desktop circular form width/padding/gaps while retaining the existing small/short-screen rounded-card fallback.
- Frontend lint/build and local preview health passed. Browser automation was unavailable; final Login/Register screenshots remain required for visual acceptance.

## 2026-10-10 — P18 authentication UX hotfix and live session verification

- Safely applied the existing additive `a91c2e6f4b20` `auth_sessions` migration to local MySQL; Alembic current/heads/check now agree at head without data reset or demo-data deletion. Added a marker-cleaning live verifier proving registration, scrypt storage, session persistence, cookies, `/me`, logout, and revocation against MySQL.
- Changed registration policy to at least 8 characters with one ASCII uppercase letter across the backend contract/helper, frontend indicators, and tests; confirmation stays browser-only and FastAPI 422 lists now become readable inline errors.
- Rebuilt only the auth surface around one persistent `/login`/`/register` component and a 780 ms 3D coin flip, browser-history synchronization, safe focus/inactive controls, responsive overflow-free fallback, light canvas/dark coin/brand treatment, attached reduced-motion gradient ring, and subtle interaction/focus states. Added a password-prompted development-only manager provisioner with no stored credentials.

## 2026-10-10 — P17 animated UX and real cookie-session authentication

- Added responsive circular Login/Register routes with an accessible 3D CSS flip, animated blue/cyan/indigo gradient ring, motion-reduction fallback, protected-route restoration, authenticated sidebar profile, and real logout.
- Added scrypt password hashing, opaque revocable/expiring HttpOnly session cookies, CSRF checks for authenticated state changes, basic sign-in throttling, safe auth responses, public least-privilege `INVENTORY_STAFF` registration, and server-side role checks for operational writes.
- Added `auth_sessions` through a new Alembic migration and focused registration/login/session/logout/protected-access tests; preserved existing operational APIs, forecasting, inventory rules, and model boundaries.

## 2026-10-10 — P17 premium UX pass: stable shell and shared presentation tokens

- Moved the floating sidebar collapse control to a fixed upper anchor with dedicated navigation clearance, preventing overlap with Purchase Orders and other route rows while retaining its accessible chevron-only behavior.
- Added an honest, non-interactive Demo Manager / Demo workspace sidebar persona with a Lucide avatar, pinned profile footer, collapsed avatar-only state, independently scrolling navigation, and mobile-drawer label restoration.
- Added a compact shared frontend token layer for spacing, radii, surfaces, text hierarchy, borders, shadows, transitions, and existing common components without changing routes, API behavior, business rules, data, or model boundaries.

## 2026-10-10 — P17 sidebar layout fix: reliable collapsed navigation

- Repaired collapsed sidebar navigation by replacing the broad nested-span hiding behavior with explicit brand and route-label classes; all eight navigation icons remain visible, centered, and usable when collapsed.
- Tightened group/row rhythm, made route and active-row treatment full width, retained the floating accessible chevron without a visual tooltip, preserved rounded sidebar corners, and retained the mobile off-canvas drawer.
- Kept the existing routes, API behavior, forecasting/inventory calculations, model boundary, data policy, palette, and card system unchanged.

## 2026-10-10 â€” CHECKPOINT-017 visual design polish: lighter SaaS card system and grouped navigation

- Rebalanced the React workspace around Inter Variable typography, light structured cards, soft borders/shadows, refined tables/forms/badges, calmer chart surfaces, and controlled blue accents.
- Reorganized sidebar navigation into Overview, Management, and Intelligence; replaced the full collapse button with a floating chevron handle integrated into the sidebar edge.
- Removed strong blue panel-header surfaces from the prior pass while retaining tooltip, workspace-modal, decision-support, and forecast functionality unchanged.

## 2026-10-10 â€” CHECKPOINT-017 final UX refinement: workspace dialogs and scan-friendly panel headers

- Centered desktop dialogs in the application workspace rather than across the fixed sidebar; contained dialog scrolling with rounded clipping and restrained scrollbar styling.
- Reworked the reusable tooltip lifecycle to open by hover/focus and close on mouse leave, blur, Escape, or unmount, preventing sticky table and decision-detail help overlays.
- Added a consistent blue full-width header treatment to major operational panels, forecast visualization, and model details without altering routes, API contracts, model behavior, or inventory calculations.

## 2026-10-10 â€” CHECKPOINT-017 decision UX: persisted forecast context and unified restocking guidance

- Added a reusable historical-sales plus expected-demand chart with linear daily lines, reused by Forecasts and selected Inventory Insights decisions; it uses only persisted forecast values and the 28 observed days through the stored origin.
- Changed Forecasts to resolve the latest persisted run per product through the existing API, retain product/horizon in URL state, and generate or refresh only on an explicit action.
- Added an Inventory Insights detail panel that presents stock position, lead-time demand, safety-stock buffer, reorder/target stock, strongest recommended-order value, real stock-coverage gap, and optional calculation explanation. No backend rules, schema, model, inference-on-navigation, TEST data access, or automatic purchasing behavior changed.

## 2026-10-10 — CHECKPOINT-017 UX refinement: human-friendly operational presentation

- Removed duplicate desktop page titles, improved sidebar collapse/tooltip behavior, standardized rounded panels and blue focus treatment, and replaced presentation-facing enum strings with centralized friendly labels.
- Added safe M5 demo display labels that retain the real SKU, humanized dashboard, inventory, insight/recommendation, sales, supplier, and purchase-order wording, and kept every backend/API contract unchanged.
- Reworked Forecasts into a real 28-day observed-sales plus persisted-future-forecast visualization, with a forecast-start marker, human-readable two-decimal summaries, and secondary technical model details. No TEST actual demand is loaded or displayed.

## 2026-10-09 — CHECKPOINT-017 polish: blue theme and real thesis-demo state

- Refined the existing React UI with the blue Smart Inventory Market palette, stronger dashboard contrast, semantic risk colors, consistent icons, restrained responsive transitions, blue forecast chart treatment, and reduced-motion support.
- Added optional, idempotent `scripts/db/setup_ui_demo.py`, which verifies prerequisites then uses the established services to prepare two labeled demo suppliers, five preferred mappings, a genuine persisted 28-day frozen XGBoost forecast, audited adjustment-based inventory positions, `DEMO-PO-001` in transit, and real recommendation records.
- The demo script does not retrain, read held-out TEST actuals, directly change `inventory.on_hand`, fake forecast/risk/reorder values, or create duplicate active recommendations on rerun.

## 2026-10-09 — CHECKPOINT-017: responsive React operational dashboard integrated

- Replaced the Vite starter with a responsive React Router operations workspace covering dashboard, products, inventory adjustments/history, suppliers/mappings, purchase-order workflow, sales/import, forecasts, and inventory decisions/recommendation review.
- Added React Query cache/refetch behavior, normalized API errors, Sonner feedback, Lucide icons, Recharts forecast/risk visualizations, modal forms, mobile sidebar behavior, and documented local Vite proxy/API configuration.
- Verified clean frontend lint and production build plus local frontend/backend health responses. No backend business rules, schema, ML artifact, TEST usage, authentication, or automatic purchasing behavior changed.

## 2026-10-09 — CHECKPOINT-016: inventory decision engine and human review workflow complete

- Added layered inventory-decision and reorder-recommendation APIs/services/repositories using persisted forecast demand, current/incoming inventory, deterministic supplier selection, 28-day population-std safety stock, explainable risks, and frozen protocol rounding.
- Added actionable `NEW` snapshot persistence with one-day expiry/supersession and explicit ACCEPT/MODIFY/REJECT workflow. No recommendation action changes inventory, creates a purchase order, or contacts a supplier; PO conversion is intentionally deferred.
- Added isolated decision tests and a marker-cleaning live MySQL smoke script. No database migration, model retraining, feature/model change, TEST-demand input, or frontend implementation was performed.

## 2026-10-09 — CHECKPOINT-015: sales ingestion and frozen M5 forecasting API complete

- Added nullable constrained retail `sales_daily.sell_price` through Alembic revision `8ac7d44590e3`; verified MySQL upgrade, downgrade, re-upgrade, head, and no-drift checks.
- Added layered Sales APIs for inventory-neutral historical CSV UPSERT and atomic operational sale recording with locked inventory, daily aggregation, and immutable `SALE` transactions.
- Added frozen M5-compatible XGBOOST_V1 forecast APIs, SHA-256 artifact validation/cache, exact FEATURE_SET_V1 builder/recursive reuse, atomic run/value persistence, 7/14/28 aggregates, and explicit unknown-SKU/retraining boundary.
- Added idempotent five-SKU CA_1/FOODS demo import plus a live MySQL/model smoke script; smoke run records are cleaned while the intentional demo catalog remains. No model retraining, feature/model selection change, or future TEST-demand input occurred.

## 2026-10-09 — CHECKPOINT-014: operational inventory and purchase-order API complete

- Added layered FastAPI `/api` modules, Pydantic contracts, services, and repositories for categories, products, suppliers, supplier-product mappings, inventory reads, immutable adjustment/history, purchase orders, controlled transitions, and receipts.
- Enforced nonnegative inventory, transaction audit records, one zero-stock inventory row per new product, unique/active supplier-product ordering checks, draft-only PO item maintenance, and a receipt-only path to `RECEIVED`.
- Defined incoming quantity as remaining PO quantity only in `ORDERED`/`IN_TRANSIT`; it is derived, never persisted as editable inventory state.
- Added five isolated API-flow tests (46 total suite tests) plus a marker-cleaning live MySQL API smoke script. Alembic remains unchanged at `f86d36b27719`; no ML, TEST, forecasting, or frontend work changed.

## 2026-10-01 — CHECKPOINT-013: MySQL relational schema and FastAPI database core verified

- Finalized MySQL 8.x + SQLAlchemy 2.x + Alembic + PyMySQL as the application database stack; removed the unused PostgreSQL `psycopg[binary]` dependency and added `pymysql`.
- Added environment-backed database settings, SQLAlchemy engine/session dependency, declarative single-store schema, Alembic environment, and initial migration `f86d36b27719`.
- Created and verified 14 MySQL application tables, portable controlled status values, explicit constraints/indexes/FKs, and a non-secret FastAPI `/health/db` `SELECT 1` health check.
- Added schema unit tests, an ignored-environment setup guide, MySQL Workbench reverse-engineering instructions, frozen schema documentation, and Vietnamese student/supervisor progress update.
- Verified the live MySQL 8.0.46 migration, schema inspector, Alembic head/current/no-drift state, and rollback-only category/product smoke transaction. No ML or inventory-policy experiment was changed.

## 2026-10-01 — CHECKPOINT-012: final held-out forecast and inventory-policy experiment complete

- Retrained validation-selected `XGBOOST_V1` once on TRAIN + VALIDATION through `d_1913` and generated/hashed 40,236 fixed-origin TEST predictions before loading TEST actuals. Final TEST MAE/RMSE/WAPE: 1.454969 / 2.651296 / 64.450274%.
- Implemented deterministic lost-sales inventory simulation, arrival queue, frozen MA28/forecast policy logic, metrics, cost proxy, synthetic tests, and a reusable P12 runner.
- Under identical TEST demand replay, forecast reordering reduced simulated lost sales (5,362 to 4,365) and stockout SKU-days (1,565 to 1,222), while increasing average on-hand inventory (11.806 to 12.569) and normalized cost proxy (515,039 to 540,233).
- Generated final forecasting and inventory tables/figures. TEST was consumed once without post-TEST model selection, tuning, retraining, or protocol changes. P12 is complete.

## 2026-10-01 — CHECKPOINT-011: inventory simulation and business-process protocol frozen

- Added version-controlled daily lost-sales inventory simulation and fair policy-comparison protocols: shared 7-day lead time, 1-day review cadence, 28-day safety-stock history, common initialization, M5 demand replay, and normalized secondary cost proxy.
- Froze `MIN_STOCK_MA28` and `FORECAST_REORDER_XGBOOST_V1`; the sole intended experimental difference is their demand-estimation source.
- Added protocol validation tests and human-readable simulation, workflow, architecture, and database-requirement documentation with Mermaid diagrams.
- Did not run an inventory simulation, retrain/forecast a model, read TEST actuals, create a database/migration, or implement backend/frontend work. P12 is the next execution task.

## 2026-09-21 — CHECKPOINT-010B: validation-selected forecasting model frozen

- Formally selected `XGBOOST_V1` with the 25-feature `FEATURE_SET_V1` / `FULL_V1` using the pre-registered validation WAPE-first rule with MAE/RMSE secondary checks.
- Retained FULL_V1 because all 20-, 16-, and 11-feature reduced variants had higher validation error; documented the modest price and clearer calendar/event benefit for this experiment.
- Added the version-controlled selected-model pointer, thesis-ready selection summary, and a reused validation-comparison figure registered as selected-model evidence.
- Marked P10 complete and intentionally paused the project before P11. TEST remains sealed and was not read, forecast, scored, summarized, or plotted.

## 2026-09-21 — CHECKPOINT-010A: XGBoost feature-group ablation complete

- Reused verified FULL_V1 and trained the three frozen reduced XGBoost variants (NO_PRICE, NO_CALENDAR_EVENT, and DEMAND_PRODUCT_ONLY) under unchanged scope, parameters, recursive validation, and categorical policy.
- Generated tracked ablation results, summary, horizon metrics, manifest, and feature-count/metrics/runtime/horizon figures. FULL_V1 remains lowest on validation WAPE, MAE, and RMSE; it is the recommended candidate for formal selection.
- Added synthetic ablation/config/recommendation tests and corrected the report-layer WAPE field mapping without retraining models.
- Standardized human-readable status markers in project status and documented the convention. TEST sales values were not read, forecast, scored, summarized, or plotted.

## 2026-09-21 — CHECKPOINT-010: Formal validation comparison and frozen ablation protocol

- Added a reproducible analysis runner that reads tracked validation artifacts only, produces formal four-method, horizon, feature-group, and resource-trade-off evidence, and does not load raw M5 or train a model.
- Identified `XGBOOST_V1` as the CURRENT VALIDATION LEADER: it is lower than all current methods on aggregate MAE/RMSE/WAPE and lower than LightGBM on all 28 measured horizons; final selection remains deferred.
- Froze `XGBOOST_FEATURE_ABLATION_V1` with FULL_V1 (25), NO_PRICE (20), NO_CALENDAR_EVENT (16), and DEMAND_PRODUCT_ONLY (11), using WAPE primary and MAE/RMSE secondary.
- TEST sales values were not read, forecast, scored, summarized, or plotted. No new model was trained, tuned, ablated, selected, or evaluated.

## 2026-09-21 — CHECKPOINT-009: Initial XGBoost recursive validation complete

- Added the exact, untuned CPU `XGBOOST_V1` configuration, native-categorical XGBoost wrapper, reusable four-method comparison utility, and synthetic XGBoost/config/reload tests.
- Trained one 400-tree global Poisson XGBoost model on the same 2,668,509 FEATURE_SET_V1 rows used by LightGBM and generated all 40,236 recursive validation predictions before validation actuals were loaded.
- Generated tracked four-method validation, horizon, feature-importance, runtime/model-size, manifest, table, and six figure artifacts. XGBoost beat both baselines and LightGBM on aggregate validation metrics; formal selection remains deferred.
- Kept the 93.565 MiB native JSON model Git-ignored. TEST sales values were not read, forecast, scored, summarized, or plotted; no feature selection, inventory simulation, application work, or final model choice was performed.

## 2026-09-21 — CHECKPOINT-008: Initial LightGBM recursive validation complete

- Added the exact, version-controlled `LIGHTGBM_V1` configuration, reusable global-model and recursive-inference utilities, and 15 passing Python tests covering the feature, baseline, model, and recursive paths.
- Trained one deterministic 400-tree global Poisson LightGBM on 2,668,509 FEATURE_SET_V1 train rows and generated all 40,236 recursive validation predictions before loading validation actuals.
- Generated tracked validation metrics, per-horizon metrics, gain importance, reproducibility manifest, report tables, and five figures. LightGBM beat Seasonal Naive but did not beat the frozen 28-day Moving Average.
- Kept the local serialized model Git-ignored. TEST sales values were not read, forecast, scored, summarized, or plotted; no model-selection decision, inventory simulation, or application functionality was implemented.

## 2026-09-21 — CHECKPOINT-007: Leakage-safe FEATURE_SET_V1 complete

- Added FEATURE_SET_V1 configuration, a train-only long-form construction pipeline, and shared global one-step/recursive-inference feature builders.
- Added past-only lag/rolling demand, calendar/event, deterministic product identity, and conservative past-only price features with explicit missing-price indicators.
- Generated a 2,668,509-row ignored train cache plus tracked feature manifest and methodology summary; added synthetic leakage tests and report-evidence entries.
- Did not read validation/TEST sales values, generate ML predictions/metrics, train LightGBM/XGBoost, simulate inventory, or implement application functionality.

## 2026-09-21 — CHECKPOINT-006: CA_1/FOODS preprocessing and validation baselines complete

- Added a reusable frozen-scope preparation boundary and metadata-only manifest, plus validation-only Seasonal Naive and 28-day Moving Average baseline implementations.
- Added aggregate/per-SKU MAE, RMSE, and WAPE utilities with explicit undefined per-SKU WAPE handling for zero-demand denominators.
- Generated tracked validation metrics/summary tables and report-ready baseline-comparison/per-SKU-distribution figures; added the permanent thesis report-evidence registry.
- Verified 1,437 series and 28 validation days. TEST sales values were not read, forecast, scored, summarized, or plotted.
- Did not implement ML features, train LightGBM/XGBoost, simulate inventory, or implement application functionality.

## 2026-09-17 — CHECKPOINT-005: M5 experimental protocol frozen

- Froze the M5 forecasting scope to `CA_1` + `FOODS` (`FOODS_1`, `FOODS_2`, `FOODS_3`), retaining all 1,437 locally verified SKU/item-store series.
- Froze one 28-day daily forecast and chronological train `d_1`–`d_1885`, validation `d_1886`–`d_1913`, and held-out test `d_1914`–`d_1941` windows.
- Added `configs/data/m5_ca1_foods.yaml` as the machine-readable protocol source, leakage/test-isolation rules, seasonal-naive and moving-average baseline plan, and MAE/RMSE/WAPE metric policy.
- Did not preprocess the subset, calculate a baseline, train a model, engineer features, simulate inventory, or implement application functionality.

## 2026-09-17 — CHECKPOINT-004: M5 acquired and formally audited

- Resolved the Kaggle competition-download blocker outside the repository and acquired the official M5 archive locally.
- Added `scripts/data/audit_m5.py` and generated metadata-only file/audit manifests plus a concise audit table.
- Formally verified local M5 schemas, date coverage, scale, sales/price quality, resource needs, candidate FOODS subsets, horizon feasibility, and chronological split candidates.
- Did not commit raw M5 data, train a model, create features, choose a final subset/horizon/time split, start simulation, or implement application features.

## 2026-09-17 — P4 download access blocked after authentication recovery

- Confirmed Kaggle CLI authentication by successfully listing the five official M5 competition files.
- Attempted the official M5 download into the ignored raw-data directory; Kaggle returned HTTP 403 before any file was acquired.
- Recorded the competition-rule/download-access resolution path; no raw data, credentials, models, features, subset choice, or time split was created.

## 2026-09-17 — P4 acquisition blocked pending Kaggle authentication

- Installed the official Kaggle CLI 2.2.4 inside the project virtual environment and recorded it as a development/data-acquisition dependency.
- Attempted the harmless M5 competition file-list operation; Kaggle required authentication.
- Did not download M5, create credentials, generate manifests, train a model, create features, freeze a subset, or freeze a time split.
- Recorded the exact safe OAuth resolution in project status, dataset memory, experiment memory, and troubleshooting documentation.

## 2026-09-17 — CHECKPOINT-003: dataset strategy and architecture decisions frozen

- Selected M5 Forecasting - Accuracy as the official forecasting dataset and froze the real-sales plus transparently simulated-inventory strategy.
- Recorded MySQL as the application database, SQLAlchemy/FastAPI as the access layer, and MySQL Workbench as the design/admin tool.
- Added initial CSV historical sales import and future POS/API ongoing-sales-sync architecture.
- Documented the distinction between forecast prediction and future model retraining.
- Did not download M5, train a model, begin feature engineering, or select the final SKU subset/time split.

## 2026-09-06 — CHECKPOINT-002: dataset candidates audited

- Changed the next milestone from immediate M5 acquisition to a multi-candidate retail dataset audit.
- Audited M5 Forecasting - Accuracy, OSA-Data, Kaggle Inventory Optimization for Retail, and FreshRetailNet-50K using published metadata, documentation, and lightweight schema inspection only.
- Recorded the distinction between real sales, on-hand inventory, stockout state, and replenishment actions, plus provenance/license risks and dataset-strategy trade-offs.
- Did not download data, train models, begin feature engineering, or freeze an official dataset.

## 2026-09-06 — CHECKPOINT-001: project initialized

- Created the project structure, tracked empty-data/artifact directories, permanent AI-agent operating manual, and project documentation memory.
- Created the FastAPI smoke application with `/` and `/health` endpoints plus two passing smoke tests.
- Initialized and production-built the React/Vite frontend scaffold; no application UI was implemented.
- Created a Python 3.12 virtual environment and installed the planned initial dependency stack.
- Verified Python dependency imports, backend tests, frontend build, ignore rules, and Git working-tree hygiene.
- M5 data was not downloaded or audited; no forecasting or application features were implemented.
