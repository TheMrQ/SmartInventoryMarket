# Thesis Report Evidence Registry

This registry records reproducible report assets and planned manual evidence. It is not a substitute for the experimental memory or raw-data access controls.

| Asset / Evidence | Status | Generated or Manual Screenshot | Purpose | Possible Thesis Section | Source Script / Command | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `data/manifests/m5_ca1_foods_preparation_manifest.json` | DONE | Generated | Verify frozen scope and chronological boundaries | Dataset / methodology | `python scripts/data/prepare_m5_ca1_foods.py` | Metadata only; TEST sales values were not read. |
| `reports/tables/baseline_validation_metrics.csv` | DONE | Generated | Concise validation comparison table | Experiments / results | `python scripts/ml/run_baselines.py` | Aggregate metrics only; TEST not evaluated. |
| `reports/tables/baseline_validation_summary.md` | DONE | Generated | Definitions, validation results, and per-SKU findings | Experiments / results | `python scripts/ml/run_baselines.py` | Includes undefined per-SKU WAPE handling. |
| `reports/figures/baseline_validation_comparison.png` | DONE | Generated | Compare baseline MAE, RMSE, and WAPE on separate axes | Experiments / results | `python scripts/ml/run_baselines.py` | English labels; 220 DPI. |
| `reports/figures/baseline_per_sku_error_distribution.png` | DONE | Generated | Show per-SKU validation MAE distribution | Experiments / results | `python scripts/ml/run_baselines.py` | Aggregate error distribution, not raw time-series. |
| Dataset overview/schema figure | TODO | Generated | Explain M5 source and frozen scope | Dataset | Future task | Do not create before the relevant verified task. |
| LightGBM result comparison | TODO | Generated | Report LightGBM validation performance | Experiments / results | Future task | No LightGBM model has been trained. |
| XGBoost result comparison | TODO | Generated | Report XGBoost validation performance | Experiments / results | Future task | No XGBoost model has been trained. |
| Model comparison | TODO | Generated | Compare selected methods | Experiments / results | Future task | Requires validation comparison/model selection. |
| Feature importance | TODO | Generated | Explain fitted ML model drivers | Experiments / results | Future task | Requires a trained interpretable model. |
| Actual vs forecast example | TODO | Generated | Illustrate one selected prediction example | Experiments / results | Future task | Must not expose restricted raw data without review. |
| Database ERD | TODO | Manual screenshot | Show MySQL Workbench database design | System design | Future database task | Prefer exported ERD if available. |
| API demonstration | TODO | Manual screenshot | Show FastAPI Swagger/API behavior | Implementation | Future API task | Capture a running, reproducible endpoint. |
| Application dashboard | TODO | Manual screenshot | Show dashboard UI | Implementation | Future frontend task | Capture the running application. |
| Forecast interface | TODO | Manual screenshot | Show forecast interaction | Implementation | Future frontend task | Capture the running application. |
| Reorder recommendation interface | TODO | Manual screenshot | Show decision-engine output | Implementation | Future frontend task | Capture the running application. |

## Manual Screenshot Policy

Generated charts and tables should be saved directly as files. Manual screenshots are reserved primarily for evidence that is naturally visual and cannot be reproduced better as an exported artifact, such as MySQL Workbench ERD/interface, FastAPI Swagger/API demonstration, the running web application UI/dashboard, forecast interaction, reorder recommendation screen, and selected experiment-execution evidence when useful for an appendix.

Do not require a screenshot of every terminal command. At the end of a future task, state either `MANUAL SCREENSHOT RECOMMENDED:` followed by the exact item to capture, or `MANUAL SCREENSHOT REQUIRED: NO`.
