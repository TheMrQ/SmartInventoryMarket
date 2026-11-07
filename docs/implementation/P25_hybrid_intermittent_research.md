# P25-02 — Final Hybrid Intermittent-Demand Forecast Research

**Status:** `DONE` — no hybrid candidate selected. `XGBOOST_V1` remains immutable and the selected/default model.

## Scientific progression and scope

P25-01 found that adding intermittent-demand features to one global XGBoost model worsened aggregate MAE/WAPE and substantially harmed sparse/low-volume series. P25-02 tested a different, limited hypothesis: demand regimes may need different forecasting strategies. It retains the unchanged rolling-retrained V1 forecast for regular demand and routes only a deterministic pre-origin intermittent subset to a transparent classical method.

This is offline M5 demand research only. It did not edit V1 configuration/features/selected-model settings, APIs, P22 forecast run 18, MySQL, or any operational simulation records.

## Evaluation isolation

| Fold | Training history available at origin | Validation actuals opened only after all predictions |
| --- | --- | --- |
| 1 | `d_1`–`d_1801` | `d_1802`–`d_1829` |
| 2 | `d_1`–`d_1829` | `d_1830`–`d_1857` |
| 3 | `d_1`–`d_1857` | `d_1858`–`d_1885` |
| 4 | `d_1`–`d_1885` | `d_1886`–`d_1913` |

The final-TEST span `d_1914`–`d_1941` was not loaded, scored, plotted, or used for any routing/parameter/selection choice. The runner contains no final-TEST actual loader import, validates the exact pre-TEST fold definition, and records `test_actuals_accessed: false` in the manifest.

## Demand regime and methods

At each origin, a series is intermittent when the proportion of zero sales in its **last 56 observed training days** is at least the preregistered threshold. Thresholds were 0.65 and 0.75 only. The final 65% routing proportions were 34.586%, 31.872%, 29.993%, and 28.045% in folds 1–4 respectively (497, 458, 431, and 403 of 1,437 series).

The locally implemented, deterministic methods are:

- **Croston classic:** separately exponentially smooths non-zero demand size and elapsed inter-demand interval; the rate is size divided by interval.
- **SBA:** multiplies Croston's rate by the explicit bias correction `1 - alpha / 2`.
- **TSB:** exponentially smooths occurrence probability daily and smooths size only when demand occurs; its rate is probability times size.

All-zero history returns a zero rate. A method's constant nonnegative expected daily rate is repeated over the 28-day horizon; no artificial day-to-day variation is created. Classical methods consume M5 sales history only, not P22 synthetic operational fields.

## Predeclared candidates and Stage 1

Stage 1 used folds 2 and 4. It evaluated one Croston candidate, SBA at alpha 0.05/0.10/0.20 (plus 75% SBA alpha 0.10), and TSB probability alpha 0.05/0.10/0.20 with size alpha 0.10 (plus 75% TSB 0.10/0.10). V1 was retrained unchanged once per origin, then its forecast was substituted only for the routed series.

| Candidate family | Stage-1 mean MAE | Stage-1 mean RMSE | Stage-1 mean WAPE | Result |
| --- | ---: | ---: | ---: | --- |
| Croston, ZR65, alpha 0.10 | 1.509728 | 2.754077 | 73.623308% | Screened out |
| SBA candidates | 1.487633–1.507947 | 2.700965–2.747584 | 72.538541–73.542189% | Screened out |
| TSB ZR65, p=0.05/s=0.10 | 1.373770 | 2.578487 | 66.967944% | Screened out |
| TSB ZR65, p=0.10/s=0.10 | 1.365945 | 2.571314 | 66.588863% | Finalist |
| TSB ZR65, p=0.20/s=0.10 | 1.363835 | 2.567345 | 66.486406% | Finalist |
| TSB ZR75, p=0.10/s=0.10 | 1.368639 | 2.570346 | 66.723497% | Screened out |

## Stage 2 results

| Model | Fold 1 MAE / RMSE / WAPE | Fold 2 | Fold 3 | Fold 4 |
| --- | --- | --- | --- | --- |
| V1 rolling control | 1.324232 / 2.735215 / 69.581195% | 1.347505 / 2.541834 / 67.412962% | 1.386687 / 2.561367 / 66.840035% | 1.402449 / 2.568234 / 66.647316% |
| TSB ZR65 p=.10/s=.10 | 1.299099 / 2.733314 / 68.260575% | 1.337906 / 2.565261 / 66.932730% | 1.377408 / 2.571976 / 66.392798% | 1.393983 / 2.577366 / 66.244996% |
| TSB ZR65 p=.20/s=.10 | 1.303846 / 2.739883 / 68.510012% | 1.336144 / 2.561475 / 66.844560% | 1.380493 / 2.574925 / 66.541522% | 1.391527 / 2.573214 / 66.128253% |

| Model | Mean MAE | Mean RMSE | Mean WAPE | WAPE-improved folds |
| --- | ---: | ---: | ---: | ---: |
| V1 rolling control | 1.365218 | 2.601663 | 67.620377% | — |
| TSB ZR65 p=.10/s=.10 | 1.352099 | 2.611979 | 66.957775% | 4 / 4 |
| TSB ZR65 p=.20/s=.10 | 1.353002 | 2.612374 | 67.006087% | 4 / 4 |

## Error and horizon interpretation

The stronger TSB hybrid improves the past-history 75–100%-zero group from MAE 0.675971 to 0.629512. It also reduces low-volume Q1 MAE from 0.478143 to 0.413429. Dense 0–25%-zero MAE is unchanged at 2.492339 because those series retain V1. High-volume Q4 MAE rises slightly from 2.839041 to 2.854294 (0.54%), within the preregistered 1% tolerance. Department MAE is lower for `FOODS_1` (1.222127 vs 1.233519), `FOODS_2` (1.022174 vs 1.023052), and `FOODS_3` (1.545761 vs 1.565254).

Across grouped horizons, TSB p=.10/s=.10 improves WAPE over V1 in days 1–7 (63.529028% vs 63.858431%), 8–14 (67.494209% vs 68.041129%), 15–21 (68.084233% vs 68.916235%), and 22–28 (68.922790% vs 69.897719%). RMSE nevertheless regresses in three of the four grouped horizons, consistent with the aggregate non-selection result. No result reached RMSE below 2.49.

## Selection decision

The preregistered gate requires lower mean WAPE, non-worse mean MAE and RMSE, WAPE improvement in at least three folds, sparse-group improvement, and no material dense/high-volume harm. TSB p=.10/s=.10 passes the WAPE, MAE, all-four-fold, sparse, dense, and high-volume checks, but fails the mean-RMSE condition (2.611979 vs 2.601663). Therefore **no hybrid is selected**. This is a useful result: regime-aware routing helps intermittent-demand MAE/WAPE but is not a justified production replacement under the stated multidimensional rule.

## Reproducibility and resources

Run `./.venv/Scripts/python.exe scripts/ml/run_hybrid_intermittent_research.py` with the ignored local M5 raw files. The four unchanged V1 fits averaged 104.932 seconds and 4.648 seconds of recursive prediction per fold; mean ignored model size was 93.284 MiB. Hybrid routing itself uses the same V1 predictions and adds no model artifact. The full method/candidate/fold/routing record is in `data/manifests/hybrid_intermittent_research.json`; tracked evidence includes the `reports/tables/hybrid_*.csv` files and two `reports/figures/hybrid_*.png` figures. Model JSON files remain ignored.
