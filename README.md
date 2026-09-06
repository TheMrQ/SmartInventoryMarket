# Smart Inventory Market

Graduation thesis project: **Development of an Intelligent Supermarket Inventory Management and Product Demand Forecasting System Using Machine Learning**.

## Goal

This single-store MVP helps a small or medium supermarket turn historical sales into demand forecasts and then into inventory-aware reorder recommendations. It is not a generic ERP.

Core flow:

`Historical sales → demand forecasting → future demand → current inventory + lead time + safety stock → stockout/overstock risk → reorder recommendation`

## Research Direction

The thesis will compare naive and moving-average baselines with LightGBM and XGBoost; assess lag, rolling, calendar, event, and price features; and compare a traditional minimum-stock rule with forecast-based replenishment in a documented inventory simulation.

## Planned Stack

- React + Vite frontend
- FastAPI backend
- PostgreSQL with SQLAlchemy and Alembic
- Pandas, scikit-learn, LightGBM, and XGBoost for reproducible script-based ML

## Structure

- `backend/` — FastAPI application
- `frontend/` — React/Vite environment scaffold
- `ml/` — future data, features, models, evaluation, and inventory simulation modules
- `scripts/` — official future training/evaluation entry points
- `configs/` — reproducible run configuration
- `data/`, `artifacts/`, `reports/` — generated-data, model-output, and report locations
- `docs/` — permanent project memory and development record

## Setup

1. Create and activate Python 3.12 virtual environment: `python -m venv .venv`.
2. Install backend/ML dependencies: `.\\.venv\\Scripts\\python -m pip install -r requirements.txt` (PowerShell).
3. Install frontend dependencies: `cd frontend; npm install`.
4. Verify backend: `.\\.venv\\Scripts\\python -m pytest`.
5. Verify frontend: `cd frontend; npm run build`.

## Current Status

Project initialization only. See [project status](docs/00_project_status.md) for the authoritative roadmap and next step.

## Dataset and Reproducibility

The M5 Forecasting - Accuracy raw dataset is **not** stored in this repository and has not been downloaded or audited during initialization. Official future ML training will be script-based and must record configuration, seed, dataset version/subset, time split, features, parameters, metrics, Git commit, and artifact paths. No model results are claimed yet.
