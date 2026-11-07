# Troubleshooting and Recovery

## 2026-11-07 — P24 reconciliation found five historical scenario stock rows without actor attribution — OPEN FOR P24 EVIDENCE

**Finding:** The current MySQL scenario has 37 stock transactions attributed to user ID 4 and five with a null actor, while all four reviewed recommendations are attributed to user ID 4.

**Containment:** P24-02 is read-only and does not rewrite historical audit evidence. New manual sale/receipt actions must be checked for server-bound actor attribution; any failure becomes a separate integrity fix rather than a data cleanup.

## 2026-11-07 — Products search lost focus after one character — RESOLVED, BROWSER VERIFICATION PENDING

**Symptom:** Typing changed the query key immediately. While the new request loaded, `ProductsPage` returned a full-page loading component, unmounting the focused search input.

**Resolution:** Search input state is now independent from its 300 ms debounced query value. React Query retains previous product data during fetches; the page shows a small live “Updating products…” status, keeps the table/input mounted, and distinguishes successful no-results from API failures.

**Verification:** Unit-level regression coverage checks the debounce value, SKU/name request parameters, and retained-table transition model. Frontend automated checks pass; P24 must still provide live browser focus/network evidence.

## 2026-11-06 — P22 scenario retry attempted a duplicate linked draft PO — RESOLVED

**Symptom:** The first scenario rerun regenerated recommendations and attempted to insert its fixed linked-draft PO number, which MySQL rejected through the unique PO-number constraint.

**Cause:** The original idempotency sequence checked the linked PO only after regenerating recommendation workflow state, so it was not truly read-only after a completed manifest.

**Resolution:** `setup_m5_supermarket_scenario.py` now checks for the named scenario immediately after actor preflight. An existing manifest is validated and summarized without entering any write path; incomplete existing manifests fail safely. Isolated tests cover this destructive-scenario guard. The failed insert was rolled back; pre-existing audit rows are retained rather than deleted.

## 2026-11-06 — P23 squared-error recursive candidate emitted negative demand — RESOLVED BY DISQUALIFICATION

**Symptom:** The predeclared `V2_SQUARED_REGULARIZED` XGBoost candidate emitted a negative value during its recursive validation forecast.

**Cause:** A squared-error regression objective is unconstrained and can produce negative continuous demand estimates, unlike the count-focused Poisson candidates.

**Resolution:** The runner rejects non-finite/negative predictions before scoring and never clips them. It records the candidate as disqualified in the aggregate validation report while allowing the other predeclared candidates to finish before validation actuals are opened. The frozen V1 model and application default are unchanged.

## 2026-11-01 — P20 audit found actor-attribution and recommendation-to-PO gaps — RESOLVED IN P21

**Symptom:** Operational writes can omit `created_by_user_id`/`approved_by_user_id`/`reviewed_by_user_id`, and a manager client can submit another existing user ID. A reviewed recommendation also stops before any linked purchase order.

**Root cause:** The operational router dependency correctly verifies an authenticated `MANAGER`/`ADMIN`, but route handlers do not pass that authenticated identity into services. Actor IDs remain optional request fields. The schema has no recommendation-to-purchase-order relationship or duplicate-order guard.

**Current containment:** Manager-only server authorization, CSRF checks, transactional inventory rules, and human review remain active. P20 changed no data or behavior; its full evidence is in `docs/implementation/P20_functional_audit.md`.

**Resolution:** P21 binds adjustment, operational-sale, purchase-order mutation/receipt, and recommendation-review actors to the authenticated server user; spoofed payload actor fields are ignored. Revision `d4e9a6c21f35` adds the durable operational-sale idempotency ledger and nullable one-to-one recommendation-to-PO link. A manager must explicitly confirm conversion of an appropriately reviewed recommendation to one linked draft PO; duplicate conversions are rejected by the database. The flow does not change on-hand stock until receipt. Isolated regression tests and the local MySQL additive migration/head/check pass. Browser workflow evidence remains a P24 acceptance item.

## 2026-10-10 — P18 Dashboard glyph still appeared optically left in the common icon frame — IMPLEMENTED, MANUAL VISUAL CHECK PENDING

**Symptom:** User visual evidence still showed the collapsed Dashboard glyph left of Products, Inventory, Suppliers, and the remaining route icons after their parent layout was standardized.

**Cause:** Static source inspection shows no Dashboard-specific layout: the common route map gives all entries the same tooltip wrapper, link geometry, and centered 19px icon frame. The former `LayoutDashboard` artwork uses unequal diagonal tiles, which can create a small-icon optical imbalance even when its SVG box is centered. Browser inventory is empty, so no rendered DOM rectangle comparison is available.

**Resolution:** Replaced only the Dashboard artwork with Lucide `LayoutGrid`, a four-equal-cell glyph that is horizontally balanced in the existing frame. No transform, per-route offset, wrapper width, active-ribbon geometry, or other icon position changed.

**Verification:** Frontend lint and production build pass. Manually compare Dashboard in active and inactive collapsed states with Products and Inventory; do not treat this source-level analysis as pixel-perfect browser measurement.

**Prevention:** First establish a shared frame/route structure, then choose a symmetric glyph for a persistent small-scale optical imbalance. Do not compensate by moving unrelated navigation icons.

## 2026-10-10 — P18 modal backdrop excluded the fixed sidebar and Dashboard icon lacked a common frame — RESOLVED, MANUAL VISUAL CHECK PENDING

**Symptom:** Opening an application modal dimmed only the main workspace; the sidebar, logo, profile/avatar, active ribbon, and floating collapse control stayed sharp. In collapsed mode, the `LayoutDashboard` glyph could also appear visually left of the remaining navigation icons.

**Cause:** A late `.app-shell .modal-backdrop` rule explicitly started the backdrop at `left: 256px` (or `78px` when collapsed), while the modal remained inside the workspace subtree. Navigation SVGs were direct inline flex children, so no explicit common frame constrained their rendered box/baseline behavior.

**Resolution:** `Modal` now portals to `document.body` and receives collapsed state through context. Its full-screen backdrop sits above the application shell, while its grid padding reserves the current sidebar width only to position the dialog over the workspace. The shell is inert while the dialog is open, and tooltip portals remain lower in the stack. Each navigation SVG is wrapped in the same fixed 19px centered grid frame, preserving the established sidebar rail and active ribbon.

**Verification:** Frontend lint and production build pass. Browser inventory is empty, so live modal opening/closing, screenshot capture, route clicking, and DOM center measurements could not run. Manually inspect an expanded and collapsed modal, then capture the requested collapsed-sidebar screenshot.

**Prevention:** Treat backdrop coverage and dialog alignment as independent concerns. Use a portal for cross-shell modal layering, and make all icon hit/visual boxes explicit before applying icon-specific corrections.

## 2026-10-10 — P18 collapsed active route rendered as two overlapping blue blocks — RESOLVED, MANUAL VISUAL CHECK PENDING

**Symptom:** In collapsed mode, an active Dashboard row could look like a rounded blue pill inside the sidebar plus a visibly separate rounded blue protrusion on its right.

**Cause:** The active `NavLink` kept both right-side rounded corners while the independently measured, 11px sidebar-level ribbon overlay began exactly at its right edge. The two same-colored surfaces therefore met with incompatible corner geometry. A row-local active hover brightness could also differ from the overlay's blue.

**Resolution:** Desktop-collapsed active rows now have only left-side rounded corners; their square inner-right edge meets the overlay to form one continuous `#2563EB` ribbon. Collapsed active hover/focus removes row-local brightness/shadow while preserving primary blue; the overlay provides the restrained single shadow. The navigation rail, icon centers, ribbon measurement, expanded styling, and inactive slate hover behavior are unchanged. The collapsed 50px avatar also has an isolated 2px gradient perimeter with a white inset, so no profile layout geometry changes.

**Verification:** Frontend lint and production build pass. No browser surface is available for the required screenshot or visual route checks. Manually confirm `LayoutDashboard`, the seamless active ribbon, the 11px protrusion, and the centered gradient-ring avatar.

**Prevention:** When a decorative active-state extension is a sibling overlay, make the adjoining active element's inner edge square and keep hover effects visually consistent across the entire combined surface.

## 2026-10-10 — P18 first collapsed alignment pass left group-local centering — IMPLEMENTED, MANUAL VISUAL CHECK PENDING

**Symptom:** User screenshot evidence showed the logo/avatar and first route close to the desired axis, while Management and Intelligence icons still sat visibly right of that axis.

**Cause:** The prior rule centered icons inside tooltip wrappers whose widths continued to resolve within individual padded grid-group contexts. `justify-content: center` therefore centered against a local parent, not the full sidebar rail.

**Resolution:** The desktop collapsed nav now has no outer inline padding; each group is a full-width border-box grid with centered items; each direct tooltip wrapper has the same symmetric `calc(100% - 24px)` width; and each route link fills that wrapper. This derives every icon's center from one sidebar-width-based track without manual translation.

**Verification:** Frontend lint and production build pass. Browser inventory is empty, so `getBoundingClientRect()` center measurements and collapsed-route click checks could not run. User must inspect the requested full collapsed-sidebar screenshot before accepting pixel alignment.

**Prevention:** Do not regard `justify-content: center` as sufficient until every ancestor width and padding context is shared. For grouped navigation, make the group and wrapper rail explicit.

## 2026-10-10 — P18 active sidebar route was restyled as inactive on hover — RESOLVED

**Symptom:** Hovering the current route changed its blue row to dark slate while the collapsed active ribbon remained blue.

**Cause:** The generic `.app-shell .sidebar nav a:hover` background rule applied after the base active treatment and had equal or greater effective cascade weight for the hover state.

**Resolution:** Added an explicit, more specific active base/hover/focus/focus-visible rule that holds `#2563EB`, white text, and zero transform. Its interaction feedback is only `brightness(1.06)` plus a soft blue shadow; inactive hover styling remains unchanged.

**Verification:** Frontend lint and production build pass. This scoped visual regression does not require a new manual screenshot.

**Prevention:** When generic interaction rules coexist with selected-state rules, define explicit selected-hover and selected-focus states rather than relying on source order.

## 2026-10-10 — P18 collapsed sidebar used independent alignment contexts — IMPLEMENTED, MANUAL VISUAL CHECK PENDING

**Symptom:** The collapsed logo mark, route icons, and footer avatar could appear to have slightly different horizontal centers, even after route icons were restored.

**Cause:** The brand retained expanded-state inline padding/gap, navigation centered inside a padded scroller, and the avatar used a separate footer width/margin rule. The active row also could not safely protrude from the horizontally clipped nav scroller.

**Resolution:** Desktop collapsed rules now center the brand mark from the sidebar width with no residual gap/padding, retain symmetric navigation padding for a shared centered rail, and keep the existing auto-margin avatar center. A measured sidebar-level ribbon overlay follows the active row vertically and extends 11px outward without living in the scrolling nav container.

**Verification:** Frontend lint and production build pass. No browser surface is available; manually inspect the complete collapsed sidebar and confirm logo/icon/avatar centers match within the requested visual tolerance, the active ribbon protrudes without shifting the icon, and no horizontal scrollbar appears.

**Prevention:** Center collapsed components from the same parent dimension rather than compensating with fixed offsets. Put decorative overflow outside the scrollable navigation element.

## 2026-10-10 — P18 collapsed navigation wrappers were hidden by a broad span selector — IMPLEMENTED, MANUAL VISUAL CHECK PENDING

**Symptom:** Collapsing the desktop sidebar left the brand mark and profile avatar visible but removed every route icon and link.

**Cause:** `.collapsed nav span { display: none; }` matched not only route-label spans, but also the current `Tooltip` span wrapper around each `NavLink`.

**Resolution:** Added a desktop collapsed-sidebar rule that restores each `.tooltip` wrapper and its direct route link while retaining the existing explicit text-label hiding. The route icons, active treatment, keyboard/click behavior, and portalled tooltips are no longer affected by the broad legacy declaration.

**Verification:** Frontend lint and production build pass. No browser surface is available; manually verify all eight icons and route changes after collapsing.

**Prevention:** Collapse selectors must target semantic text classes such as `.nav-label` and `.nav-group-label`, never generic inline elements that may be component wrappers.

## 2026-10-10 — P18 Inventory Insight chart header inherited page-panel negative margins — IMPLEMENTED, MANUAL VISUAL CHECK PENDING

**Symptom:** The compact demand outlook heading in the Inventory Insight modal sat too close to the panel edges.

**Cause:** The nested `.decision-chart .demand-forecast > header` inherited negative margins intended for top-level page panels.

**Resolution:** Scoped a 20px inset and zero-negative-margin header treatment to the decision modal chart only, retaining its rounded white panel, responsive chart, divider, and legend.

**Verification:** Frontend lint and production build pass. Manually review both 7- and 28-day saved forecasts in the insight dialog when a browser is available.

**Prevention:** Nested modal panels must opt out of page-level negative header-margin patterns with a local layout rule.

## 2026-10-10 — P18 sidebar horizontal scrollbar during navigation hover — IMPLEMENTED, MANUAL VISUAL CHECK PENDING

**Symptom:** A horizontal scrollbar could appear above the fixed sidebar profile, especially while hovering full-width navigation rows.

**Cause:** Later sidebar styling translated full-width route rows by 2px on hover. Collapsed navigation also kept tooltip content in the scrollable navigation hierarchy, so a visible tooltip could contribute to its layout width.

**Resolution:** Removed physical route translation in favor of color/background/inset-shadow feedback, bounded navigation's horizontal layout while preserving vertical scroll, and made collapsed-only navigation tooltip content a fixed portal outside the navigation tree. The profile is not used as an overflow workaround; it is a separate fixed footer capsule.

**Verification:** Frontend lint and production build pass. Browser automation is unavailable, so inspect expanded and collapsed sidebars manually: hover every route, confirm no horizontal scrollbar, confirm a collapsed tooltip appears beside its icon, and confirm the white avatar-only collapsed footer.

**Prevention:** Diagnose scroll-width contributors before applying overflow masking. Keep decorative overlays outside scrollable layout containers and avoid translating elements that deliberately fill a constrained width.

## 2026-10-10 — P18 circular authentication rendering issues superseded by sliding-card redesign — IMPLEMENTED, MANUAL VISUAL CHECK PENDING

**Symptom:** The circular 3D authentication concept continued to be visually fragile, including earlier gradient-plane compositing defects.

**Cause:** A coin geometry required stacked front/back forms and decorative 3D planes, making the desired presentation unnecessarily sensitive to browser compositing.

**Resolution:** Replaced the circular UI with a stable two-pane rectangular card. A CSS gradient overlay grows to the full card and contracts to the opposing half; `transitionend` advances an explicit `idle → expanding → retracting → idle` sequence. Forms remain mounted but inactive controls are disabled and hidden. The backend, auth endpoints, sessions, policy, and routes are untouched.

**Verification:** Frontend lint and production build pass. Browser automation remains unavailable, so user inspection of Login, full-gradient transition, and Register is required before visual acceptance.

**Prevention:** Prefer simple 2D overlay composition for split-card transformations. Treat lint/build as code checks only, and perform a real viewport/interaction review for animation work.

## 2026-10-10 — P18 gradient ring obscured the Register face — IMPLEMENTED, MANUAL VISUAL CHECK PENDING

**Symptom:** After the working 3D flip reached Register, a large opaque blue gradient disc covered most of the form.

**Cause:** The original `.auth-ring` was a full conic-gradient plane with a 3D translation. On the reverse side of the parent rotation, compositing could place that opaque plane in front of the register card.

**Resolution:** Replaced the single plane with separate front/back decorative ring faces. Each has `backface-visibility: hidden`, the appropriate 3D transform, and a radial mask that leaves its center transparent, so only the moving perimeter can render. Restored the requested dark authentication canvas and increased form-clearance geometry.

**Verification:** Frontend lint/build and local preview HTTP health succeeded. Chromium/Edge/in-app browser automation was unavailable in this environment, so user screenshots of Login and flipped Register are still required before visual acceptance.

**Prevention:** A successful build cannot prove CSS 3D compositing. Test both faces after a full flip in a real Chromium browser whenever the environment provides one.

## 2026-10-10 — P18 local authentication migration was pending — RESOLVED

**Symptom:** Repository code included Alembic revision `a91c2e6f4b20` for `auth_sessions`, while local MySQL still reported revision `8ac7d44590e3`; `alembic check` therefore reported that the target database was not up to date.

**Cause:** The prior authentication implementation was committed before the additive migration was applied to the local thesis database.

**Resolution:** Ran `alembic upgrade head` without dropping, resetting, or deleting existing data. `alembic current`, `alembic heads`, and `alembic check` now all report `a91c2e6f4b20` with no drift. The marker-cleaning `scripts/db/verify_auth_live.py` then verified actual local-MySQL registration, password hashing, server session persistence, cookies, `/api/auth/me`, and logout/revocation.

**Prevention:** After any committed Alembic revision, run current/heads/check against the configured local database before reporting the feature complete. Use the live verifier for cookie-session claims; isolated SQLite tests alone are insufficient.

## 2026-10-09 — P15 multipart CSV route required an undeclared runtime dependency — RESOLVED

**Symptom:** FastAPI refused to register `/api/sales/import` because multipart form parsing support was not installed in the local environment.

**Cause:** `python-multipart`, required by FastAPI `UploadFile`, was absent from the original web runtime requirements.

**Resolution:** Added `python-multipart` to `requirements.txt`, installed it only in the project virtual environment for verification, and added isolated upload tests.

**Prevention:** Any FastAPI endpoint using multipart/form-data must declare its parser dependency in runtime requirements and be import-smoke-tested before full tests.

## 2026-10-09 — P14 MySQL smoke cleanup rejected a nested target-table delete — RESOLVED

**Symptom:** The first successful live P14 API smoke flow reached complete receipt, but cleanup failed with MySQL error 1093 while deleting `purchase_order_items` through a subquery on the same table.

**Cause:** MySQL does not permit that target-table/subquery delete form.

**Resolution:** `scripts/db/smoke_p14.py` now fetches its uniquely marked product, purchase-order, and line IDs first, then deletes in explicit foreign-key-safe order. The one marker run was removed with the corrected routine; a second full live smoke run and no-marker-data verification passed.

**Prevention:** Live smoke cleanup must use exact marker IDs and MySQL-compatible deletes. Do not use broad cleanup patterns or leave operational test records behind.

## 2026-10-01 — P13 Alembic MySQL downgrade initially rejected an FK-supporting index

**Symptom:** A safe `alembic downgrade base` on the empty `smart_inventory_market` development schema failed with MySQL error 1553: an index on `stock_transactions` could not be dropped because it supported a foreign key.

**Cause:** Alembic autogeneration emitted standalone index drops before dropping child tables. MySQL keeps an FK-supporting index mandatory until that foreign key/table is removed.

**Resolution:** The initial migration's downgrade now drops child tables in dependency order and lets MySQL remove each table's indexes together with the table. The schema was confirmed empty before the test; the corrected downgrade/upgrade cycle was then rerun.

**Prevention:** Run a safe downgrade/upgrade test for MySQL migrations before marking a migration checkpoint complete. Do not manually drop FK-supporting indexes first.

## 2026-09-17 — Kaggle CLI authentication required for M5 acquisition — RESOLVED

Symptom:

`.\\.venv\\Scripts\\kaggle.exe competitions files m5-forecasting-accuracy` returned `Authentication required to call the Kaggle API.`

Root cause:

The project virtual environment had no authenticated Kaggle CLI session.

Fix:

User ran `.\\.venv\\Scripts\\kaggle.exe auth login` and completed its browser-based OAuth flow outside the repository. No token, `kaggle.json`, or `.env` credential was added to the repository.

Verification:

The competition file-list command successfully returned the five official M5 files.

Files changed:

`requirements-dev.txt`, `docs/00_project_status.md`, `docs/05_experiments.md`, `docs/06_dataset.md`, `docs/04_troubleshooting.md`, `docs/CHANGELOG.md`.

Prevention:

Use a harmless metadata/file-list call before every protected Kaggle acquisition and never store credentials in repository files.

## 2026-09-17 — M5 download forbidden after successful Kaggle authentication — RESOLVED

Symptom:

`.\\.venv\\Scripts\\kaggle.exe competitions download m5-forecasting-accuracy -p data\\raw\\m5` returned `403 Client Error: Forbidden for url: https://api.kaggle.com/v1/competitions.CompetitionApiService/DownloadDataFiles`.

Root cause:

Authentication is valid because the file listing succeeds, but the authenticated account does not currently have download access. Competition-rule acceptance or account access confirmation is required.

Fix:

User resolved competition access outside the repository and successfully downloaded the 45.785 MiB M5 archive to `data/raw/m5/`.

Verification:

The archive extracted to the five official files under `data/raw/m5/`; Git confirms the archive and all raw CSVs remain ignored.

Files changed:

`docs/00_project_status.md`, `docs/04_troubleshooting.md`, `docs/05_experiments.md`, `docs/06_dataset.md`, `docs/CHANGELOG.md`.

Prevention:

Treat a successful file list as authentication verification only; verify download authorization separately before creating an audit plan.

## 2026-10-09 — Optional UI demo setup reports unavailable frozen prerequisites

Symptom:

`scripts/db/setup_ui_demo.py` stops before preparing the local dashboard state.

Root cause:

The optional demo requires the ignored frozen XGBoost artifact, M5 calendar metadata, source sales/price files, and local MySQL configuration. They are intentionally not committed with the application.

Fix:

Restore the local project prerequisites from the documented thesis environment, then run `.\.venv\Scripts\python.exe scripts\db\setup_ui_demo.py` again. Do not replace missing prerequisites with synthetic predictions or TEST demand.

Verification:

The script prints its persisted forecast run, engine-derived risk distribution, incoming PO quantity, and adjustment-audit count. Rerunning it should not add another forecast, PO, active recommendation, or adjustment when the prepared state is unchanged.

Prevention:

Treat the utility as optional/local-demo setup only. Keep raw M5 files, model artifacts, `.env`, and database dumps ignored.

## Problem Record Template

## 2026-09-21 — Ablation-summary WAPE mapping corrected

Symptom:

The first ablation report rendered reduced-variant WAPE cells as blank despite successful model training and recursive prediction generation.

Root cause:

The shared metric utility returns the aggregate field as `WAPE_percent`, while the ablation result schema requires `WAPE`.

Fix:

Mapped the shared field explicitly to `WAPE`, added a unit test, and regenerated reports from the already saved ignored XGBoost artifacts using recursive inference only; no model was retrained.

Verification:

All four variants have finite MAE, RMSE, and WAPE values in the tracked result table; the full pytest suite passes.

Prevention:

Normalize shared metric names at report boundaries and test the output schema rather than assuming identical field names.

## YYYY-MM-DD — Problem title

Symptom:

Root cause:

Fix:

Verification:

Files changed:

Prevention:

# Context Reset Recovery

When an AI agent loses context:

1. Read `AGENTS.md`.
2. Read `docs/00_project_status.md`.
3. Read the latest `CHANGELOG` entries.
4. Check Last Stable Checkpoint.
5. Read Next Exact Step.
6. Read Known Blockers.
7. Run verification commands.
8. Continue from repository state.
9. Do not redo tasks already marked `DONE` unless verification fails.
## 2026-11-01 — P22 scenario apply requires an existing manager/admin — BLOCKED

**Symptom:** The explicit `scripts/db/setup_m5_supermarket_scenario.py --apply` preflight stopped before any scenario write with `P22 apply requires an existing active manager or admin; it will not create a user`.

**Root cause:** P21 correctly requires synthetic adjustments, recommendation reviews, POs, and receipts to retain a real server-side actor. The local database has no active manager/admin suitable for this scenario. Creating an account automatically would bypass the ownership and password boundary.

**Safe resolution:** The project owner must run the password-prompting local utility `scripts/db/provision_manager.py --email <manager-email> --full-name <manager-name>`, then rerun the P22 dry-run and explicit `--apply`. Do not supply credentials to an agent, add passwords to repository files, impersonate a staff user, or weaken the P21 actor requirement. No P22 data was imported before this stop.
