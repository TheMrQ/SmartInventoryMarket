# P25-03 — Forecast Reliability, Uncertainty, and Decision-Trust Evidence

Status: `DONE` as a P25 research/product-evidence subtask. Broad P25 remains `PLANNED`; P24 browser acceptance remains `IN_PROGRESS`.

## What “trustworthy” means here

Reliability is evidence across separate dimensions, not a fabricated confidence score: chronological accuracy (MAE/RMSE/WAPE), stability across time, signed bias, interval calibration, demand sparsity/difficulty, operational-policy utility, provenance, human review, and stated limitations. No screen says that a forecast is “X% correct.”

The selected point model remains immutable: `XGBOOST_V1` with `FEATURE_SET_V1` / `FULL_V1` (25 past-only features), trained for M5 `CA_1` / `FOODS` and a 28-day recursive horizon. Its original validation result is MAE 1.402449, RMSE 2.568234, WAPE 66.647316%; its one already-consumed final TEST result is MAE 1.454969, RMSE 2.651296, WAPE 64.450274%. Neither model selection nor the Decision Engine formula changed in P25-03.

## Non-leaky interval protocol

The reproducible runner is `scripts/ml/run_forecast_reliability.py`, configured by `configs/experiments/forecast_reliability_v1.yaml`.

- It permits only four expanding V1 origins ending at `d_1913`; its guard fails for `d_1914` or later.
- It reloads the existing rolling V1 artifacts and produces each recursive point forecast before opening the matching fold’s actuals.
- Residual = actual demand − point forecast. Intervals are asymmetric empirical residual quantiles, with final lower **demand** bounds only clamped to zero.
- Fold 1–3 residuals calibrate the independent Fold-4 evaluation. Only after that evaluation is frozen are all four pre-TEST folds used as the demo/reference calibration pool.
- 80% uses the 10th–90th residual quantiles; 95% uses the 2.5th–97.5th quantiles. Buckets use horizon + 56-day sparsity band only with at least 500 residuals; otherwise they fall back to horizon, then global. This prevents small-bucket overfitting.
- Final TEST actuals `d_1914`–`d_1941` were **not accessed**.

## Results

The four rolling folds have mean fold MAE/RMSE/WAPE of **1.365218 / 2.601663 / 67.620377%**. Their MAE rises from 1.324232 in Fold 1 to 1.402449 in Fold 4, while WAPE varies from 69.581195% to 66.647316%; one favorable fixed window therefore is not treated as proof of universal stability. Pooled-observation details and daily horizon metrics are tracked in `reports/tables/forecast_reliability_*.csv`.

Independent Fold-4 calibration is close to nominal: the 80% interval contained actual demand **79.687%** of the time (mean width 3.515 units), while the 95% interval contained **94.696%** (mean width 6.604 units). This means: “under this defined rolling backtest, the 80% interval historically contained actual demand about 79.7% of the time”—not that any exact forecast is 80% correct.

Sparse demand remains materially difficult. WAPE increases from 49.979% in the 0–25% zero-demand band to 109.737% in the 75–100% band; a zero observed sale is not proof of zero customer demand or stock. Exact horizon and interval-coverage evidence is retained daily; later-horizon WAPE is generally more variable, so the product shows horizon-specific bands rather than claiming uniformly reliable 28-day predictions.

Per-product labels are qualitative and deterministic. `LIMITED` applies for a 56-day zero rate at least 65%, or historical MAE/80% width at or above the corresponding pre-TEST 75th percentile; `HIGHER` requires <=25% zeros and both MAE and width no higher than their medians; all other products are `MODERATE`. These labels describe comparable historical evidence, not probability of correctness.

## Decision utility and control

P12’s frozen policy simulation is separate evidence: compared with `MIN_STOCK_MA28`, forecast-based ordering reduced lost sales 5,362 → 4,365 and stockout days 1,565 → 1,222, improved fill rate 94.097% → 95.194%, and required fewer reorders 13,215 → 12,681. It also raised average on-hand inventory 11.806 → 12.569 and normalized cost proxy 515,039 → 540,233. Thus it improved simulated service availability at a higher inventory/cost proxy; it is not “always better.”

The UI adds a read-only Forecast Reliability panel, 80% historical uncertainty shading, provenance/freshness disclosure, and Inventory Insight decision evidence. It does not alter safety stock, reorder point, target stock, recommended quantity, forecast values, purchase-order behavior, or human approval. Recommendations remain reviewed before a PO can be created.

## Limitations and defense answer

M5 supplies historical Walmart demand, while product inventory, supplier, and PO records are synthetic thesis-demo operations. The frozen model cannot forecast arbitrary new SKUs or a new supermarket without local POS/context retraining and validation. Intermittent/low-volume demand, later recursive horizons, distribution shift, and stale demo origins require more caution.

Vietnamese defense answer: **Hệ thống không tuyên bố dự báo chắc chắn. Độ tin cậy được kiểm tra bằng dữ liệu thời gian chưa thấy, bốn backtest theo thời gian, sai lệch dự báo, độ bao phủ của khoảng bất định và mô phỏng chính sách tồn kho. Khoảng 80%/95% là bằng chứng lịch sử theo giao thức đã công bố, không phải “độ tự tin” của từng con số. Quyết định mua vẫn cần người quản lý xem xét tồn kho, nhà cung cấp, thời gian giao hàng và giới hạn dữ liệu.**

## P25-03b manager-language presentation

P25-03b changes only the presentation of the existing evidence. The manager-facing Forecasts and Inventory Insights views now show a readable reliability state with a derived reason, typical forecast error, demand pattern, model, history cutoff, forecast period, and a manager-review reminder. The four existing 56-day zero-sales bands are rendered as Stable, Variable, Irregular, or Highly intermittent; these are deterministic labels for the same stored bands, not a new classifier.

Technical traceability remains preserved behind `View technical details`: historical MAE/RMSE, exact zero-sales rate, the original evidence basis, forecast run ID, feature set, and independent interval-check coverage. No interval, residual, model, calibration, API, forecast value, inventory formula, recommendation quantity, database record, or P22 scenario value changed.
