# Changelog

All notable project changes are recorded here chronologically.

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
