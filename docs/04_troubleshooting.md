# Troubleshooting and Recovery

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
