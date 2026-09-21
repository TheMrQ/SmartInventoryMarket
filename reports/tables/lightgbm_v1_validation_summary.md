# LIGHTGBM_V1 Validation Summary

LIGHTGBM_V1 is the initial / untuned global one-step model. Its Poisson objective is the training loss; MAE, RMSE, and WAPE remain the thesis evaluation metrics.

## Training Setup

- One global LightGBM model trained on 2,668,509 SKU-day rows from 1,437 CA_1/FOODS series using FEATURE_SET_V1 (25 features).
- Parameters: `{"boosting_type": "gbdt", "deterministic": true, "feature_set": "FEATURE_SET_V1", "force_col_wise": true, "learning_rate": 0.05, "max_depth": -1, "min_child_samples": 100, "model_name": "LIGHTGBM_V1", "n_estimators": 400, "n_jobs": -1, "num_leaves": 31, "objective": "poisson", "random_state": 42, "reg_alpha": 0.0, "reg_lambda": 0.1}`.
- Categorical features: `item_code, dept_code, wday, month, year, is_weekend, snap_CA, event_name_1_code, event_type_1_code, event_name_2_code, event_type_2_code`.
- Runtime: 49.370 seconds; final trees: 400; local ignored model: `C:\SmartInventMarket\artifacts\models\lightgbm_v1.joblib` (2.447 MiB).
- Versions: `{"lightgbm": "4.7.0", "numpy": "2.5.2", "pandas": "3.0.5", "python": "3.12.10", "scikit_learn": "1.9.0"}`.

Each boosted decision tree improves the preceding collection's residual fit; the fitted collection of trees is the saved global model. The same model is reused recursively for all 28 forecast days.

## Recursive Validation Protocol

Forecasts for d_1886–d_1913 were generated before validation actuals were loaded. At each step, the runner used train history plus earlier model predictions, rebuilt past-only features, and never appended validation actual sales. Future price values were not used.

## Metrics and Baseline Comparison

| Method | MAE | RMSE | WAPE (%) | MAE improvement vs Moving Average | RMSE improvement | WAPE improvement |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Seasonal Naive (lag 7) | 1.739785 | 3.357394 | 82.678226 | -20.934% | -23.144% | -20.934% |
| 28-day Moving Average | 1.438625 | 2.726401 | 68.366443 | 0.000% | 0.000% | 0.000% |
| LIGHTGBM_V1 | 1.523283 | 2.730151 | 72.389572 | -5.885% | -0.138% | -5.885% |

LIGHTGBM_V1 validation metrics: MAE 1.523283, RMSE 2.730151, WAPE 72.389572%.
Against the Moving Average, its absolute differences are MAE 0.084658, RMSE 0.003749, and WAPE 4.023129 percentage points.

## Per-SKU and Horizon Findings

- Per-SKU LightGBM MAE median/mean/p90: 1.064630 / 1.523283 / 2.697365.
- Undefined per-SKU WAPE: 81 of 1437 due to zero 28-day validation actual demand.
- Recursive horizon MAE: first day 1.226082, last day 1.857874, minimum 1.194999, maximum 1.988939.
- Top gain feature: `rolling_mean_7` (71.563% of total gain). Gain describes fitted-model use, not causal importance.

## Test Isolation

TEST SALES VALUES WERE NOT READ, FORECAST, SCORED, SUMMARIZED, OR PLOTTED.
