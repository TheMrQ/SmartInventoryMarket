# Project Status

Project: Smart Inventory Market

Thesis: Development of an Intelligent Supermarket Inventory Management and Product Demand Forecasting System Using Machine Learning

Overall status: `IN_PROGRESS` — Dataset Strategy Review

## Roadmap

| Phase | Status |
| --- | --- |
| P0 Topic selected and roadmap reviewed | DONE |
| P1 Repository + environment + long-term memory | DONE |
| P2 Retail dataset candidate audit | DONE |
| P3 Review dataset strategy + select official dataset/subset + freeze time split | TODO |
| P4 Naive / Moving Average forecasting baselines | TODO |
| P5 Time-series feature engineering | TODO |
| P6 LightGBM forecasting | TODO |
| P7 XGBoost forecasting | TODO |
| P8 Forecast comparison + model selection | TODO |
| P9 Inventory simulation protocol | TODO |
| P10 Minimum-stock vs forecast-based reorder experiment | TODO |
| P11 Database + FastAPI core | TODO |
| P12 Inventory/product/supplier modules | TODO |
| P13 Sales integration + forecasting API | TODO |
| P14 Inventory decision engine | TODO |
| P15 React dashboard + application integration | TODO |
| P16 Testing + final experiments | TODO |
| P17 Thesis report + defense package | TODO |

## Current Task

P2 retail dataset candidate audit is complete. The project is awaiting user review before any official dataset strategy is frozen. No candidate has been acquired locally, and no preprocessing, EDA, model training, feature engineering, or application features have been performed.

## Last Stable Checkpoint

`CHECKPOINT-002` — Dataset candidates audited

## Next Exact Step

`NEXT-003` — Review the dataset audit with the user and freeze the official dataset strategy.

This review must decide whether to use M5 with explicitly simulated inventory, a single verified dataset, or another defensible strategy. It must not start model training. Once a dataset is selected, a later formal acquisition/schema audit and chronological subset/time-split freeze remain required before forecasting work.

## Known Blockers

None.
