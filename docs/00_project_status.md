# Project Status

Project: Smart Inventory Market

Thesis: Development of an Intelligent Supermarket Inventory Management and Product Demand Forecasting System Using Machine Learning

Overall status: `BLOCKED` — P4 M5 Acquisition and Formal Local Schema Audit

## Quick Human Summary

What we decided:

- M5 is the official forecasting dataset.
- Inventory will be simulated transparently because M5 has no real inventory history.
- MySQL is the application database; MySQL Workbench is its design/admin tool.
- Historical sales can first be imported by CSV; a real deployment should later sync new sales from POS automatically.

Why:

- M5 has real retail provenance and long SKU-level sales history.
- Mixing unrelated sales and inventory datasets would weaken the thesis.
- A deployed supermarket must eventually use its own POS history, not Walmart M5 data permanently.

What happens next: authenticate the Kaggle CLI outside this repository, acquire the real M5 files, audit their actual schema/size, then freeze the store/category/SKU subset, forecast horizon, and time split.

## Roadmap

| Phase | Status |
| --- | --- |
| P0 Topic selected and roadmap reviewed | DONE |
| P1 Repository + environment + long-term memory | DONE |
| P2 Retail dataset candidate audit | DONE |
| P3 Official dataset strategy + architecture decisions | DONE |
| P4 M5 acquisition + formal local schema audit | BLOCKED |
| P5 Subset + forecast horizon + chronological split freeze | TODO |
| P6 Naive / Moving Average baselines | TODO |
| P7 Time-series feature engineering | TODO |
| P8 LightGBM forecasting | TODO |
| P9 XGBoost forecasting | TODO |
| P10 Forecast comparison + model selection | TODO |
| P11 Inventory simulation protocol | TODO |
| P12 Minimum-stock vs forecast-based reorder experiment | TODO |
| P13 MySQL + FastAPI core | TODO |
| P14 Inventory/product/supplier modules | TODO |
| P15 Sales ingestion + forecasting API | TODO |
| P16 Inventory decision engine | TODO |
| P17 React dashboard + integration | TODO |
| P18 Testing + final experiments | TODO |
| P19 Thesis report + defense package | TODO |

## Current Task

P4 is blocked before acquisition. The official Kaggle CLI was installed in the project virtual environment and its harmless competition file-list operation was attempted. Kaggle returned `Authentication required to call the Kaggle API.` No M5 files were downloaded, and no preprocessing, EDA, training, feature engineering, or application features have been performed.

## Last Stable Checkpoint

`CHECKPOINT-003` — Dataset strategy and system architecture decisions frozen

## Next Exact Step

`NEXT-004A` — Authenticate the Kaggle CLI outside this repository, accept the M5 competition rules if prompted, then rerun the M5 acquisition and formal local schema/resource audit.

The required manual action is `.\\.venv\\Scripts\\kaggle.exe auth login` followed by the browser-based OAuth flow. Do not put a token in repository files, `.env`, or source code. NEXT-004A must not train a model or freeze a store, category, SKU subset, forecast horizon, or chronological time split.

## Known Blockers

- `P4_ACQUISITION_BLOCKED` (2026-09-17): `.\\.venv\\Scripts\\kaggle.exe competitions files m5-forecasting-accuracy` returned `Authentication required to call the Kaggle API.` The local commit must not include credentials. Resolve with the manual OAuth login in NEXT-004A, then retry the harmless file-list command before downloading.
