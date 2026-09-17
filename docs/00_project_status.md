# Project Status

Project: Smart Inventory Market

Thesis: Development of an Intelligent Supermarket Inventory Management and Product Demand Forecasting System Using Machine Learning

Overall status: `IN_PROGRESS` — P6 Naive / Moving Average Baselines

## Quick Human Summary

What we decided:

- M5 `CA_1` food products are the official forecasting scope: 1,437 SKU-level series.
- The official forecast is 28 daily steps; the app will derive 7/14/28-day demand summaries from it.
- Train, validation, and test are frozen chronological windows; the test window is held out.
- Inventory will be simulated transparently because M5 has no real inventory history.
- MySQL is the application database; MySQL Workbench is its design/admin tool.
- Historical sales can first be imported by CSV; a real deployment should later sync new sales from POS automatically.

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

What we learned:

- `CA_1` + `FOODS` contains exactly 1,437 item-store series across `FOODS_1`, `FOODS_2`, and `FOODS_3`.
- The frozen 28-day windows are train `d_1`–`d_1885`, validation `d_1886`–`d_1913`, and test `d_1914`–`d_1941`.
- No observed M5 zero sale proves zero demand or zero inventory.

What happens next: build the reproducible frozen-subset pipeline and implement seasonal-naive and moving-average baselines, measured with MAE, RMSE, and WAPE.

## Roadmap

| Phase | Status |
| --- | --- |
| P0 Topic selected and roadmap reviewed | DONE |
| P1 Repository + environment + long-term memory | DONE |
| P2 Retail dataset candidate audit | DONE |
| P3 Official dataset strategy + architecture decisions | DONE |
| P4 M5 acquisition + formal local schema audit | DONE |
| P5 Subset + forecast horizon + chronological split freeze | DONE |
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

P5 is complete. The M5 experimental protocol is frozen at `CA_1` + `FOODS` (1,437 series), a 28-day daily forecast, and the documented chronological train/validation/test split. `configs/data/m5_ca1_foods.yaml` is the machine-readable source of protocol values. No preprocessing, feature engineering, forecast calculation, model training, inventory simulation, or application features have been performed.

## Last Stable Checkpoint

`CHECKPOINT-005` — M5 experimental protocol frozen

## Next Exact Step

`NEXT-006` — Build the reproducible CA_1/FOODS preprocessing pipeline and implement the seasonal-naive and moving-average forecasting baselines.

NEXT-006 may preprocess the frozen data and calculate baseline metrics. It must preserve the frozen scope/split, avoid random splitting, and must not train LightGBM or XGBoost.

## Known Blockers

None.
