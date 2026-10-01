# Final Held-Out TEST Forecast Evaluation

`XGBOOST_V1` + `FEATURE_SET_V1` / `FULL_V1` was selected on validation before TEST was opened. It was retrained exactly once on TRAIN + VALIDATION through `d_1913` without tuning.

## Final TEST Metrics

| MAE | RMSE | WAPE (%) | Predictions |
| ---: | ---: | ---: | ---: |
| 1.454969 | 2.651296 | 64.450274 | 40,236 |

## Protocol Evidence

- Train-plus-validation FEATURE_SET_V1 rows: 2,708,745.
- Fit runtime: 93.503 seconds; selected configuration and 25 features are unchanged.
- All 40,236 fixed-origin predictions for `d_1914`–`d_1941` were created and hashed before TEST actual sales were loaded.
- Per-SKU WAPE is undefined for 25 of 1437 SKUs with zero TEST-demand denominators.
- Horizon MAE: first 1.144386, last 1.814026, minimum 1.130687, maximum 1.916348.
- TEST metrics are final held-out evidence and were not used for post-TEST model selection, feature changes, hyperparameter tuning, or retraining.
