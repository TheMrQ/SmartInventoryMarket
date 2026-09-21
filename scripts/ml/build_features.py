"""Build the local, leakage-safe FEATURE_SET_V1 training matrix.

Only train sales targets through d_1885 are loaded. Validation calendar metadata
is used solely to prepare a later recursive forecast interface; no validation
or test sales values are read, predicted, or evaluated.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT))

from ml.data.m5_ca1_foods import load_training_feature_source
from ml.features.builder import (
    build_daily_price_matrix,
    build_training_features,
    load_feature_config,
    load_train_price_rows,
)


def _manifest(result, source, config, artifact_path: Path, elapsed_seconds: float) -> dict[str, object]:
    frame = result.frame
    missing_counts = {column: int(count) for column, count in frame.isna().sum().items() if int(count) > 0}
    return {
        "feature_set": config["feature_set"],
        "model_formulation": config["model_formulation"],
        "recursive_forecasting": config["recursive_forecasting"],
        "scope": {
            "store_id": "CA_1",
            "category_id": "FOODS",
            "series_count": len(source.metadata),
            "departments": sorted(source.metadata["dept_id"].astype(str).unique().tolist()),
        },
        "train_partition": {
            "start_d": source.train_day_keys[0],
            "end_d": source.train_day_keys[-1],
            "source_days": len(source.train_day_keys),
            "model_rows": len(frame),
            "dropped_warmup_rows": result.dropped_warmup_rows,
            "warmup_days_per_series": result.warmup_days,
        },
        "feature_count": len(result.feature_names),
        "feature_names": list(result.feature_names),
        "dtypes": {column: str(dtype) for column, dtype in frame.dtypes.items()},
        "missing_counts": missing_counts,
        "categorical_encodings": {
            "item_id": result.encodings.item_codes,
            "dept_id": result.encodings.dept_codes,
            "event_categories": result.encodings.event_codes,
        },
        "price_policy": "Current target-day prices are excluded. Within each item/store, only past observed prices are forward-filled; no backward fill is used. Missing price history remains NaN with price_available/price_missing indicators.",
        "test_access_policy": "Test sales values were not read. Validation sales values were not read. Only validation calendar metadata was loaded for future recursive inference support.",
        "local_artifact": {
            "path": "data/processed/m5_ca1_foods_features_v1.pkl.gz (Git-ignored)",
            "size_bytes": artifact_path.stat().st_size,
            "frame_memory_bytes": int(frame.memory_usage(deep=True).sum()),
        },
        "generation": {"elapsed_seconds": round(elapsed_seconds, 3)},
    }


def _write_summary(manifest: dict[str, object], output_path: Path) -> None:
    train = manifest["train_partition"]
    artifact = manifest["local_artifact"]
    missing = manifest["missing_counts"]
    lines = [
        "# FEATURE_SET_V1 Summary",
        "",
        "FEATURE_SET_V1 supports a global one-step regression model with recursive 28-step inference. No ML model was trained in this task.",
        "",
        "## Scope and Resource Summary",
        "",
        f"- Frozen scope: `CA_1` / `FOODS`, {manifest['scope']['series_count']} SKU/item-store series.",
        f"- Train source: `{train['start_d']}`–`{train['end_d']}` ({train['source_days']} days).",
        f"- Model rows: {train['model_rows']:,}; warm-up rows dropped: {train['dropped_warmup_rows']:,} ({train['warmup_days_per_series']} per series).",
        f"- Model feature count: {manifest['feature_count']}.",
        f"- Feature-frame memory: {artifact['frame_memory_bytes'] / 1024 / 1024:.3f} MiB; ignored local cache: {artifact['size_bytes'] / 1024 / 1024:.3f} MiB.",
        f"- Generation duration: {manifest['generation']['elapsed_seconds']:.3f} seconds.",
        "",
        "## Feature Groups",
        "",
        "- Sales lags: `lag_1`, `lag_7`, `lag_14`, `lag_28`.",
        "- Past-only rolling demand: means over 7/14/28 days and population standard deviations over 7/28 days; the latest permitted observation is `t-1`.",
        "- Calendar: `wday`, `month`, `year`, `is_weekend`, `snap_CA`, and deterministic codes for both event-name/type pairs. TX/WI SNAP fields are excluded.",
        "- Product identity: deterministic `item_code` and `dept_code`; M5 item IDs remain in the tracked mapping metadata.",
        "- Price: `last_known_sell_price`, `price_lag_7`, `price_change_from_7_days_ago`, `price_available`, and `price_missing`.",
        "",
        "## Missingness and Leakage Safeguards",
        "",
        f"- Nonzero missing counts: {missing if missing else 'none'}.",
        "- Warm-up policy: drop the first 28 days of every series because lag/rolling history is incomplete.",
        "- Price policy: no backward fill and no target/future price feature. Pre-first-price history stays missing and is explicitly flagged.",
        "- Recursive inference API receives only explicit history plus the target calendar row. Later steps must append prior predictions, never validation actual sales.",
        "- TEST sales values were not read; validation sales values were not read.",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=REPOSITORY_ROOT / "data/raw/m5")
    parser.add_argument("--protocol", type=Path, default=REPOSITORY_ROOT / "configs/data/m5_ca1_foods.yaml")
    parser.add_argument("--feature-config", type=Path, default=REPOSITORY_ROOT / "configs/features/ml_features_v1.yaml")
    parser.add_argument("--artifact", type=Path, default=REPOSITORY_ROOT / "data/processed/m5_ca1_foods_features_v1.pkl.gz")
    parser.add_argument("--manifest", type=Path, default=REPOSITORY_ROOT / "data/manifests/m5_ca1_foods_features_v1.json")
    parser.add_argument("--summary", type=Path, default=REPOSITORY_ROOT / "reports/tables/feature_set_v1_summary.md")
    args = parser.parse_args()

    started = time.perf_counter()
    config = load_feature_config(args.feature_config)
    source = load_training_feature_source(args.raw_dir, args.protocol)
    item_ids = tuple(source.metadata["item_id"].astype(str))
    price_rows = load_train_price_rows(args.raw_dir, item_ids, source.train_calendar)
    prices = build_daily_price_matrix(price_rows, item_ids, source.train_calendar)
    calendar_metadata = pd.concat([source.train_calendar, source.validation_calendar], ignore_index=True)
    result = build_training_features(
        source.metadata,
        source.train_sales,
        source.train_calendar,
        calendar_metadata,
        prices,
        config,
    )
    args.artifact.parent.mkdir(parents=True, exist_ok=True)
    result.frame.to_pickle(args.artifact, compression="gzip")
    elapsed = time.perf_counter() - started
    manifest = _manifest(result, source, config, args.artifact, elapsed)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    _write_summary(manifest, args.summary)
    print(f"Built {manifest['train_partition']['model_rows']:,} FEATURE_SET_V1 train rows with {manifest['feature_count']} features.")
    print(f"Wrote Git-ignored local cache: {args.artifact}")
    print("Validation and TEST sales values were not read.")


if __name__ == "__main__":
    main()
