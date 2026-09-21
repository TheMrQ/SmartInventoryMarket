# XGBoost Feature-Group Ablation V1

All variants use the same frozen CA_1/FOODS scope, 1,437 series, 2,668,509 training rows, XGBOOST_V1 hyperparameters/seed, 28-step recursive validation protocol, and metric utilities. FULL_V1 was reused from its verified tracked result; the other three variants alone were trained. All reduced forecasts were generated before validation actuals were loaded. TEST SALES VALUES WERE NOT READ, FORECAST, SCORED, SUMMARIZED, OR PLOTTED.

| Variant | Meaning | Features | MAE | RMSE | WAPE (%) | Runtime (s) | Size (MiB) | WAPE improvement vs FULL |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FULL_V1 | all frozen information | 25 | 1.402449 | 2.568234 | 66.647316 | 109.747 | 93.565 | 0.000% |
| NO_PRICE | removes historical price information | 20 | 1.410193 | 2.590741 | 67.015300 | 76.427 | 102.569 | -0.552% |
| NO_CALENDAR_EVENT | removes calendar/event information | 16 | 1.436128 | 2.637362 | 68.247805 | 88.416 | 101.622 | -2.401% |
| DEMAND_PRODUCT_ONLY | keeps demand history plus product identity | 11 | 1.436787 | 2.659655 | 68.279111 | 61.235 | 107.880 | -2.448% |

## Research Questions

- **RQ-A:** Demand/product-only does not match FULL_V1 on all three validation metrics; demand history is highly informative but the 11-feature model is not sufficient by this strict criterion.
- **RQ-B:** Removing calendar/event features worsened validation WAPE, so the group helps this validation experiment under the frozen protocol.
- **RQ-C:** Removing historical price features worsened validation WAPE, so the group helps this validation experiment under the frozen protocol.
- **RQ-D:** No for this validation experiment: the 11-feature model does not match or exceed FULL_V1 on all three metrics.

## Pre-registered Recommendation

**RECOMMENDED CANDIDATE FOR NEXT-010B: FULL_V1.** It has the lowest validation WAPE under the pre-registered WAPE-first rule (MAE/RMSE remain secondary). This is a recommended candidate only; NEXT-010B, not this experiment, formally freezes the forecasting model and feature set.
The best reduced variant by WAPE is NO_PRICE. Feature count is a parsimony consideration, not a substitute for forecast quality.
