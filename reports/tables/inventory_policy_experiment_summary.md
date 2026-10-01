# Frozen Inventory Policy Experiment — P12 Results

The policies were executed once under the CHECKPOINT-011 protocol. M5 sales are an exogenous realized-demand proxy; these are simulated inventory outcomes, not observed Walmart inventory performance.

| Metric | MIN_STOCK_MA28 | FORECAST_REORDER_XGBOOST_V1 | Forecast policy change vs baseline |
| --- | ---: | ---: | ---: |
| Total realized demand | 90,833 | 90,833 | Same replay |
| Fulfilled units | 85,471 | 86,468 | +997 |
| Lost-sales units | 5,362 | 4,365 | -18.594% |
| Stockout SKU-days | 1,565 | 1,222 | -21.917% |
| Fill rate | 94.097% | 95.194% | +1.098 percentage points |
| Average on-hand units | 11.806 | 12.569 | +6.466% |
| Reorder events | 13,215 | 12,681 | -4.041% |
| Total ordered quantity | 87,874 | 89,108 | +1.404% |
| SKUs with any stockout | 549 (38.205%) | 492 (34.238%) | -57 SKUs |
| Median per-SKU fill rate | 100.000% | 100.000% | 0.000 points |
| Normalized cost proxy (not USD) | 515,039 | 540,233 | +4.892% |

Negative percentage changes for lost sales and stockouts mean the forecast policy reduced that undesirable metric. Positive fill-rate points mean improvement. Positive inventory/cost changes mean the forecast policy held more stock or incurred a larger normalized proxy cost.

## Interpretation

The forecast policy improves service outcomes under this frozen replay: it reduces lost sales and stockout SKU-days while increasing fill rate and reducing the count of affected SKUs. It does so with 6.466% higher average on-hand inventory and a 4.892% higher normalized cost proxy, despite fewer reorder events. The outcome is therefore **mixed**: forecast-informed reordering improves availability but does not dominate the baseline on every operational/resource measure. Lower forecasting WAPE does not, by itself, guarantee lower inventory cost.
