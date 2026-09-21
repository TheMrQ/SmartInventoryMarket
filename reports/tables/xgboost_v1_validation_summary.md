# XGBOOST_V1 Validation Summary

XGBOOST_V1 is an initial / untuned global one-step model. `count:poisson` is its training objective; MAE, RMSE, and WAPE remain the thesis metrics.

## Training Setup

- One global CPU XGBoost model trained on 2,668,509 SKU-day rows from 1,437 CA_1/FOODS series using the unchanged 25-feature FEATURE_SET_V1.
- Parameters: `{"colsample_bytree": 1.0, "feature_set": "FEATURE_SET_V1", "learning_rate": 0.05, "max_depth": 8, "min_child_weight": 10, "model_name": "XGBOOST_V1", "n_estimators": 400, "n_jobs": -1, "objective": "count:poisson", "random_state": 42, "reg_alpha": 0.0, "reg_lambda": 1.0, "subsample": 1.0, "tree_method": "hist"}`.
- Native categorical policy: the same deterministic integer codes were cast to pandas categorical dtype with a frozen schema; `enable_categorical=True` was used. No one-hot encoding or XGBoost-only feature was added.
- Categorical level counts: `{"dept_code": 3, "event_name_1_code": 31, "event_name_2_code": 5, "event_type_1_code": 5, "event_type_2_code": 3, "is_weekend": 2, "item_code": 1437, "month": 12, "snap_CA": 2, "wday": 7, "year": 6}`.
- Runtime: 109.747 seconds; final trees: 400; local ignored JSON model: `C:\SmartInventMarket\artifacts\models\xgboost_v1.json` (93.565 MiB).
- Versions: `{"numpy": "2.5.2", "pandas": "3.0.5", "python": "3.12.10", "scikit_learn": "1.9.0", "xgboost": "3.4.1"}`.

## Recursive Validation Protocol

All forecasts for d_1886–d_1913 were generated before validation actuals were loaded. Each step used training history plus earlier XGBoost predictions, rebuilt past-only features, and never appended validation actual sales. Future prices remained unavailable (`NaN`).

## Four-Method Validation Metrics

| Method | MAE | RMSE | WAPE (%) |
| --- | ---: | ---: | ---: |
| Seasonal Naive (lag 7) | 1.739785 | 3.357394 | 82.678226 |
| 28-day Moving Average | 1.438625 | 2.726401 | 68.366443 |
| LIGHTGBM_V1 | 1.523283 | 2.730151 | 72.389572 |
| XGBOOST_V1 | 1.402449 | 2.568234 | 66.647316 |

## Comparisons

- Versus Moving Average: MAE difference -0.036175 (2.515% improvement); RMSE difference -0.158167 (5.801%); WAPE difference -1.719127 points (2.515%).
- Versus LIGHTGBM_V1: MAE difference -0.120833 (7.932% improvement); RMSE difference -0.161917 (5.931%); WAPE difference -5.742256 points (7.932%).

## Per-SKU, Horizon, and Runtime Findings

- Per-SKU XGBoost MAE median/mean/p90: 1.014283 / 1.402449 / 2.602418.
- Undefined per-SKU WAPE: 81 of 1437 because total validation demand is zero.
- Horizon MAE: first 1.219299, last 1.711911, minimum 1.097862, maximum 1.800677.
- Top gain feature: `rolling_mean_7` (64.695% of total gain). Gain is descriptive model behavior, not causal evidence.
- Runtime/model-size evidence: `[{'model': 'LIGHTGBM_V1', 'training_seconds': 49.37, 'model_size_bytes': 2565567}, {'model': 'XGBOOST_V1', 'training_seconds': 109.74699630006216, 'model_size_bytes': 98109535}]`. Speed and artifact size do not select a model.

## Test Isolation

TEST SALES VALUES WERE NOT READ, FORECAST, SCORED, SUMMARIZED, OR PLOTTED.
