# Demand Forecasting

Status: `TODO` — no dataset, features, models, or experiments have been implemented.

## Dataset and Models

Official forecasting dataset: **M5 Forecasting - Accuracy**.

M5 supplies historical retail sales for thesis model development and evaluation. It does not provide Walmart on-hand inventory, replenishment, supplier lead time, or purchase-order history. Those inventory inputs will later be simulated under documented assumptions, and their results must be described as simulation results rather than observed Walmart inventory performance.

Planned baselines:

- Naive
- Moving Average

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

## Evaluation Rule

**No random train/test split.** All forecasting work must use chronological train, validation, and test periods to prevent future leakage.

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
