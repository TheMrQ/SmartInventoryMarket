# Selected Forecasting Model -- Validation Only

## Frozen Decision

- **Selected forecasting model based on validation:** `XGBOOST_V1`.
- **Selected feature set:** `FEATURE_SET_V1` / `FULL_V1` (25 features).
- **Forecasting formulation:** one global one-step regression model with recursive 28-day inference.
- **Configuration:** frozen `count:poisson` / `hist` XGBoost configuration in `configs/models/xgboost_v1.yaml`.
- **Selection pointer:** `configs/models/selected_forecasting_model.yaml`.

## Selected Validation Metrics

| MAE | RMSE | WAPE (%) |
| ---: | ---: | ---: |
| 1.402449 | 2.568234 | 66.647316 |

The pre-registered rule uses WAPE as the primary metric, with MAE and RMSE as secondary checks. Lower is better for all three. XGBOOST_V1 is lower than every current baseline and ML method on validation.

## Comparison Context

| Method | MAE | RMSE | WAPE (%) | Interpretation relative to selected model |
| --- | ---: | ---: | ---: | --- |
| Seasonal Naive (lag 7) | 1.739785 | 3.357394 | 82.678226 | Higher error on all metrics. |
| 28-day Moving Average | 1.438625 | 2.726401 | 68.366443 | Strongest baseline; XGBoost improves MAE/WAPE by 2.515% and RMSE by 5.801%. |
| LIGHTGBM_V1 | 1.523283 | 2.730151 | 72.389572 | XGBoost improves MAE/WAPE by 7.932% and RMSE by 5.931%. |
| XGBOOST_V1 / FULL_V1 | 1.402449 | 2.568234 | 66.647316 | Selected on validation. |

## Feature-Ablation Decision

The 25-feature FULL_V1 result is retained. Every reduced feature variant has higher validation WAPE, MAE, and RMSE:

| Variant | Features | MAE | RMSE | WAPE (%) | WAPE change vs FULL |
| --- | ---: | ---: | ---: | ---: | ---: |
| FULL_V1 | 25 | 1.402449 | 2.568234 | 66.647316 | 0.000% |
| NO_PRICE | 20 | 1.410193 | 2.590741 | 67.015300 | +0.552% |
| NO_CALENDAR_EVENT | 16 | 1.436128 | 2.637362 | 68.247805 | +2.401% |
| DEMAND_PRODUCT_ONLY | 11 | 1.436787 | 2.659655 | 68.279111 | +2.448% |

Price features provide a modest validation benefit, and calendar/event features provide a clearer validation benefit in this experiment. Demand/product-only features preserve much of the observed performance but do not match FULL_V1. The hypothesis that substantially fewer features could match or exceed FULL_V1 is not supported by this validation experiment; this does not claim that these features are always necessary in every setting.

## Resource Trade-off

XGBOOST_V1 required 109.747 seconds and its ignored local JSON artifact is 93.565 MiB. LIGHTGBM_V1 required 49.370 seconds and its ignored artifact is 2.447 MiB. The reduced XGBoost variants were faster (61.235--88.416 seconds) but had higher validation error and did not produce smaller artifacts (101.622--107.880 MiB). Forecast accuracy, runtime, and artifact size are reported separately; no arbitrary combined score was used.

## Test Isolation

This is a **validation-selected model**, not a final test-validated model. TEST `d_1914`--`d_1941` remains sealed: its sales values were not read, forecast, scored, summarized, plotted, or used for selection. A held-out TEST evaluation belongs only to the planned final evaluation stage after downstream work.
