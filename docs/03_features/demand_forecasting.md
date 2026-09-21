# Demand Forecasting

Status: `IN_PROGRESS` — the frozen protocol, validation baselines, FEATURE_SET_V1, and the initial LightGBM validation run are complete; XGBoost and model selection remain.

## Dataset and Models

Official forecasting dataset: **M5 Forecasting - Accuracy**.

## Frozen Experimental Protocol — CHECKPOINT-005

The version-controlled protocol is [configs/data/m5_ca1_foods.yaml](../../configs/data/m5_ca1_foods.yaml). Its values are frozen for the baseline and ML comparison work unless a future documented protocol revision explicitly supersedes them.

- **Scope:** `store_id = CA_1`, `cat_id = FOODS`, including `FOODS_1`, `FOODS_2`, and `FOODS_3`.
- **Experimental unit:** one M5 SKU/item within store `CA_1`. There are 1,437 verified item-store series. M5 `item_id` values remain the experimental identities; Vietnamese-friendly names, if ever used for a demo, must be separate seed data and must not replace M5 IDs.
- **Modeling approach:** global forecasting. One LightGBM model has learned from many SKU-day observations using item identity and time-series/calendar/price features; future XGBoost work follows the same one-model, not one-model-per-SKU, formulation. Per-series baselines are appropriate where their methods require them.
- **Primary forecast:** 28 daily steps, `t+1` through `t+28`. A single output will supply application demand summaries as sums of days 1–7, 1–14, and 1–28, avoiding separately trained 7-, 14-, and 28-day models unless later evidence justifies a protocol change.

| Partition | M5 keys | Calendar dates | Purpose |
| --- | --- | --- | --- |
| Train | `d_1`–`d_1885` | 2011-01-29–2016-03-27 | Fit model/baseline parameters |
| Validation | `d_1886`–`d_1913` | 2016-03-28–2016-04-24 | Select methods and hyperparameters using train + validation only |
| Test | `d_1914`–`d_1941` | 2016-04-25–2016-05-22 | One final held-out evaluation |

The raw sales file is wide: one item-store row followed by `d_1` through `d_1941`. A later preprocessing task will create the conceptual long-form records `date`, `item_id`, `sales`, `price`, calendar features, lag features, and rolling features. This checkpoint does not implement that transformation.

M5 supplies historical retail sales for thesis model development and evaluation. It does not provide Walmart on-hand inventory, replenishment, supplier lead time, or purchase-order history. Those inventory inputs will later be simulated under documented assumptions, and their results must be described as simulation results rather than observed Walmart inventory performance.

Frozen baseline plan, completed in CHECKPOINT-006:

- **Seasonal Naive (primary naive):** same day in the preceding week (`lag_7`), which is more appropriate than a simple naive forecast for likely retail weekly seasonality.
- **28-day Moving Average:** a clearly documented moving-average baseline.
- **Auxiliary only:** simple naive (`lag_1`) may be retained as a reference, not the primary naive baseline.

## Validation-Only Baseline Results — CHECKPOINT-006

The reusable runner `scripts/ml/run_baselines.py` evaluated the frozen `CA_1`/`FOODS` scope at the fixed forecast origin `d_1885`. It read train and validation sales values only through `d_1913`; it did not read, forecast, score, summarize, or plot TEST sales values.

- **Seasonal Naive:** repeats each SKU's final seven known training days four times, producing the 28 validation steps without using any validation actual as a later forecast input.
- **28-day Moving Average:** repeats each SKU's mean over its final 28 known training days for all 28 validation steps, without any validation update.

| Method | Validation MAE | Validation RMSE | Validation WAPE | Undefined per-SKU WAPE |
| --- | ---: | ---: | ---: | ---: |
| Seasonal Naive (`lag_7`) | 1.739785 | 3.357394 | 82.678226% | 81 |
| 28-day Moving Average | 1.438625 | 2.726401 | 68.366443% | 81 |

The 28-day Moving Average is lower on all three aggregate validation metrics and is the reference baseline future methods must beat on validation. Per-SKU WAPE is undefined, not zero, for the 81 SKUs with zero total validation actual demand; MAE and RMSE remain available for them. Details are recorded in `reports/tables/baseline_validation_summary.md`.

## FEATURE_SET_V1 — Leakage-Safe ML Inputs

The first ML formulation is a **global one-step regression model**. One future LightGBM model will learn from all `CA_1`/`FOODS` SKU-day training observations; it is not one model per SKU or one model per forecast horizon. For target day `t`, the model receives information available before `t` and predicts sales at `t`.

At later inference, the model will make a **recursive 28-step forecast**: predict `t+1`, append that prediction to the working sales history, recompute the same past-only features, and continue through `t+28`. This is computationally practical, deploys as one global model, and fits the frozen global-model plan. Its limitation is recursive error propagation: early prediction error can affect later steps. Direct multi-horizon forecasting remains future work only.

`configs/features/ml_features_v1.yaml` freezes FEATURE_SET_V1. `scripts/ml/build_features.py` produced 2,668,509 train rows from `d_1`–`d_1885` after dropping the 28-day warm-up for each of 1,437 series (40,236 dropped rows). The ignored local cache is `data/processed/m5_ca1_foods_features_v1.pkl.gz`; tracked metadata and methodology summary are `data/manifests/m5_ca1_foods_features_v1.json` and `reports/tables/feature_set_v1_summary.md`.

- **Sales history:** `lag_1`, `lag_7`, `lag_14`, `lag_28`; `rolling_mean_7`, `rolling_mean_14`, `rolling_mean_28`; and population `rolling_std_7`, `rolling_std_28`. Every value stops at `t-1`; incomplete warm-up rows are dropped.
- **Calendar:** `wday`, `month`, `year`, `is_weekend`, `snap_CA`, and deterministic codes for `event_name_1`, `event_type_1`, `event_name_2`, and `event_type_2`. TX/WI SNAP values are excluded because the frozen store is CA_1. Calendar/event values are known-date inputs, not causal claims.
- **Product identity:** deterministic `item_code` and `dept_code`; the manifest preserves the mapping to real M5 IDs and no demo names are substituted.
- **Past-only prices:** `last_known_sell_price`, `price_lag_7`, `price_change_from_7_days_ago`, `price_available`, and `price_missing`. Current target-day price and future prices are excluded. Prices only forward-fill within an item/store from already observed values; there is no backward fill. Before a first known price, the feature remains missing and the indicator remains explicit.
- **Missingness:** sales lag/rolling inputs have no post-warm-up missing values. Price history remains missing for 508,049 `last_known_sell_price`, 512,561 `price_lag_7`, and 512,561 price-change feature rows; these are not imputed from future values.

`ml/features/builder.py` shares the feature calculations between vectorized training construction and the single-step inference API. The inference API accepts only explicit sales/price history, product metadata, categorical mappings, and the target calendar row. A caller must append prior predictions—not validation actuals—between recursive steps. Synthetic tests verify lag/rolling values, current-target and future mutation isolation, past-only prices, deterministic encoding, calendar mapping, recursive feature shape, and config validation.

## LIGHTGBM_V1 — Initial Global Recursive Validation (CHECKPOINT-008)

`configs/models/lightgbm_v1.yaml` freezes the first intentionally untuned CPU configuration: Poisson objective, `gbdt`, 400 estimators, learning rate 0.05, 31 leaves, `min_child_samples=100`, `reg_lambda=0.1`, seed 42, deterministic column-wise training, and no random subsampling. `ml/models/lightgbm_model.py` fits exactly one global model, explicitly marks `item_code`, `dept_code`, calendar/SNAP, and event codes as categorical, and rejects non-finite or negative forecasts rather than silently clipping them.

`scripts/ml/train_lightgbm.py` fit 2,668,509 FEATURE_SET_V1 train rows (1,437 series, 25 features), then used `ml/models/recursive.py` to generate all 40,236 `d_1886`–`d_1913` predictions before loading validation actuals. At each step the working sales history receives the preceding continuous model prediction; price history receives an unknown (`NaN`) value, so no future sell price or validation actual sales can enter the forecast. TEST sales values were not read, forecast, scored, summarized, or plotted.

| Method | Validation MAE | Validation RMSE | Validation WAPE |
| --- | ---: | ---: | ---: |
| Seasonal Naive (`lag_7`) | 1.739785 | 3.357394 | 82.678226% |
| 28-day Moving Average | 1.438625 | 2.726401 | 68.366443% |
| `LIGHTGBM_V1` | 1.523283 | 2.730151 | 72.389572% |

The first LightGBM run improves every aggregate metric over Seasonal Naive but is worse than the Moving Average by 0.084658 MAE, 0.003749 RMSE, and 4.023129 WAPE percentage points. This is an experimental result, not a model-selection decision. Per-SKU LightGBM MAE median/mean/p90 are 1.064630 / 1.523283 / 2.697365; 81 of 1,437 series have undefined per-SKU WAPE because their validation-demand denominator is zero. Horizon MAE is 1.226082 on day 1 and 1.857874 on day 28 (minimum 1.194999; maximum 1.988939), showing fluctuating recursive error rather than a monotonic path.

Gain importance is descriptive of the fitted trees, not causal: `rolling_mean_7` contributes 71.563% of total gain, followed by `rolling_mean_14` (17.714%), `rolling_mean_28` (2.941%), `lag_1` (1.974%), and `item_code` (1.876%). The ignored model artifact is `artifacts/models/lightgbm_v1.joblib` (2.447 MiB, SHA-256 recorded in the tracked manifest); fitting took 49.370 seconds on the local CPU. Tracked evidence is the `lightgbm_v1_*` manifest, tables, and figures under `data/manifests/` and `reports/`.

Planned ML models:

- LightGBM
- XGBoost

Possible later comparison: SARIMA or Prophet.

Optional only: LSTM / Transformer.

## Planned Features

- `lag_1`, `lag_7`, `lag_14`, `lag_28`
- Rolling statistics
- Day of week, month, and weekend indicators
- Event variables
- Price and price change

## Evaluation and Leakage Rules

- **No random split.** The frozen chronological train/validation/test windows above are mandatory.
- **Test isolation.** Test data remains untouched during model development. Hyperparameter and model decisions use train plus validation only; final reported test metrics use test only and must not drive tuning.
- **Past-only target features.** No future sales may appear in training features. Lag features must reference past observations only.
- **Safe rolling features.** Rolling statistics must be shifted before rolling when necessary so that the current or future target never enters a feature.
- **Prediction-time availability.** Price and calendar features must reflect information that would have been available when the forecast was issued.

Primary thesis metrics are **MAE**, **RMSE**, and **WAPE**. Do not report Accuracy for forecasting. Do not use MAPE as the sole primary metric because many SKU-days have zero observed sales. Future reports must provide both aggregate metrics across all `CA_1`/`FOODS` observations and per-SKU/error-distribution analysis so high-volume products do not hide poor SKU-level performance.

The experiment order is: validation baselines → leakage-safe lag/rolling/calendar/price features → initial LightGBM (complete) → XGBoost → validation comparison/model selection → one final TEST evaluation. TEST stays sealed until that final evaluation; it must never be used to choose a feature, baseline, model, or hyperparameter.

## Future Model Lifecycle

Prediction and retraining are different operations:

```text
New daily sales
      ↓
Update time-series features
      ↓
Existing trained model
      ↓
Generate new forecasts
```

Retraining does not need to occur after every transaction. Future strategies may use scheduled retraining (for example, monthly) or retraining when measured model performance degrades. The retraining frequency is not frozen.

## Definition of Done

Official training and evaluation must be reproducible and script-based, not notebook-driven. Runs must record configuration, seed, dataset version/subset, chronological split, feature set, model parameters, metrics, Git commit, and artifact paths. Models must be evaluated against baselines before use in inventory recommendations.
