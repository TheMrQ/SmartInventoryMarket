# Project Status

Project: Smart Inventory Market

Thesis: Development of an Intelligent Supermarket Inventory Management and Product Demand Forecasting System Using Machine Learning

Overall status: 🟡 **IN_PROGRESS** — P18 targeted UI repair awaits requested sidebar/chart screenshot verification; broader final evidence remains

## Quick Human Summary

What we selected:

- XGBoost is the validation-selected forecasting algorithm.
- The full 25-feature `FEATURE_SET_V1` / `FULL_V1` is retained.
- It achieved the best validation result: MAE 1.402449, RMSE 2.568234, and WAPE 66.647316%.
- Reducing to 20, 16, or 11 features made validation forecasting worse.
- TEST was sealed during development/model selection, then consumed exactly once by the frozen P12 final evaluation; it must never be used for later tuning or selection.
- Inventory behavior will be simulated because M5 has no stock records.
- The 7-day lead time is an explicit simulation assumption, not observed Walmart practice.
- Both future policies share inventory rules; only their demand estimate differs.
- Business workflows and architecture requirements are frozen enough to guide later database design.
- The final held-out XGBoost TEST forecast achieved MAE 1.454969, RMSE 2.651296, and WAPE 64.450274%.
- Forecast-based reordering reduced simulated lost sales and stockouts, but held more inventory and had a higher normalized cost proxy.
- TEST was consumed once for final evaluation; no tuning may be performed against it.

Why:

- FOODS is closest to the supermarket scenario, and audited `CA_1` FOODS has the lowest zero-sales prevalence among the candidate full-FOODS stores.
- 1,437 series are large enough for global ML experiments while remaining manageable.
- A 28-day forecast aligns with M5 and supports both short- and medium-term inventory views.
- Mixing unrelated sales and inventory datasets would weaken the thesis.
- A deployed supermarket must eventually use its own POS history, not Walmart M5 data permanently.

What we did:

- Downloaded and locally inspected the five official M5 files.
- Verified their real columns, sizes, products, stores, dates, sales, and prices.
- Froze `CA_1` + `FOODS`, all three FOODS departments, a 28-day horizon, and chronological evaluation boundaries.
- Added the version-controlled protocol at `configs/data/m5_ca1_foods.yaml`.
- Prepared the frozen source boundary and generated the first fixed-origin 28-day validation forecasts.
- Converted train sales into leakage-safe ML features: past sales lags, rolling demand, calendar/events, product codes, and historical prices.
- Trained and evaluated the initial global `LIGHTGBM_V1` model using a recursive 28-day validation forecast.
- Trained the initial global `XGBOOST_V1` model under the identical frozen data, feature, and recursive-validation protocol.
- Formally compared all four validation methods, their horizon behavior, feature-group gain patterns, and ML resource trade-offs without training another model.
- Froze the controlled XGBoost feature-group ablation protocol for the next experiment.
- Reused FULL_V1 and trained the three frozen reduced XGBoost variants under the same recursive validation protocol.
- Formally selected and froze `XGBOOST_V1` + `FEATURE_SET_V1` / `FULL_V1` from validation-only evidence.
- Froze the lost-sales inventory simulation, minimum-stock and forecast-based reorder policies, human approval workflow, and database requirements without executing the experiment.
- Retrained the validation-selected XGBoost configuration once through `d_1913`, generated and hashed all 40,236 fixed-origin TEST forecasts before loading TEST actuals, then executed both frozen inventory policies.

What we learned:

- `CA_1` + `FOODS` contains exactly 1,437 item-store series across `FOODS_1`, `FOODS_2`, and `FOODS_3`.
- The frozen 28-day windows are train `d_1`–`d_1885`, validation `d_1886`–`d_1913`, and test `d_1914`–`d_1941`.
- No observed M5 zero sale proves zero demand or zero inventory.
- On validation, the 28-day Moving Average outperformed Seasonal Naive: MAE 1.438625 vs 1.739785, RMSE 2.726401 vs 3.357394, and WAPE 68.366443% vs 82.678226%.
- The 28 validation days contained 81 SKUs with zero total actual sales, so their per-SKU WAPE is undefined rather than treated as zero.
- FEATURE_SET_V1 contains 25 model features across 2,668,509 train rows; tests confirm features cannot see their own target or future sales.
- `LIGHTGBM_V1` completed 400 deterministic CPU trees in 49.370 seconds. Its validation MAE/RMSE/WAPE were 1.523283 / 2.730151 / 72.389572%: better than Seasonal Naive, but not the 28-day Moving Average reference (1.438625 / 2.726401 / 68.366443%).
- Recursive forecasts were created before validation actuals were loaded; TEST sales values remain unread, unforecast, unscored, unsummarized, and unplotted.
- `XGBOOST_V1` achieved validation MAE/RMSE/WAPE of 1.402449 / 2.568234 / 66.647316%. It beat Seasonal Naive, the Moving Average (2.515% MAE/WAPE and 5.801% RMSE improvement), and `LIGHTGBM_V1` (7.932% MAE/WAPE and 5.931% RMSE improvement).
- XGBoost took 109.747 seconds and its ignored JSON artifact is 93.565 MiB, versus LightGBM's 49.370 seconds and 2.447 MiB. Performance and resource cost remain separate considerations.
- `XGBOOST_V1` + `FEATURE_SET_V1` / `FULL_V1` was selected on validation and then evaluated once on held-out TEST in P12; it remains frozen and TEST may not be reused for tuning.
- Recent rolling-demand features account for 93.146% of LightGBM and 95.527% of XGBoost normalized gain. This is descriptive model behavior, not evidence that the other features are unnecessary.
- FULL_V1 (25 features) remains lowest on validation WAPE/MAE/RMSE. The best reduced model, NO_PRICE (20), worsens WAPE by 0.552%; calendar/event removal and the 11-feature demand/product model worsen it by 2.401% and 2.448%.

What happens next: run end-to-end verification, UX polish, integration tests, and consolidate final experiment evidence. TEST remains final-evaluation evidence only and must not drive any tuning.

## Roadmap

| Phase | Status |
| --- | --- |
| P0 Topic selected and roadmap reviewed | 🟢 **DONE** |
| P1 Repository + environment + long-term memory | 🟢 **DONE** |
| P2 Retail dataset candidate audit | 🟢 **DONE** |
| P3 Official dataset strategy + architecture decisions | 🟢 **DONE** |
| P4 M5 acquisition + formal local schema audit | 🟢 **DONE** |
| P5 Subset + forecast horizon + chronological split freeze | 🟢 **DONE** |
| P6 Naive / Moving Average baselines | 🟢 **DONE** |
| P7 Time-series feature engineering | 🟢 **DONE** |
| P8 LightGBM forecasting | 🟢 **DONE** |
| P9 XGBoost forecasting | 🟢 **DONE** |
| P10 Forecast comparison + model selection | 🟢 **DONE** |
| P11 Inventory simulation protocol | 🟢 **DONE** |
| P12 Minimum-stock vs forecast-based reorder experiment | 🟢 **DONE** |
| P13 MySQL + FastAPI core | 🟢 **DONE** |
| P14 Inventory/product/supplier modules | 🟢 **DONE** |
| P15 Sales ingestion + forecasting API | 🟢 **DONE** |
| P16 Inventory decision engine | 🟢 **DONE** |
| P17 React dashboard + integration | 🟢 **DONE** |
| P18 Testing + final experiments | 🟡 **IN_PROGRESS** |
| P19 Thesis report + defense package | ⚪ **TODO** |

## Current Task

`P18-AUTH-UX-HOTFIX` is **DONE**. The additive `a91c2e6f4b20` authentication-session migration is applied to local MySQL and Alembic current/heads/check agree at that revision. A marker-cleaning live local-MySQL test verified a public inventory-staff registration (201), non-plaintext scrypt hash, persisted active session, cookies, `/api/auth/me`, logout revocation, and cookie expiry.

Registration now requires at least 8 characters and one ASCII uppercase letter, consistently checked in the backend contract, a shared helper, the frontend indicators, and automated tests. The login/register UI is one stable component: it preserves `/login` and `/register`, waits for a genuine 780 ms 3D coin flip before URL navigation, follows direct/back/forward navigation, shifts focus to the visible face, and prevents focus/submission on the hidden form. Its light canvas, dark navy coin, attached animated gradient ring, compact navy brand container, soft focus treatment, responsive form geometry, reduced-motion fallback, and restrained interaction feedback are limited to authentication screens. No model, inventory, forecast, purchase-order, or demo-data behavior changed.

`scripts/db/verify_auth_live.py` creates and cleans only a unique temporary account for live proof. `scripts/db/provision_manager.py --email ... --full-name ...` prompts locally for a password, validates the same registration policy, and creates or updates a manager only in development/local/test environments; it stores no credential in code or the repository.

### P18 Auth Coin Render Hotfix

The original single conic-gradient ring was an opaque 3D plane. When the coin rotated, that plane could be composited in front of the register face and obscure the form. The implementation now uses two `backface-visibility: hidden` ring faces, each masked with a transparent center and attached to its respective side of the coin. The outer authentication canvas is restored to dark navy `#0F172A`, with restrained navy/blue illumination and an integrated slate-navy brand pill. Form content width, card padding, and gaps were tightened so the register form has increased clearance inside the desktop circle; the existing short/mobile rounded-card fallback remains.

Frontend lint/build and an HTTP preview-health check pass. Browser automation is unavailable in this environment, so visual flip verification remains **IN_PROGRESS**: capture the Login front face and the Register back face after a flip before treating this rendering repair as fully accepted.

### P18 Auth Sliding-Card Redesign

The circular/3D coin concept has been deliberately replaced, not repaired further. The stable `/login` and `/register` component now renders a rounded 960-by-590px-class white card on the existing dark navy canvas. Login presents the gradient welcome panel on the left and the form on the right; Register reverses that composition. A transition-state overlay expands from its active half to cover the full card, swaps the visible/interactive form only at the midpoint, then contracts to the destination half. Its `transitionend` event, rather than overlapping delays, advances the state machine; reduced-motion and compact layouts swap directly.

Both actual forms remain mounted, with inactive controls disabled and hidden from interaction. The established password policy, confirmation check, backend API calls, session restoration, redirect behavior, inline errors, and route/history synchronization are preserved. Google, Facebook, and GitHub are disabled visual placeholders with accessible “coming soon” labels only. Responsive CSS uses the horizontal layout on desktop and a single-column card on small or short screens.

Lint/build pass, but visual acceptance remains **IN_PROGRESS** because no browser automation surface is available. The user must inspect Login, the full-gradient midpoint, and Register before accepting the redesign.

### P18 Premium Workspace Refinement

The operational workspace now shares the authentication surface's restrained blue, shadow, radius, focus, and motion language without changing operational behavior. The sidebar's horizontal scroll defect was traced to full-width route rows being translated on hover and to collapsed labels being rendered inside the scrollable navigation tree. Hover no longer moves route rows; the navigation has a bounded horizontal layout; and collapsed-only labels are fixed-position portal overlays outside that tree. Tooltips remain useful without increasing sidebar `scrollWidth`.

The authenticated profile is now an avatar-led capsule: a prominent 50px white `UserRound` circle overlaps a lighter-navy tail with the real authenticated name, normalized role, and operational logout button. It is not a fake account control. During the 200ms desktop collapse transition, only the centered white avatar remains; the name, role, tail, and logout control retract. The mobile drawer restores the readable capsule and real logout control. Shared component polish adds controlled button press/lift feedback, thin blue input focus rings, calmer table-row hover, and refined panel/modal shadows while preserving table scrolling and all existing routes, API calls, forecast behavior, inventory rules, and data boundaries.

Frontend lint and production build pass. Browser automation is unavailable in this environment, so the requested screenshots of the expanded capsule and collapsed white-avatar-only sidebar remain the manual acceptance evidence.

### P18 Targeted UI Repair

The approved workspace and authentication designs remain intact. The desktop collapsed-sidebar regression came from the inherited broad selector `.collapsed nav span`, which hid the `Tooltip` span wrapper around each `NavLink`, rather than only its text. The sidebar repair restores each wrapper/link in desktop collapsed state while the existing explicit label and group-label rules continue to hide text. All eight route icons, active state, collapsed portal tooltips, white-avatar-only footer, and floating collapse control are preserved.

The Inventory Insight modal now gives its compact demand chart a scoped 20px internal inset. Its heading no longer inherits negative page-panel margins; it has a modest divider and comfortable heading-to-chart spacing without affecting the main Forecasts chart, forecast data, or horizon behavior. Register no longer renders the disabled social-login placeholder block; Login retains the shared disabled Google/Facebook/GitHub controls and coming-soon label. The centered register form therefore rebalances naturally without changing its sliding-card transition or authentication logic.

Frontend lint and production build pass. Browser automation is unavailable, so visually inspect the collapsed eight-icon sidebar and the 7-/28-day Inventory Insight chart before final acceptance.

### P17 Decision UX

Forecasts now resolves the latest persisted forecast per selected product, restores its product and horizon from URL search parameters, and displays the actual 28 observed sales days before the persisted origin with future expected demand; navigation never triggers inference. Inventory Insights now has a selected-product decision panel that combines current/incoming stock, inventory position, lead-time demand, safety-stock buffer, reorder/target stock, recommended order, an actual coverage comparison, calculation explanation, and the same reusable demand chart. This is presentation only: no backend formula, database schema, frozen model, TEST boundary, or automatic-purchasing behavior changed.

### P17 Final Presentation Refinement

Major operational panels now have a structured, typography-led header hierarchy. Tooltip visibility is event-managed so it closes on mouse leave, blur, Escape, and modal unmount. Dialogs are centered inside the main workspace on desktop rather than across the fixed sidebar; their clipped, rounded scroll containers use integrated scrollbars. These are frontend-only usability changes and preserve existing routes, contracts, decisions, forecasts, model behavior, and demo data.

### P17 Visual Design Polish

The final P17 presentation pass replaces strong blue header bands with light, structured cards, restrained borders, subtle shadows, and typography-led section headers. It adds Inter Variable, a grouped premium sidebar, and a floating chevron-only collapse handle. Blue remains a controlled accent for actions, active navigation, focused controls, charts, and key emphasis; no behavior, API contract, forecast, inventory calculation, or dataset treatment changed.

### P17 Sidebar Layout Fix

The grouped sidebar now uses full-width, 42px navigation controls with compact group spacing, full-row active treatment, and 16px right-hand corners. Collapsing hides only explicit text labels: all eight Lucide navigation icons remain mounted, centered, keyboard/click reachable, and route tooltips remain available. The floating chevron keeps its accessible aria label but no longer has a visible tooltip balloon. Mobile retains the off-canvas drawer with all labels visible. This frontend-only repair changes no route, API, business rule, forecast, inventory calculation, model, or data boundary.

### P17 Premium UX Pass

The floating collapse control now has a stable 92px upper-edge anchor and dedicated navigation clearance rather than following sidebar height, eliminating the former route-row overlap. A non-interactive, clearly labeled Demo Manager / Demo workspace footer is pinned below independently scrollable navigation; its avatar remains visible when collapsed and the full truthful demo label returns in the mobile drawer. Shared frontend tokens consolidate spacing, radii, surfaces, text hierarchy, borders, shadows, and transition timing across existing cards, controls, tables, badges, and modals. No authentication claim, backend behavior, API, schema, model, data value, or decision rule changed.

### P17 Animated UX and Authentication

The application now has real cookie-session authentication: public registration grants only `INVENTORY_STAFF`; protected write operations require `MANAGER` or `ADMIN`; password hashes use scrypt; opaque HttpOnly session cookies are backed by revocable, expiring database records; and CSRF verification protects authenticated state changes. Login/Register are dedicated routes with an accessible responsive circular flip interface and no operational shell. The sidebar now reflects the authenticated name/role and performs real logout. Existing operational routes are server-protected, not merely hidden in the browser.

## Last Stable Checkpoint

`CHECKPOINT-017` — Human-friendly polished React dashboard, real local thesis-demo workflow, and historical-to-forecast visualization integrated with FastAPI

## Next Exact Step

`NEXT-018` — End-to-end verification, UX polish, integration testing, and final experiment/evidence consolidation.

Do not re-open model selection, change feature/model/protocol values, or tune against TEST. The current deployed thesis artifact is M5-specific; a real supermarket requires retraining on its own POS/product/calendar/price context.

## Known Blockers

`P18-TARGETED-UI-REPAIR` needs user screenshots of the collapsed sidebar with all eight route icons and the padded Inventory Insight chart for final visual acceptance. Browser automation is unavailable in the current environment; this does not block source, lint, build, or Git verification.
