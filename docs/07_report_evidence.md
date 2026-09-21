# Thesis Report Evidence Registry

This registry records reproducible report assets and planned manual evidence. It is not a substitute for the experimental memory or raw-data access controls.

| Asset / Evidence | Status | Generated or Manual Screenshot | Purpose | Possible Thesis Section | Source Script / Command | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `data/manifests/m5_ca1_foods_preparation_manifest.json` | DONE | Generated | Verify frozen scope and chronological boundaries | Dataset / methodology | `python scripts/data/prepare_m5_ca1_foods.py` | Metadata only; TEST sales values were not read. |
| `reports/tables/baseline_validation_metrics.csv` | DONE | Generated | Concise validation comparison table | Experiments / results | `python scripts/ml/run_baselines.py` | Aggregate metrics only; TEST not evaluated. |
| `reports/tables/baseline_validation_summary.md` | DONE | Generated | Definitions, validation results, and per-SKU findings | Experiments / results | `python scripts/ml/run_baselines.py` | Includes undefined per-SKU WAPE handling. |
| `reports/figures/baseline_validation_comparison.png` | DONE | Generated | Compare baseline MAE, RMSE, and WAPE on separate axes | Experiments / results | `python scripts/ml/run_baselines.py` | English labels; 220 DPI. |
| `reports/figures/baseline_per_sku_error_distribution.png` | DONE | Generated | Show per-SKU validation MAE distribution | Experiments / results | `python scripts/ml/run_baselines.py` | Aggregate error distribution, not raw time-series. |
| `configs/features/ml_features_v1.yaml` | DONE | Generated | Freeze first ML feature definition | Methodology | Version-controlled configuration | FEATURE_SET_V1; no model trained. |
| `data/manifests/m5_ca1_foods_features_v1.json` | DONE | Generated | Reproducibility, mappings, dtypes, missingness, and resources | Methodology / appendix | `python scripts/ml/build_features.py` | Metadata only; train sales through d_1885 only. |
| `reports/tables/feature_set_v1_summary.md` | DONE | Generated | Describe feature groups and leakage safeguards | Methodology | `python scripts/ml/build_features.py` | Report-ready feature evidence. |
| FEATURE_SET_V1 leakage-test evidence | DONE | Generated | Verify no current/future target leakage | Methodology / appendix | `pytest ml/tests/test_feature_builder.py` | Synthetic tests; no raw M5 dependency. |
| Dataset overview/schema figure | TODO | Generated | Explain M5 source and frozen scope | Dataset | Future task | Do not create before the relevant verified task. |
| `reports/tables/lightgbm_v1_validation_metrics.csv` and `reports/figures/lightgbm_v1_model_comparison.png` | DONE | Generated | Report LightGBM validation performance against frozen baselines | Experiments / results | `python scripts/ml/train_lightgbm.py` | Initial untuned run; improves Seasonal Naive but not the Moving Average; TEST sealed. |
| `reports/tables/lightgbm_v1_horizon_metrics.csv` and `reports/figures/lightgbm_v1_horizon_mae.png` | DONE | Generated | Assess recursive 28-step validation error by horizon | Experiments / results | `python scripts/ml/train_lightgbm.py` | Validation-only recursive predictions; TEST remains sealed. |
| `data/manifests/lightgbm_v1_validation.json` and `reports/tables/lightgbm_v1_validation_summary.md` | DONE | Generated | Record reproducibility and practical cost | Experiments / results / appendix | `python scripts/ml/train_lightgbm.py` | Records configuration, versions, runtime, ignored-artifact hash/size, and test policy. |
| `reports/tables/xgboost_v1_validation_metrics.csv` and `reports/figures/xgboost_v1_model_comparison.png` | DONE | Generated | Compare all four validation methods | Experiments / results | `python scripts/ml/train_xgboost.py` | XGBoost initial validation evidence; final selection remains TODO. |
| `reports/tables/xgboost_v1_feature_importance.csv` and `reports/figures/xgboost_v1_feature_importance_gain.png` | DONE | Generated | Explain fitted XGBoost feature use | Experiments / results | `python scripts/ml/train_xgboost.py` | Gain is descriptive, not causal; no features were removed. |
| `reports/tables/xgboost_v1_horizon_metrics.csv` and `reports/figures/xgboost_v1_horizon_mae.png` | DONE | Generated | Assess XGBoost recursive horizon error | Experiments / results | `python scripts/ml/train_xgboost.py` | Validation-only recursive predictions; TEST sealed. |
| `reports/figures/ml_models_horizon_mae_comparison.png` | DONE | Generated | Compare LightGBM and XGBoost recursive horizon MAE | Experiments / results | `python scripts/ml/train_xgboost.py` | Model-selection interpretation is deferred to NEXT-010. |
| `reports/figures/xgboost_v1_validation_total_actual_vs_forecast.png` and `reports/figures/xgboost_v1_per_sku_mae_distribution.png` | DONE | Generated | Show aggregate XGBoost validation fit and SKU error distribution | Experiments / results | `python scripts/ml/train_xgboost.py` | Aggregate/distribution evidence only; TEST not accessed. |
| `reports/tables/ml_models_runtime_comparison.csv` and `data/manifests/xgboost_v1_validation.json` | DONE | Generated | Compare runtime/model size and preserve XGBoost reproducibility | Experiments / results / appendix | `python scripts/ml/train_xgboost.py` | Performance and resource cost are separate evaluation dimensions. |
| Model comparison | TODO | Generated | Compare selected methods | Experiments / results | Future task | Requires validation comparison/model selection. |
| `reports/tables/lightgbm_v1_feature_importance.csv` and `reports/figures/lightgbm_v1_feature_importance_gain.png` | DONE | Generated | Explain fitted LightGBM feature use | Experiments / results | `python scripts/ml/train_lightgbm.py` | Gain importance is descriptive, not causal; no raw sales rows are exposed. |
| `reports/figures/lightgbm_v1_validation_total_actual_vs_forecast.png` and `reports/figures/lightgbm_v1_per_sku_mae_distribution.png` | DONE | Generated | Show aggregate validation actual/forecast and per-SKU error distribution | Experiments / results | `python scripts/ml/train_lightgbm.py` | Aggregate and distribution evidence only; TEST not accessed. |
| Database ERD | TODO | Manual screenshot | Show MySQL Workbench database design | System design | Future database task | Prefer exported ERD if available. |
| API demonstration | TODO | Manual screenshot | Show FastAPI Swagger/API behavior | Implementation | Future API task | Capture a running, reproducible endpoint. |
| Application dashboard | TODO | Manual screenshot | Show dashboard UI | Implementation | Future frontend task | Capture the running application. |
| Forecast interface | TODO | Manual screenshot | Show forecast interaction | Implementation | Future frontend task | Capture the running application. |
| Reorder recommendation interface | TODO | Manual screenshot | Show decision-engine output | Implementation | Future frontend task | Capture the running application. |

## Manual Screenshot Policy

Generated charts and tables should be saved directly as files. Manual screenshots are reserved primarily for evidence that is naturally visual and cannot be reproduced better as an exported artifact, such as MySQL Workbench ERD/interface, FastAPI Swagger/API demonstration, the running web application UI/dashboard, forecast interaction, reorder recommendation screen, and selected experiment-execution evidence when useful for an appendix.

Do not require a screenshot of every terminal command. At the end of a future task, state either `MANUAL SCREENSHOT RECOMMENDED:` followed by the exact item to capture, or `MANUAL SCREENSHOT REQUIRED: NO`.
