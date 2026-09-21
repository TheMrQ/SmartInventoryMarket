# Project Status

Project: Smart Inventory Market

Thesis: Development of an Intelligent Supermarket Inventory Management and Product Demand Forecasting System Using Machine Learning

Overall status: 🟢 **DONE** — P10 complete; project intentionally PAUSED BEFORE P11 after the forecasting model was selected.

## Quick Human Summary

What we selected:

- XGBoost is the validation-selected forecasting algorithm.
- The full 25-feature `FEATURE_SET_V1` / `FULL_V1` is retained.
- It achieved the best validation result: MAE 1.402449, RMSE 2.568234, and WAPE 66.647316%.
- Reducing to 20, 16, or 11 features made validation forecasting worse.
- TEST is still sealed.

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
- Converted train sales into leakage-safe ML features: past sales lags, rolling demand, calendar/events, product codes, and historical prices.
- Trained and evaluated the initial global `LIGHTGBM_V1` model using a recursive 28-day validation forecast.
- Trained the initial global `XGBOOST_V1` model under the identical frozen data, feature, and recursive-validation protocol.
- Formally compared all four validation methods, their horizon behavior, feature-group gain patterns, and ML resource trade-offs without training another model.
- Froze the controlled XGBoost feature-group ablation protocol for the next experiment.
- Reused FULL_V1 and trained the three frozen reduced XGBoost variants under the same recursive validation protocol.
- Formally selected and froze `XGBOOST_V1` + `FEATURE_SET_V1` / `FULL_V1` from validation-only evidence.

What we learned:

- `CA_1` + `FOODS` contains exactly 1,437 item-store series across `FOODS_1`, `FOODS_2`, and `FOODS_3`.
- The frozen 28-day windows are train `d_1`–`d_1885`, validation `d_1886`–`d_1913`, and test `d_1914`–`d_1941`.
- No observed M5 zero sale proves zero demand or zero inventory.
- On validation, the 28-day Moving Average outperformed Seasonal Naive: MAE 1.438625 vs 1.739785, RMSE 2.726401 vs 3.357394, and WAPE 68.366443% vs 82.678226%.
- The 28 validation days contained 81 SKUs with zero total actual sales, so their per-SKU WAPE is undefined rather than treated as zero.
- FEATURE_SET_V1 contains 25 model features across 2,668,509 train rows; tests confirm features cannot see their own target or future sales.
- `LIGHTGBM_V1` completed 400 deterministic CPU trees in 49.370 seconds. Its validation MAE/RMSE/WAPE were 1.523283 / 2.730151 / 72.389572%: better than Seasonal Naive, but not the 28-day Moving Average reference (1.438625 / 2.726401 / 68.366443%).
- Recursive forecasts were created before validation actuals were loaded; TEST sales values remain unread, unforecast, unscored, unsummarized, and unplotted.
- `XGBOOST_V1` achieved validation MAE/RMSE/WAPE of 1.402449 / 2.568234 / 66.647316%. It beat Seasonal Naive, the Moving Average (2.515% MAE/WAPE and 5.801% RMSE improvement), and `LIGHTGBM_V1` (7.932% MAE/WAPE and 5.931% RMSE improvement).
- XGBoost took 109.747 seconds and its ignored JSON artifact is 93.565 MiB, versus LightGBM's 49.370 seconds and 2.447 MiB. Performance and resource cost remain separate considerations.
- `XGBOOST_V1` + `FEATURE_SET_V1` / `FULL_V1` is the **selected forecasting model based on validation**. It is not a final test-validated model because TEST remains sealed.
- Recent rolling-demand features account for 93.146% of LightGBM and 95.527% of XGBoost normalized gain. This is descriptive model behavior, not evidence that the other features are unnecessary.
- FULL_V1 (25 features) remains lowest on validation WAPE/MAE/RMSE. The best reduced model, NO_PRICE (20), worsens WAPE by 0.552%; calendar/event removal and the 11-feature demand/product model worsen it by 2.401% and 2.448%.

What happens next: the project is intentionally paused before P11. Future work begins with the inventory simulation protocol; it must not evaluate TEST unless the separately planned final-evaluation stage is reached.

## Roadmap

| Phase | Status |
| --- | --- |
| P0 Topic selected and roadmap reviewed | 🟢 **DONE** |
| P1 Repository + environment + long-term memory | 🟢 **DONE** |
| P2 Retail dataset candidate audit | 🟢 **DONE** |
| P3 Official dataset strategy + architecture decisions | 🟢 **DONE** |
| P4 M5 acquisition + formal local schema audit | 🟢 **DONE** |
| P5 Subset + forecast horizon + chronological split freeze | 🟢 **DONE** |
| P6 Naive / Moving Average baselines | 🟢 **DONE** |
| P7 Time-series feature engineering | 🟢 **DONE** |
| P8 LightGBM forecasting | 🟢 **DONE** |
| P9 XGBoost forecasting | 🟢 **DONE** |
| P10 Forecast comparison + model selection | 🟢 **DONE** |
| P11 Inventory simulation protocol | ⚪ **TODO** |
| P12 Minimum-stock vs forecast-based reorder experiment | ⚪ **TODO** |
| P13 MySQL + FastAPI core | ⚪ **TODO** |
| P14 Inventory/product/supplier modules | ⚪ **TODO** |
| P15 Sales ingestion + forecasting API | ⚪ **TODO** |
| P16 Inventory decision engine | ⚪ **TODO** |
| P17 React dashboard + integration | ⚪ **TODO** |
| P18 Testing + final experiments | ⚪ **TODO** |
| P19 Thesis report + defense package | ⚪ **TODO** |

## Current Task

P10 is complete. The pre-registered WAPE-first rule (with MAE/RMSE secondary) selected `XGBOOST_V1` + `FEATURE_SET_V1` / `FULL_V1` (25 features) from validation evidence. Every reduced variant was worse on all three metrics. The project is intentionally paused before P11; TEST remains sealed.

## Last Stable Checkpoint

`CHECKPOINT-010B` — `XGBOOST_V1` + `FEATURE_SET_V1` formally selected on validation

## Next Exact Step

`P11` — Inventory simulation protocol (TODO; deliberately not started in this task).

The project is paused before P11. Any future work must preserve test isolation; it must not open, forecast, score, summarize, or evaluate TEST outside the planned final evaluation.

## Known Blockers

None.
