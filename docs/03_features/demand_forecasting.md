# Demand Forecasting

Status: `TODO` — no dataset, features, models, or experiments have been implemented.

## Dataset and Models

Primary dataset candidate: **M5 Forecasting - Accuracy**.

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

## Definition of Done

Official training and evaluation must be reproducible and script-based, not notebook-driven. Runs must record configuration, seed, dataset version/subset, chronological split, feature set, model parameters, metrics, Git commit, and artifact paths. Models must be evaluated against baselines before use in inventory recommendations.
