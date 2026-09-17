# Project Status

Project: Smart Inventory Market

Thesis: Development of an Intelligent Supermarket Inventory Management and Product Demand Forecasting System Using Machine Learning

Overall status: `IN_PROGRESS` — P5 Subset, Forecast Horizon, and Chronological Split Freeze

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

What we did:

- Downloaded and locally inspected the five official M5 files.
- Verified their real columns, sizes, products, stores, dates, sales, and prices.
- Identified candidate single-store FOODS subsets without choosing one.

What we learned:

- Evaluation sales contains 30,490 item-store series over 1,941 observed daily columns.
- There are 10 stores, 3,049 items, 3 categories, and 7 departments.
- Observed sales are sparse: 68.00% of evaluation sales cells are zero, which does not prove zero demand or inventory.
- The CSVs occupy 429.604 MiB extracted; memory-conscious chunking/subsetting is recommended.

What happens next: choose one store/product scope, choose a 7/14/28-day forecast horizon, and freeze chronological train/validation/test windows. Only after that may baseline forecasting begin.

## Roadmap

| Phase | Status |
| --- | --- |
| P0 Topic selected and roadmap reviewed | DONE |
| P1 Repository + environment + long-term memory | DONE |
| P2 Retail dataset candidate audit | DONE |
| P3 Official dataset strategy + architecture decisions | DONE |
| P4 M5 acquisition + formal local schema audit | DONE |
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

P4 is complete. The official M5 archive was acquired locally, extracted under Git-ignored `data/raw/m5/`, and formally audited by `scripts/data/audit_m5.py`. P5 must review the verified candidates and freeze a single-store product scope, horizon, and chronological protocol. No training, feature engineering, inventory simulation, or application features have been performed.

## Last Stable Checkpoint

`CHECKPOINT-004` — M5 acquired and formally audited

## Next Exact Step

`NEXT-005` — Review the verified M5 audit and freeze the single-store product scope, forecast horizon, and chronological train/validation/test protocol.

NEXT-005 must use the local audit evidence, must not use a random split, and must not start model training.

## Known Blockers

None.
