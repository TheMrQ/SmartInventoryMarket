# Validation Baseline Summary

This is a fixed-origin 28-day validation experiment for the frozen M5 `CA_1` / `FOODS` scope.
Forecast origin: `d_1885`. Validation: `d_1886`–`d_1913` (2016-03-28–2016-04-24).
TEST SALES VALUES WERE NOT READ OR EVALUATED.

| Method | MAE | RMSE | WAPE (%) | SKUs | Validation days | Undefined per-SKU WAPE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Seasonal Naive (lag 7) | 1.739785 | 3.357394 | 82.678226 | 1437 | 28 | 81 |
| 28-day Moving Average | 1.438625 | 2.726401 | 68.366443 | 1437 | 28 | 81 |

Validation result: **28-day Moving Average** has the lower MAE; **28-day Moving Average** has the lower RMSE; and **28-day Moving Average** has the lower WAPE.

## Definitions

- Seasonal Naive repeats each SKU's final seven known train days four times; validation actuals are never used as inputs.
- 28-day Moving Average repeats each SKU's mean over its final 28 known train days; validation actuals are never used to update it.
- WAPE = sum(abs(actual - forecast)) / sum(abs(actual)) * 100. Per-SKU WAPE is recorded as undefined when a SKU's validation actual sum is zero.

## Per-SKU Error Findings

### Seasonal Naive (lag 7)

- Median per-SKU MAE: 1.250000
- Mean per-SKU MAE: 1.739785
- 90th-percentile per-SKU MAE: 3.478571
- Undefined per-SKU WAPE: 81 of 1437 (zero validation-demand denominator).

### 28-day Moving Average

- Median per-SKU MAE: 1.045918
- Mean per-SKU MAE: 1.438625
- 90th-percentile per-SKU MAE: 2.738776
- Undefined per-SKU WAPE: 81 of 1437 (zero validation-demand denominator).
