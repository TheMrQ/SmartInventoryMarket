# FEATURE_SET_V1 Summary

FEATURE_SET_V1 supports a global one-step regression model with recursive 28-step inference. No ML model was trained in this task.

## Scope and Resource Summary

- Frozen scope: `CA_1` / `FOODS`, 1437 SKU/item-store series.
- Train source: `d_1`–`d_1885` (1885 days).
- Model rows: 2,668,509; warm-up rows dropped: 40,236 (28 per series).
- Model feature count: 25.
- Feature-frame memory: 180.687 MiB; ignored local cache: 14.710 MiB.
- Generation duration: 33.969 seconds.

## Feature Groups

- Sales lags: `lag_1`, `lag_7`, `lag_14`, `lag_28`.
- Past-only rolling demand: means over 7/14/28 days and population standard deviations over 7/28 days; the latest permitted observation is `t-1`.
- Calendar: `wday`, `month`, `year`, `is_weekend`, `snap_CA`, and deterministic codes for both event-name/type pairs. TX/WI SNAP fields are excluded.
- Product identity: deterministic `item_code` and `dept_code`; M5 item IDs remain in the tracked mapping metadata.
- Price: `last_known_sell_price`, `price_lag_7`, `price_change_from_7_days_ago`, `price_available`, and `price_missing`.

## Missingness and Leakage Safeguards

- Nonzero missing counts: {'last_known_sell_price': 508049, 'price_lag_7': 512561, 'price_change_from_7_days_ago': 512561}.
- Warm-up policy: drop the first 28 days of every series because lag/rolling history is incomplete.
- Price policy: no backward fill and no target/future price feature. Pre-first-price history stays missing and is explicitly flagged.
- Recursive inference API receives only explicit history plus the target calendar row. Later steps must append prior predictions, never validation actual sales.
- TEST sales values were not read; validation sales values were not read.
