# P23 — XGBoost V2 Forecasting Research

Status: **DONE** (validation-only research; no production-model change)

## Protocol and controls

- Scope: frozen M5 `CA_1` / `FOODS`, 1,437 series; train `d_1`–`d_1885`, validation `d_1886`–`d_1913` (28 days / 40,236 predictions).
- The already-consumed V1 TEST period was never loaded, scored, or used to tune V2. V1's immutable validation artifact is the only comparison baseline.
- `FEATURE_SET_V2` is separate from V1: 34 past-only features, including lags through 56 days and 3/56-day rolling signals. Its warm-up is 56 days. Recursive validation appends only prior forecasts; unknown future prices remain missing.
- Candidate JSON files are local Git-ignored artifacts; only aggregate tables and a compact manifest are tracked. Saved candidate models were reloaded and checked before recursive inference.

## Candidate results

| Candidate | MAE | RMSE | WAPE | Decision |
| --- | ---: | ---: | ---: | --- |
| XGBOOST_V1 (immutable baseline) | 1.402449 | 2.568234 | 66.647316% | retained |
| V2 Poisson conservative | 1.390242 | 2.588324 | 66.067219% | no: RMSE worsened |
| V2 Poisson capacity | 1.389021 | 2.571583 | 66.009157% | no: RMSE worsened |
| V2 squared regularized | — | — | — | disqualified: negative recursive prediction; no clipping |

WAPE is primary, but the selection protocol also requires non-worse MAE and RMSE. The best V2 candidate improved WAPE by 0.958% and MAE by 0.958%, but RMSE worsened by 0.130%; it is therefore not selected. No inventory-policy comparison was run because no credible replacement emerged. Direct multi-horizon was documented but not run: it requires 28 separately leak-safe models and was not justified by this result.

## Error and resource observations

V1 validation has 81 zero-total-demand SKUs and 250 series with at least 75% zero days. It has positive mean bias (+0.1163), 63.62% overprediction cells, median per-SKU MAE 1.0143, p90 2.6024, and mean MAE rises from 1.3216 over horizons 1–7 to 1.4156 over 22–28, consistent with recursive accumulation. V1 error rises with observed validation-volume quartile (MAE 0.5102 low to 2.8303 high). The two scored V2 fits took 151.8s / 241.3s and occupy 55.2 / 201.7 MiB, versus V1's recorded 109.7s / 93.6 MiB.

## Evidence

- `configs/features/ml_features_v2.yaml`
- `configs/experiments/xgboost_v2_research.yaml`
- `reports/tables/xgboost_v2_validation_results.csv`
- `reports/tables/xgboost_v2_horizon_metrics.csv`
- `reports/tables/xgboost_v1_error_by_validation_volume.csv`
- `data/manifests/xgboost_v2_validation.json`

The API/default configuration remains `XGBOOST_V1`; rollback is therefore inherent. Any future V3 study must remain validation/backtest-only and create a new immutable experiment record.
