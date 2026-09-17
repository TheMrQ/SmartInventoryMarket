# Experiment Plan

Status: planning only; no experiment has run.

| ID | Planned experiment |
| --- | --- |
| E0 | Formal M5 local audit — DONE (data audit, not a forecasting experiment) |
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

## E0 — Formal M5 Local Audit

- **Date:** 2026-09-17
- **Status:** `DONE` — this is a data audit, not a forecasting experiment.
- **Tooling:** Kaggle CLI 2.2.4 in `.venv`; script `scripts/data/audit_m5.py` with 500-row sales chunks and 100,000-row price chunks.
- **Dataset source/location:** Kaggle `m5-forecasting-accuracy`, extracted under Git-ignored `data/raw/m5/`.
- **Manifest/artifacts:** `data/manifests/m5_file_manifest.json`, `data/manifests/m5_audit.json`, and `reports/tables/m5_audit_summary.md`; all contain metadata/aggregates only.
- **Verified result:** Five official CSVs, 429.604 MiB extracted; evaluation sales has 30,490 item-store series × 1,941 daily columns, and price data has 6,841,121 rows.
- **Resource finding:** Audit completed in 48.964 seconds. One optimized sales CSV is plausible to load, but not both sales files plus prices together; chunking/subsetting remains recommended.
- **Metrics:** Not applicable; no model was trained.
- **Next action:** NEXT-005 must freeze the product scope, forecast horizon, and chronological split without beginning a forecasting experiment.
