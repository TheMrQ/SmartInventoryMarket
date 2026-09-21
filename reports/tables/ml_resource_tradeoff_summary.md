# ML Resource Trade-off Summary

| Model | Training seconds | Model size (MiB) | Validation WAPE (%) |
| --- | ---: | ---: | ---: |
| LIGHTGBM_V1 | 49.370 | 2.447 | 72.389572 |
| XGBOOST_V1 | 109.747 | 93.565 | 66.647316 |

XGBOOST_V1 took 2.223× the LightGBM training runtime and produced a 38.241× larger local artifact. LightGBM is computationally lighter in this experiment; XGBoost has better validation forecasting performance. These are separate dimensions, not a combined winner score.

TEST SALES VALUES WERE NOT READ, FORECAST, SCORED, SUMMARIZED, OR PLOTTED.
