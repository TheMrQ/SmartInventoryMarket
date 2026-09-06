# Experiment Plan

Status: planning only; no experiment has run.

| ID | Planned experiment |
| --- | --- |
| E0 | Dataset audit |
| E1 | Naive forecast baseline |
| E2 | Moving Average baseline |
| E3 | LightGBM forecasting |
| E4 | XGBoost forecasting |
| E5 | Feature ablation: without lag/rolling vs with lag/rolling |
| E6 | Forecast-horizon comparison, if appropriate |
| E7 | Forecast-model comparison |
| E8 | Minimum-stock inventory simulation |
| E9 | Forecast-based reorder simulation |
| E10 | Minimum-stock vs forecast-based inventory comparison |

## Required Record for Every Future Experiment

- Experiment ID and date/time
- Git commit
- Dataset version and selected subset
- Train, validation, and test periods
- Forecast horizon and feature set
- Model, hyperparameters, and random seed where relevant
- MAE, RMSE, WAPE, training time, and prediction time
- Artifact paths, observations, decision, and next experiment

Inventory experiments must also record initial-inventory assumptions, lead-time assumptions, safety-stock rule, replenishment rule, stockout count, average inventory, reorder count, service level if used, and a simple cost proxy if used.
