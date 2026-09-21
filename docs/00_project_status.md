# Project Status

Project: Smart Inventory Market

Thesis: Development of an Intelligent Supermarket Inventory Management and Product Demand Forecasting System Using Machine Learning

Overall status: `IN_PROGRESS` — P7 Leakage-Safe Forecasting Features

## Quick Human Summary

What we decided:

- M5 `CA_1` food products are the official forecasting scope: 1,437 SKU-level series.
- The official forecast is 28 daily steps; the app will derive 7/14/28-day demand summaries from it.
- Train, validation, and test are frozen chronological windows; the test window is held out.
- The 28-day Moving Average is the current validation reference baseline.
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
- Prepared the frozen source boundary and generated the first fixed-origin 28-day validation forecasts.

What we learned:

- `CA_1` + `FOODS` contains exactly 1,437 item-store series across `FOODS_1`, `FOODS_2`, and `FOODS_3`.
- The frozen 28-day windows are train `d_1`–`d_1885`, validation `d_1886`–`d_1913`, and test `d_1914`–`d_1941`.
- No observed M5 zero sale proves zero demand or zero inventory.
- On validation, the 28-day Moving Average outperformed Seasonal Naive: MAE 1.438625 vs 1.739785, RMSE 2.726401 vs 3.357394, and WAPE 68.366443% vs 82.678226%.
- The 28 validation days contained 81 SKUs with zero total actual sales, so their per-SKU WAPE is undefined rather than treated as zero.

What happens next: build leakage-safe lag, rolling, calendar, and price features for the first ML forecasting model. LightGBM and XGBoost have not been trained.

## Roadmap

| Phase | Status |
| --- | --- |
| P0 Topic selected and roadmap reviewed | DONE |
| P1 Repository + environment + long-term memory | DONE |
| P2 Retail dataset candidate audit | DONE |
| P3 Official dataset strategy + architecture decisions | DONE |
| P4 M5 acquisition + formal local schema audit | DONE |
| P5 Subset + forecast horizon + chronological split freeze | DONE |
| P6 Naive / Moving Average baselines | DONE |
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

P6 is complete. The reusable frozen-scope boundary, validation-only Seasonal Naive and 28-day Moving Average baselines, aggregate/per-SKU metrics, report figures, and evidence registry are in place. The runner reads sales values through validation `d_1913` only; TEST remains sealed and was not evaluated. No ML feature engineering, LightGBM/XGBoost training, inventory simulation, or application features have been performed.

## Last Stable Checkpoint

`CHECKPOINT-006` — CA_1/FOODS preprocessing and validation baselines complete

## Next Exact Step

`NEXT-007` — Build leakage-safe time-series, calendar, and price features for the first ML forecasting model.

NEXT-007 must preserve the frozen scope/split and test isolation. It may build features, but must not train a model unless a subsequent task explicitly authorizes it.

## Known Blockers

None.
