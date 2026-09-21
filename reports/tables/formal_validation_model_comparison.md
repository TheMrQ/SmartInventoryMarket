# Formal Validation Model Comparison

All results below are existing, tracked validation-only experiment outputs. Forecast quality and resource cost are intentionally reported separately.

| Method | MAE | RMSE | WAPE (%) | Training required | Training seconds | Model size (MiB) | Feature count |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| Seasonal Naive (lag 7) | 1.739785 | 3.357394 | 82.678226 | False | — | — | — |
| 28-day Moving Average | 1.438625 | 2.726401 | 68.366443 | False | — | — | — |
| LIGHTGBM_V1 | 1.523283 | 2.730151 | 72.389572 | True | 49.370 | 2.447 | 25 |
| XGBOOST_V1 | 1.402449 | 2.568234 | 66.647316 | True | 109.747 | 93.565 | 25 |

## Interpretation

Seasonal Naive is the weakest current method. The 28-day Moving Average is a strong simple reference. LIGHTGBM_V1 improves Seasonal Naive but does not beat Moving Average. XGBOOST_V1 has the lowest validation MAE, RMSE, and WAPE.

**CURRENT VALIDATION LEADER: XGBOOST_V1** — this is not a final-model declaration because TEST remains sealed and the frozen feature-group ablation has not run.

## Frozen Next Experiment

NEXT-010A will run controlled XGBoost feature-group ablation only: FULL_V1 (25 features; existing result reused), NO_PRICE (20), NO_CALENDAR_EVENT (16), and DEMAND_PRODUCT_ONLY (11). All retain the same scope, split, 28-day recursive protocol, XGBoost V1 hyperparameters, seed, and sealed TEST. WAPE is the primary comparison metric; MAE and RMSE are secondary.

The research questions are whether demand-only history provides most performance, whether calendar/event or price groups improve validation forecasts, and whether 11 features retain comparable or better error. Gain importance is descriptive and does not preselect a top-k feature model.

TEST SALES VALUES WERE NOT READ, FORECAST, SCORED, SUMMARIZED, OR PLOTTED.
