# Demand Forecasting

Status: `IN_PROGRESS` — the M5 experimental protocol is frozen; preprocessing, features, and forecasting experiments are not yet implemented.

## Dataset and Models

Official forecasting dataset: **M5 Forecasting - Accuracy**.

## Frozen Experimental Protocol — CHECKPOINT-005

The version-controlled protocol is [configs/data/m5_ca1_foods.yaml](../../configs/data/m5_ca1_foods.yaml). Its values are frozen for the baseline and ML comparison work unless a future documented protocol revision explicitly supersedes them.

- **Scope:** `store_id = CA_1`, `cat_id = FOODS`, including `FOODS_1`, `FOODS_2`, and `FOODS_3`.
- **Experimental unit:** one M5 SKU/item within store `CA_1`. There are 1,437 verified item-store series. M5 `item_id` values remain the experimental identities; Vietnamese-friendly names, if ever used for a demo, must be separate seed data and must not replace M5 IDs.
- **Modeling approach:** planned global forecasting. A single future LightGBM or XGBoost model will learn from many SKU-day observations using item identity and time-series/calendar/price features; it will not be one separately trained ML model per SKU. Per-series baselines are appropriate where their methods require them.
- **Primary forecast:** 28 daily steps, `t+1` through `t+28`. A single output will supply application demand summaries as sums of days 1–7, 1–14, and 1–28, avoiding separately trained 7-, 14-, and 28-day models unless later evidence justifies a protocol change.

| Partition | M5 keys | Calendar dates | Purpose |
| --- | --- | --- | --- |
| Train | `d_1`–`d_1885` | 2011-01-29–2016-03-27 | Fit model/baseline parameters |
| Validation | `d_1886`–`d_1913` | 2016-03-28–2016-04-24 | Select methods and hyperparameters using train + validation only |
| Test | `d_1914`–`d_1941` | 2016-04-25–2016-05-22 | One final held-out evaluation |

The raw sales file is wide: one item-store row followed by `d_1` through `d_1941`. A later preprocessing task will create the conceptual long-form records `date`, `item_id`, `sales`, `price`, calendar features, lag features, and rolling features. This checkpoint does not implement that transformation.

M5 supplies historical retail sales for thesis model development and evaluation. It does not provide Walmart on-hand inventory, replenishment, supplier lead time, or purchase-order history. Those inventory inputs will later be simulated under documented assumptions, and their results must be described as simulation results rather than observed Walmart inventory performance.

Frozen baseline plan for NEXT-006:

- **Seasonal Naive (primary naive):** same day in the preceding week (`lag_7`), which is more appropriate than a simple naive forecast for likely retail weekly seasonality.
- **28-day Moving Average:** a clearly documented moving-average baseline.
- **Auxiliary only:** simple naive (`lag_1`) may be retained as a reference, not the primary naive baseline.

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
