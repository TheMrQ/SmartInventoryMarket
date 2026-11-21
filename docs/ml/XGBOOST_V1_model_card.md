# XGBOOST_V1 Model Card

- **Model / feature set:** `XGBOOST_V1` / `FEATURE_SET_V1` (`FULL_V1`, 25 leakage-safe past-only features).
- **Training scope:** M5 Forecasting Accuracy, `CA_1` / `FOODS`, 1,437 item-store series.
- **Output:** global recursive daily point forecast for 7, 14, or 28 persisted days; intended inventory-decision-support prototype only.
- **Selection:** validation MAE/RMSE/WAPE 1.402449 / 2.568234 / 66.647316%, lower than the frozen baselines and LightGBM under the documented validation selection protocol.
- **Final TEST:** consumed once only for descriptive final evidence (1.454969 / 2.651296 / 64.450274%); it is not reused for P25-03 calibration, tuning, or selection.
- **Stability:** four pre-TEST rolling origins ending `d_1913` have mean fold MAE/RMSE/WAPE 1.365218 / 2.601663 / 67.620377%.
- **Uncertainty:** P25-03 uses asymmetric empirical rolling residual intervals. Fold 1–3 calibrate, Fold 4 evaluates, and all four pre-TEST folds form the later demo reference. Nominal 80%/95% intervals achieved 79.687%/94.696% Fold-4 coverage.

## Known failure modes

Intermittent and low-volume demand, later recursive horizons, distribution shift, missing/non-contiguous history, stale historical-demo cutoffs, and unseen store/SKU context all reduce trust. M5 zero sales do not prove zero demand or inventory availability.

## Not intended for

Guaranteed future demand, automatic purchasing, arbitrary retailer deployment, or changing inventory formulas without a separate policy experiment. A manager reviews recommendations; a new supermarket requires its own POS, product, calendar, and price data plus retraining/validation.
