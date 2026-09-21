# ML Recursive Horizon Comparison

XGBOOST_V1 has lower MAE on 28 of 28 horizons; LIGHTGBM_V1 is lower on 0.

| Model | h=1 MAE | h=28 MAE | Minimum MAE (horizon) | Maximum MAE (horizon) | First-7 mean MAE | Last-7 mean MAE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| LIGHTGBM_V1 | 1.226082 | 1.857874 | 1.194999 (h=3) | 1.988939 (h=14) | 1.443677 | 1.516112 |
| XGBOOST_V1 | 1.219299 | 1.711911 | 1.097862 (h=3) | 1.800677 (h=14) | 1.321572 | 1.415566 |

Both profiles fluctuate, so the evidence does not support a strict monotonic recursive-error increase. Both models have higher MAE on day 28 than day 1, and their largest errors occur at horizon 14; recursively feeding earlier predictions remains a plausible contributor to later-horizon degradation, not proof of its sole cause.

TEST SALES VALUES WERE NOT READ, FORECAST, SCORED, SUMMARIZED, OR PLOTTED.
