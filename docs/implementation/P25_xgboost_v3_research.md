# P25-01 — XGBoost V3 Rolling-Backtest Research

**Status:** `DONE` — no candidate selected; `XGBOOST_V1` remains immutable and the selected/default forecasting model.

## Objective and scope

This controlled offline study tested whether a global recursive XGBoost formulation with intermittent-demand features could credibly replace the frozen V1 model for the M5 `CA_1` / `FOODS` scope (1,437 item-store series). It did not modify the API, database, P22 scenario, selected-model configuration, V1/V2 artifacts, or production model file.

## Evaluation protocol and final-TEST isolation

Each model emitted all 28 recursive predictions for a fold before that fold's sales actuals were loaded for scoring. The exact expanding folds were:

| Fold | Training sales available at origin | Validation actuals loaded only after forecasting |
| --- | --- | --- |
| 1 | `d_1`–`d_1801` | `d_1802`–`d_1829` |
| 2 | `d_1`–`d_1829` | `d_1830`–`d_1857` |
| 3 | `d_1`–`d_1857` | `d_1858`–`d_1885` |
| 4 | `d_1`–`d_1885` | `d_1886`–`d_1913` |

`d_1914`–`d_1941` final-TEST actuals were never loaded. The runner deliberately uses only `load_rolling_fold_actuals`, has no final-TEST actual-loader import, rejects a fold ending after `d_1913`, and writes `test_actuals_accessed: false` in the manifest. The earlier V1 final-TEST result remains historical final-evaluation evidence and was not used to tune or select V3.

## Candidate design

FEATURE_SET_V3 has 44 inputs. It retains V2's past-only sales lags/rolling statistics, calendar context, product identity, and past-only price features, then adds:

- 28/56-day zero-demand rate;
- 28/56-day non-zero-demand mean plus an explicit `has_nonzero_demand` indicator;
- 28-day rolling median;
- days since the last non-zero sale, capped at 56; and
- 7:28 and 28:56 rolling-mean trend ratios.

All feature windows end at `t-1`. For an all-zero history window, the non-zero mean is deterministically zero and the accompanying flag is false, avoiding an ambiguous implicit imputation. Regression tests mutate future sales and prove these values do not alter target-time features.

Stage 1 compared two Poisson candidates and a squared-error check on folds 2 and 4. The two Poisson candidates advanced by Stage 1 WAPE. Stage 2 completed all four folds for those finalists. The fair control retrained the unchanged V1 configuration at each fold origin.

## Aggregate selection result

| Candidate | Mean MAE | Mean RMSE | Mean WAPE | WAPE-improved folds vs V1 | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| `XGBOOST_V1_ROLLING_RETRAINED` | 1.365218 | 2.601663 | 67.620377% | — | Control/default retained |
| `V3_POISSON_REGULARIZED` | 1.420281 | 2.588206 | 70.366227% | 0 / 4 | Not selected |
| `V3_POISSON_BALANCED` | 1.423776 | 2.586972 | 70.540783% | 0 / 4 | Not selected |

The preregistered gate required lower mean WAPE, non-worse MAE and RMSE, at least three folds with WAPE improvement, and acceptable error-group behavior. Both finalists slightly reduced mean RMSE but worsened MAE and WAPE on every fold. Consequently, neither can replace V1. No V3 fold reached the aspirational RMSE below 2.49; that value was observational only, not a tuning target.

## Per-fold evidence

| Fold | V1 MAE / RMSE / WAPE | Regularized V3 MAE / RMSE / WAPE | Balanced V3 MAE / RMSE / WAPE |
| --- | --- | --- | --- |
| 1 | 1.324232 / 2.735215 / 69.581195% | 1.388262 / 2.689093 / 72.945596% | 1.392641 / 2.662931 / 73.175739% |
| 2 | 1.347505 / 2.541834 / 67.412962% | 1.409270 / 2.541773 / 70.502911% | 1.413451 / 2.545222 / 70.712089% |
| 3 | 1.386687 / 2.561367 / 66.840035% | 1.445886 / 2.563968 / 69.693546% | 1.447966 / 2.574409 / 69.793798% |
| 4 | 1.402449 / 2.568234 / 66.647316% | 1.437707 / 2.557989 / 68.322857% | 1.441046 / 2.565325 / 68.481506% |

## Error-profile interpretation

Diagnostics are aggregate series-fold results, not an inventory or stockout claim. The regularized V3 candidate modestly improves the densest 0–25%-zero band (MAE 2.350445 vs V1 2.372054) and the high-volume quartile (2.811343 vs 2.839041), but it degrades the 75–100%-zero band (0.870094 vs 0.552827), low-volume Q1 (0.722023 vs 0.478143), and every department aggregate. Department MAE is 1.284970/1.075629/1.622467 for `FOODS_1`/`FOODS_2`/`FOODS_3`, versus V1's 1.233519/1.023052/1.565254. Thus the additional intermittent signals do not behave acceptably across the intended product mix.

The tracked tables provide complete reproducible diagnostics:

- `reports/tables/xgboost_v3_rolling_metrics.csv`
- `reports/tables/xgboost_v3_candidate_summary.csv`
- `reports/tables/xgboost_v3_error_by_sparsity.csv`
- `reports/tables/xgboost_v3_error_by_volume.csv`
- `reports/tables/xgboost_v3_error_by_department.csv`
- `reports/tables/xgboost_v3_horizon_metrics.csv`

The horizon MAE and mean rolling-WAPE figures are `reports/figures/xgboost_v3_horizon_mae.png` and `reports/figures/xgboost_v3_mean_rolling_wape.png`.

## Resource record

| Model | Features | Mean training time/fold | Mean prediction time/fold | Mean ignored model size |
| --- | ---: | ---: | ---: | ---: |
| V1 rolling control | 25 | 104.071s | 4.693s | 93.284 MiB |
| V3 Poisson balanced | 44 | 105.264s | 4.686s | 38.664 MiB |
| V3 Poisson regularized | 44 | 132.649s | 4.623s | 74.904 MiB |

The full research run reached roughly 3.3 GiB resident memory while constructing/training recursive fold matrices. Its model JSON files stay under Git-ignored `artifacts/models/`; only metadata, checksums, metrics, figures, and documentation are tracked.

## Reproducibility and follow-up

Run `./.venv/Scripts/python.exe scripts/ml/run_xgboost_v3_research.py` from the repository root with local ignored M5 raw files present. The configuration is `configs/experiments/xgboost_v3_research.yaml`; the feature contract is `configs/features/ml_features_v3.yaml`; the manifest records the starting source commit, exact folds, model hashes, sizes, and selection outcome.

This negative selection result is useful thesis evidence: V3 was tested with a chronological, leakage-safe protocol and rejected under the declared rule. Future forecasting work must be separately specified, still exclude the final-TEST actuals from tuning, and must not change `XGBOOST_V1` without a new documented selection decision.
