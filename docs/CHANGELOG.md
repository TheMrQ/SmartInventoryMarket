# Changelog

All notable project changes are recorded here chronologically.

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
