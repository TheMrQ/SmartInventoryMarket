# Experiment Plan

Status: `IN_PROGRESS` — validation baselines are complete; ML features and models have not been implemented.

| ID | Planned experiment |
| --- | --- |
| E0 | Formal M5 local audit — DONE (data audit, not a forecasting experiment) |
| E1 | Seasonal Naive (`lag_7`) validation baseline — DONE |
| E2 | 28-day Moving Average validation baseline — DONE |
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

## E0 — Formal M5 Local Audit

- **Date:** 2026-09-17
- **Status:** `DONE` — this is a data audit, not a forecasting experiment.
- **Tooling:** Kaggle CLI 2.2.4 in `.venv`; script `scripts/data/audit_m5.py` with 500-row sales chunks and 100,000-row price chunks.
- **Dataset source/location:** Kaggle `m5-forecasting-accuracy`, extracted under Git-ignored `data/raw/m5/`.
- **Manifest/artifacts:** `data/manifests/m5_file_manifest.json`, `data/manifests/m5_audit.json`, and `reports/tables/m5_audit_summary.md`; all contain metadata/aggregates only.
- **Verified result:** Five official CSVs, 429.604 MiB extracted; evaluation sales has 30,490 item-store series × 1,941 daily columns, and price data has 6,841,121 rows.
- **Resource finding:** Audit completed in 48.964 seconds. One optimized sales CSV is plausible to load, but not both sales files plus prices together; chunking/subsetting remains recommended.
- **Metrics:** Not applicable; no model was trained.
- **Follow-up:** Completed by CHECKPOINT-005; the protocol is now frozen without beginning a forecasting experiment.

## Frozen Protocol for Future Forecast Experiments — CHECKPOINT-005

- **Scope:** M5 `CA_1` + `FOODS`, including `FOODS_1`, `FOODS_2`, and `FOODS_3`; 1,437 verified SKU/item-store series.
- **Protocol source:** `configs/data/m5_ca1_foods.yaml`.
- **Primary target:** one 28-day daily forecast (`t+1` through `t+28`). App-facing 7/14/28-day demand summaries will be aggregates of this one prediction output, not independently trained horizons.
- **Chronological split:** train `d_1`–`d_1885` (2011-01-29–2016-03-27), validation `d_1886`–`d_1913` (2016-03-28–2016-04-24), and held-out test `d_1914`–`d_1941` (2016-04-25–2016-05-22).
- **Baselines:** seasonal naive (`lag_7`) is the primary naive baseline; a 28-day moving average is the second frozen baseline. Simple `lag_1` is auxiliary only if used.
- **Metrics:** MAE, RMSE, and WAPE, reported both in aggregate and later with per-SKU/error-distribution analysis. MAPE is not a sole primary metric because zero sales are common.
- **Protocol controls:** no random split, no model selection/tuning with test data, and no future-target leakage in lags, rolling statistics, price, or calendar features.
- **Status:** no metrics calculated and no model/baseline run in this protocol-decision task.

## E1 / E2 — Validation Baselines

- **Date:** 2026-09-21
- **Status:** `DONE` — fixed-origin forecasting baselines, not trained ML models.
- **Dataset scope:** M5 `CA_1` + `FOODS`, all three FOODS departments; 1,437 SKU/item-store series.
- **Forecast origin / validation:** only `d_1`–`d_1885` were known at origin. The 28-day validation target was `d_1886`–`d_1913` (2016-03-28–2016-04-24), totaling 40,236 SKU-day observations.
- **Methods:** Seasonal Naive repeats the final seven train days four times. The 28-day Moving Average repeats the final-28-train-day mean for each SKU. Neither method updates from validation actuals.
- **Aggregate results:** Seasonal Naive MAE 1.739785, RMSE 3.357394, WAPE 82.678226%; 28-day Moving Average MAE 1.438625, RMSE 2.726401, WAPE 68.366443%.
- **Comparison:** 28-day Moving Average is lower on every aggregate validation metric and is the current reference baseline.
- **Per-SKU findings:** Seasonal Naive median/90th-percentile MAE 1.250000/3.478571; Moving Average 1.045918/2.738776. For both methods, 81 of 1,437 SKUs have undefined per-SKU WAPE because their 28-day actual-demand denominator is zero; this was not converted to zero.
- **Metrics:** WAPE = sum(abs(actual - forecast)) / sum(abs(actual)) × 100. Aggregate validation demand denominator was nonzero; MAE/RMSE remain available for every SKU.
- **Assets:** `data/manifests/m5_ca1_foods_preparation_manifest.json`, `reports/tables/baseline_validation_metrics.csv`, `reports/tables/baseline_validation_summary.md`, `reports/figures/baseline_validation_comparison.png`, and `reports/figures/baseline_per_sku_error_distribution.png`.
- **TEST:** NOT ACCESSED for forecasting evaluation. Preparation verified only TEST column names/calendar dates; the runner read sales values through `d_1913` only.
