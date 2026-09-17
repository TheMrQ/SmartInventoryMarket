"""Create a memory-conscious local audit of M5 Forecasting - Accuracy files.

This script performs metadata and quality inspection only.  It does not train a
model, create forecasting features, or choose a final experimental subset.
Raw source data remains in the Git-ignored ``data/raw/m5`` directory; outputs
contain aggregated metadata only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sqlite3
import sys
import tempfile
import time
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


EXPECTED_FILES = (
    "calendar.csv",
    "sales_train_evaluation.csv",
    "sales_train_validation.csv",
    "sample_submission.csv",
    "sell_prices.csv",
)
SALES_IDENTIFIER_COLUMNS = ("id", "item_id", "dept_id", "cat_id", "store_id", "state_id")


def json_default(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def mib(byte_count: int | float) -> float:
    return round(float(byte_count) / (1024 * 1024), 3)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def csv_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as source:
        return next(csv.reader(source))


def percentile_from_histogram(histogram: Counter[int], percentile: float) -> int:
    total = sum(histogram.values())
    if not total:
        return 0
    threshold = math.ceil(total * percentile)
    cumulative = 0
    for value in sorted(histogram):
        cumulative += histogram[value]
        if cumulative >= threshold:
            return int(value)
    return int(max(histogram))


def daterange_entry(calendar: pd.DataFrame, day_key: str) -> str | None:
    match = calendar.loc[calendar["d"] == day_key, "date"]
    return str(match.iloc[0].date()) if not match.empty else None


def audit_sales(path: Path, chunksize: int) -> tuple[dict[str, Any], pd.DataFrame, dict[str, dict[str, int]]]:
    header = csv_header(path)
    day_columns = [column for column in header if column.startswith("d_")]
    identifier_columns = [column for column in SALES_IDENTIFIER_COLUMNS if column in header]
    if len(identifier_columns) != len(SALES_IDENTIFIER_COLUMNS) or not day_columns:
        raise ValueError(f"Unexpected sales schema in {path.name}")

    identifiers = pd.read_csv(path, usecols=identifier_columns, dtype="string")
    duplicate_series = int(identifiers.duplicated(subset=["item_id", "store_id"]).sum())
    unique_items = identifiers["item_id"].nunique()
    product_by_category = (
        identifiers[["item_id", "cat_id"]].drop_duplicates().groupby("cat_id")["item_id"].nunique().sort_index()
    )
    product_by_department = (
        identifiers[["item_id", "dept_id"]].drop_duplicates().groupby("dept_id")["item_id"].nunique().sort_index()
    )
    series_by_store = identifiers.groupby("store_id").size().sort_index()
    series_by_store_category = identifiers.groupby(["store_id", "cat_id"]).size().sort_index()
    series_by_store_dept = identifiers.groupby(["store_id", "dept_id"]).size().sort_index()

    total_cells = total_sales = zero_cells = negative_cells = missing_cells = 0
    minimum: int | None = None
    maximum: int | None = None
    histogram: Counter[int] = Counter()
    by_store_category: dict[str, dict[str, int]] = defaultdict(lambda: {"cells": 0, "zeros": 0})
    by_store_department: dict[str, dict[str, int]] = defaultdict(lambda: {"cells": 0, "zeros": 0})

    for chunk in pd.read_csv(path, usecols=header, chunksize=chunksize):
        chunk = chunk.reset_index(drop=True)
        values = chunk[day_columns].to_numpy()
        missing_cells += int(pd.isna(values).sum())
        numeric = np.nan_to_num(values, nan=0).astype(np.int64, copy=False)
        total_cells += int(numeric.size)
        total_sales += int(numeric.sum())
        zero_cells += int((numeric == 0).sum())
        negative_cells += int((numeric < 0).sum())
        current_min = int(numeric.min())
        current_max = int(numeric.max())
        minimum = current_min if minimum is None else min(minimum, current_min)
        maximum = current_max if maximum is None else max(maximum, current_max)
        unique_values, counts = np.unique(numeric, return_counts=True)
        histogram.update({int(value): int(count) for value, count in zip(unique_values, counts, strict=True)})

        for (store_id, cat_id), positions in chunk.groupby(["store_id", "cat_id"], sort=False).groups.items():
            group_values = numeric[np.fromiter(positions, dtype=np.intp)]
            key = f"{store_id}|{cat_id}"
            by_store_category[key]["cells"] += int(group_values.size)
            by_store_category[key]["zeros"] += int((group_values == 0).sum())
        for (store_id, dept_id), positions in chunk.groupby(["store_id", "dept_id"], sort=False).groups.items():
            group_values = numeric[np.fromiter(positions, dtype=np.intp)]
            key = f"{store_id}|{dept_id}"
            by_store_department[key]["cells"] += int(group_values.size)
            by_store_department[key]["zeros"] += int((group_values == 0).sum())

    distribution = {
        "min": minimum,
        "max": maximum,
        "mean": round(total_sales / total_cells, 6) if total_cells else None,
        "p50": percentile_from_histogram(histogram, 0.50),
        "p95": percentile_from_histogram(histogram, 0.95),
        "p99": percentile_from_histogram(histogram, 0.99),
    }
    audit = {
        "row_count": int(len(identifiers)),
        "column_count": len(header),
        "identifier_columns": identifier_columns,
        "day_column_count": len(day_columns),
        "first_day_key": day_columns[0],
        "last_day_key": day_columns[-1],
        "unique_items": int(unique_items),
        "unique_departments": int(identifiers["dept_id"].nunique()),
        "unique_categories": int(identifiers["cat_id"].nunique()),
        "unique_stores": int(identifiers["store_id"].nunique()),
        "unique_states": int(identifiers["state_id"].nunique()),
        "item_store_series": int(len(identifiers)),
        "duplicate_item_store_keys": duplicate_series,
        "sales_quality": {
            "cell_count": total_cells,
            "missing_cells": missing_cells,
            "negative_cells": negative_cells,
            "zero_cells": zero_cells,
            "zero_prevalence": round(zero_cells / total_cells, 6) if total_cells else None,
            "distribution": distribution,
        },
        "product_counts_by_category": {str(key): int(value) for key, value in product_by_category.items()},
        "product_counts_by_department": {str(key): int(value) for key, value in product_by_department.items()},
        "series_counts_by_store": {str(key): int(value) for key, value in series_by_store.items()},
        "series_counts_by_store_category": {f"{store}|{category}": int(value) for (store, category), value in series_by_store_category.items()},
        "series_counts_by_store_department": {f"{store}|{department}": int(value) for (store, department), value in series_by_store_dept.items()},
    }
    group_quality = {
        "store_category": dict(by_store_category),
        "store_department": dict(by_store_department),
    }
    return audit, identifiers, group_quality


def audit_calendar(path: Path, sales_day_keys: tuple[str, str]) -> tuple[dict[str, Any], pd.DataFrame]:
    calendar = pd.read_csv(path)
    event_columns = [column for column in ("event_name_1", "event_type_1", "event_name_2", "event_type_2") if column in calendar]
    snap_columns = [column for column in calendar.columns if column.startswith("snap_")]
    calendar["date"] = pd.to_datetime(calendar["date"])
    audit = {
        "row_count": int(len(calendar)),
        "column_count": len(calendar.columns),
        "columns": list(calendar.columns),
        "date_range": {"first": str(calendar["date"].min().date()), "last": str(calendar["date"].max().date())},
        "d_key_range": {"first": str(calendar["d"].iloc[0]), "last": str(calendar["d"].iloc[-1])},
        "sales_day_mapping": {
            sales_day_keys[0]: daterange_entry(calendar, sales_day_keys[0]),
            sales_day_keys[1]: daterange_entry(calendar, sales_day_keys[1]),
        },
        "event_columns": event_columns,
        "event_missing_values": {column: int(calendar[column].isna().sum()) for column in event_columns},
        "snap_columns": snap_columns,
        "duplicate_d_keys": int(calendar["d"].duplicated().sum()),
        "duplicate_dates": int(calendar["date"].duplicated().sum()),
        "wm_yr_wk_unique_count": int(calendar["wm_yr_wk"].nunique()),
        "weekday_wday_month_year_columns": [column for column in ("weekday", "wday", "month", "year") if column in calendar],
    }
    return audit, calendar


def audit_prices(path: Path, chunksize: int) -> dict[str, Any]:
    header = csv_header(path)
    expected = {"store_id", "item_id", "wm_yr_wk", "sell_price"}
    if not expected.issubset(header):
        raise ValueError(f"Unexpected price schema in {path.name}")

    row_count = missing = zero_prices = negative_prices = duplicate_keys = 0
    min_price: float | None = None
    max_price: float | None = None
    stores: set[str] = set()
    items: set[str] = set()
    weeks: set[int] = set()

    with tempfile.TemporaryDirectory(prefix="m5_price_audit_") as temporary_directory:
        database = Path(temporary_directory) / "price_keys.sqlite"
        connection = sqlite3.connect(database)
        connection.execute("PRAGMA journal_mode=OFF")
        connection.execute("PRAGMA synchronous=OFF")
        connection.execute("PRAGMA temp_store=FILE")
        connection.execute(
            "CREATE TABLE price_key (store_id TEXT, item_id TEXT, wm_yr_wk INTEGER, "
            "PRIMARY KEY (store_id, item_id, wm_yr_wk)) WITHOUT ROWID"
        )
        try:
            for chunk in pd.read_csv(path, chunksize=chunksize, dtype={"store_id": "string", "item_id": "string"}):
                row_count += len(chunk)
                missing += int(chunk[["store_id", "item_id", "wm_yr_wk", "sell_price"]].isna().sum().sum())
                prices = pd.to_numeric(chunk["sell_price"], errors="coerce")
                valid_prices = prices.dropna()
                if not valid_prices.empty:
                    current_min = float(valid_prices.min())
                    current_max = float(valid_prices.max())
                    min_price = current_min if min_price is None else min(min_price, current_min)
                    max_price = current_max if max_price is None else max(max_price, current_max)
                    zero_prices += int((valid_prices == 0).sum())
                    negative_prices += int((valid_prices < 0).sum())
                stores.update(chunk["store_id"].dropna().astype(str).unique())
                items.update(chunk["item_id"].dropna().astype(str).unique())
                weeks.update(int(value) for value in chunk["wm_yr_wk"].dropna().unique())
                records = list(chunk[["store_id", "item_id", "wm_yr_wk"]].dropna().itertuples(index=False, name=None))
                before = connection.total_changes
                connection.executemany("INSERT OR IGNORE INTO price_key VALUES (?, ?, ?)", records)
                duplicate_keys += len(records) - (connection.total_changes - before)
            connection.commit()
        finally:
            connection.close()

    return {
        "row_count": int(row_count),
        "column_count": len(header),
        "columns": header,
        "unique_stores": len(stores),
        "unique_items": len(items),
        "unique_weeks": len(weeks),
        "missing_values_important_fields": missing,
        "minimum_sell_price": min_price,
        "maximum_sell_price": max_price,
        "zero_sell_prices": zero_prices,
        "negative_sell_prices": negative_prices,
        "duplicate_store_item_week_keys": duplicate_keys,
        "join_note": "Join sales item_id/store_id to calendar wm_yr_wk, then join on item_id/store_id/wm_yr_wk.",
    }


def candidate_subsets(
    identifiers: pd.DataFrame,
    day_count: int,
    group_quality: dict[str, dict[str, dict[str, int]]],
) -> list[dict[str, Any]]:
    foods = identifiers.loc[identifiers["cat_id"] == "FOODS"]
    representative_stores: list[str] = []
    for state in sorted(foods["state_id"].unique()):
        representative_stores.append(sorted(foods.loc[foods["state_id"] == state, "store_id"].unique())[0])
    largest_food_department = (
        foods[["item_id", "dept_id"]].drop_duplicates().groupby("dept_id")["item_id"].nunique().sort_values(ascending=False).index[0]
    )
    selections: list[tuple[str, str, str | None]] = [(store, "FOODS", None) for store in representative_stores]
    selections.append((representative_stores[-1], "FOODS", str(largest_food_department)))

    candidates: list[dict[str, Any]] = []
    for store, category, department in selections:
        subset = identifiers.loc[(identifiers["store_id"] == store) & (identifiers["cat_id"] == category)]
        if department:
            subset = subset.loc[subset["dept_id"] == department]
            quality = group_quality["store_department"][f"{store}|{department}"]
        else:
            quality = group_quality["store_category"][f"{store}|{category}"]
        series_count = int(len(subset))
        candidates.append(
            {
                "store": store,
                "category": category,
                "department": department,
                "item_count": int(subset["item_id"].nunique()),
                "series_count": series_count,
                "history_days": day_count,
                "long_format_rows": series_count * day_count,
                "zero_sales_prevalence": round(quality["zeros"] / quality["cells"], 6),
                "estimated_int32_sales_payload_mib": mib(series_count * day_count * 4),
                "status": "CANDIDATE ONLY — not selected or ranked",
            }
        )
    return candidates


def split_candidates(calendar: pd.DataFrame) -> list[dict[str, Any]]:
    plans = ((7, 1927, 1928, 1934, 1935, 1941), (14, 1913, 1914, 1927, 1928, 1941), (28, 1885, 1886, 1913, 1914, 1941))
    candidates = []
    for horizon, train_end, validation_start, validation_end, test_start, test_end in plans:
        candidates.append(
            {
                "horizon_days": horizon,
                "train": {"start": "d_1", "end": f"d_{train_end}", "end_date": daterange_entry(calendar, f"d_{train_end}")},
                "validation": {"start": f"d_{validation_start}", "end": f"d_{validation_end}", "days": horizon, "start_date": daterange_entry(calendar, f"d_{validation_start}"), "end_date": daterange_entry(calendar, f"d_{validation_end}")},
                "test": {"start": f"d_{test_start}", "end": f"d_{test_end}", "days": horizon, "start_date": daterange_entry(calendar, f"d_{test_start}"), "end_date": daterange_entry(calendar, f"d_{test_end}")},
                "status": "CANDIDATE ONLY — chronological and not frozen",
            }
        )
    return candidates


def write_summary(path: Path, audit: dict[str, Any]) -> None:
    sales = audit["sales_files"]["sales_train_evaluation.csv"]
    calendar = audit["calendar"]
    prices = audit["sell_prices"]
    lines = [
        "# M5 Local Audit Summary",
        "",
        "This generated report contains aggregate metadata only; it has no raw M5 records.",
        "",
        "## Verified Local Findings",
        "",
        f"- Extracted raw CSV size: {audit['resource_audit']['extracted_csv_size_mib']} MiB; archive: {audit['resource_audit']['archive_size_mib']} MiB.",
        f"- Evaluation sales: {sales['row_count']:,} item-store series × {sales['day_column_count']:,} daily columns ({sales['first_day_key']} to {sales['last_day_key']}).",
        f"- Calendar: {calendar['date_range']['first']} to {calendar['date_range']['last']}; evaluation sales ends {calendar['sales_day_mapping'][sales['last_day_key']]}.",
        f"- Stores/items/categories/departments: {sales['unique_stores']}/{sales['unique_items']}/{sales['unique_categories']}/{sales['unique_departments']}.",
        f"- Zero sales prevalence: {sales['sales_quality']['zero_prevalence']:.2%}; negative sales cells: {sales['sales_quality']['negative_cells']:,}.",
        f"- Prices: {prices['row_count']:,} rows, range {prices['minimum_sell_price']} to {prices['maximum_sell_price']}, duplicate keys {prices['duplicate_store_item_week_keys']:,}.",
        "",
        "## Candidate Subsets (Not Selected)",
        "",
        "| Store | Category | Department | Items | Series | Days | Zero sales | Estimated int32 payload MiB |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for candidate in audit["subset_candidates"]:
        lines.append(
            f"| {candidate['store']} | {candidate['category']} | {candidate['department'] or 'All'} | "
            f"{candidate['item_count']:,} | {candidate['series_count']:,} | {candidate['history_days']:,} | "
            f"{candidate['zero_sales_prevalence']:.2%} | {candidate['estimated_int32_sales_payload_mib']} |"
        )
    lines.extend(["", "Final subset, horizon, and split selection belongs to NEXT-005.", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/m5"))
    parser.add_argument("--manifest-dir", type=Path, default=Path("data/manifests"))
    parser.add_argument("--report-path", type=Path, default=Path("reports/tables/m5_audit_summary.md"))
    parser.add_argument("--sales-chunksize", type=int, default=500, help="CSV rows per sales audit chunk")
    parser.add_argument("--price-chunksize", type=int, default=100_000, help="CSV rows per price audit chunk")
    arguments = parser.parse_args()

    raw_dir = arguments.raw_dir.resolve()
    missing = [name for name in EXPECTED_FILES if not (raw_dir / name).is_file()]
    if missing:
        parser.error(f"Missing expected M5 files in {raw_dir}: {', '.join(missing)}")
    arguments.manifest_dir.mkdir(parents=True, exist_ok=True)
    arguments.report_path.parent.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    validation_path = raw_dir / "sales_train_validation.csv"
    evaluation_path = raw_dir / "sales_train_evaluation.csv"
    validation, _, _ = audit_sales(validation_path, arguments.sales_chunksize)
    evaluation, identifiers, group_quality = audit_sales(evaluation_path, arguments.sales_chunksize)
    calendar, calendar_frame = audit_calendar(raw_dir / "calendar.csv", (evaluation["first_day_key"], evaluation["last_day_key"]))
    prices = audit_prices(raw_dir / "sell_prices.csv", arguments.price_chunksize)

    default_sample = pd.read_csv(evaluation_path, nrows=min(arguments.sales_chunksize, evaluation["row_count"]))
    optimized_sample = pd.read_csv(
        evaluation_path,
        nrows=min(arguments.sales_chunksize, evaluation["row_count"]),
        dtype={column: "int32" for column in [column for column in csv_header(evaluation_path) if column.startswith("d_")]},
    )
    archive_files = sorted(raw_dir.glob("*.zip"))
    archive_size = sum(path.stat().st_size for path in archive_files)
    csv_size = sum((raw_dir / name).stat().st_size for name in EXPECTED_FILES)
    largest = max([raw_dir / name for name in EXPECTED_FILES], key=lambda path: path.stat().st_size)
    sample_rows = len(default_sample)
    resource_audit = {
        "archive_files": [{"filename": path.name, "size_bytes": path.stat().st_size, "size_mib": mib(path.stat().st_size)} for path in archive_files],
        "archive_size_bytes": archive_size,
        "archive_size_mib": mib(archive_size),
        "extracted_csv_size_bytes": csv_size,
        "extracted_csv_size_mib": mib(csv_size),
        "largest_file": {"filename": largest.name, "size_bytes": largest.stat().st_size, "size_mib": mib(largest.stat().st_size)},
        "representative_sales_read": {
            "sample_rows": sample_rows,
            "default_pandas_memory_bytes": int(default_sample.memory_usage(deep=True).sum()),
            "int32_day_columns_memory_bytes": int(optimized_sample.memory_usage(deep=True).sum()),
            "projected_default_full_sales_memory_mib": mib(default_sample.memory_usage(deep=True).sum() / sample_rows * evaluation["row_count"]),
            "projected_int32_full_sales_memory_mib": mib(optimized_sample.memory_usage(deep=True).sum() / sample_rows * evaluation["row_count"]),
        },
        "recommendation": "One optimized sales CSV may be practical on a typical development machine, but do not load both sales files and prices together. Use chunking/subsetting for audit and future feature work.",
    }

    file_manifest: dict[str, Any] = {"source": "Kaggle competition m5-forecasting-accuracy", "acquired_date": datetime.now(UTC).date().isoformat(), "files": []}
    audited_rows = {
        "sales_train_validation.csv": validation["row_count"],
        "sales_train_evaluation.csv": evaluation["row_count"],
        "calendar.csv": calendar["row_count"],
        "sell_prices.csv": prices["row_count"],
    }
    audited_columns = {
        "sales_train_validation.csv": validation["column_count"],
        "sales_train_evaluation.csv": evaluation["column_count"],
        "calendar.csv": calendar["column_count"],
        "sell_prices.csv": prices["column_count"],
    }
    for name in EXPECTED_FILES:
        path = raw_dir / name
        header = csv_header(path)
        entry = {
            "filename": name,
            "size_bytes": path.stat().st_size,
            "size_mib": mib(path.stat().st_size),
            "column_count": audited_columns.get(name, len(header)),
            "row_count": audited_rows.get(name),
            "first_columns": header[:8],
            "last_columns": header[-8:],
            "sha256": sha256(path),
        }
        if name == "sample_submission.csv":
            with path.open("r", encoding="utf-8", newline="") as source:
                entry["row_count"] = max(sum(1 for _ in source) - 1, 0)
        file_manifest["files"].append(entry)
    file_manifest["total_extracted_csv_size_bytes"] = csv_size
    file_manifest["total_extracted_csv_size_mib"] = mib(csv_size)

    audit = {
        "audit_metadata": {
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "script": "scripts/data/audit_m5.py",
            "source": "Kaggle competition m5-forecasting-accuracy",
            "raw_directory": "data/raw/m5 (Git-ignored)",
            "python_version": sys.version.split()[0],
            "pandas_version": pd.__version__,
            "sales_chunksize": arguments.sales_chunksize,
            "price_chunksize": arguments.price_chunksize,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "scope": "metadata/schema/resource audit only; no training, features, or final protocol selection",
        },
        "sales_files": {"sales_train_validation.csv": validation, "sales_train_evaluation.csv": evaluation},
        "sales_file_difference": {
            "validation_last_day_key": validation["last_day_key"],
            "evaluation_last_day_key": evaluation["last_day_key"],
            "additional_evaluation_day_columns": evaluation["day_column_count"] - validation["day_column_count"],
            "identifier_schema_matches": validation["identifier_columns"] == evaluation["identifier_columns"],
        },
        "calendar": calendar,
        "sell_prices": prices,
        "resource_audit": resource_audit,
        "subset_candidates": candidate_subsets(identifiers, evaluation["day_column_count"], group_quality),
        "horizon_feasibility": {
            "7_days": "Feasible: evaluation sales includes observed labels through d_1941; use chronological 7-day holdouts.",
            "14_days": "Feasible: evaluation sales includes observed labels through d_1941; use chronological 14-day holdouts.",
            "28_days": "Feasible: evaluation sales includes observed labels through d_1941; use chronological 28-day holdouts consistent with M5 competition framing.",
            "status": "All are technically feasible; horizon is not selected by this audit.",
        },
        "chronological_split_candidates": split_candidates(calendar_frame),
        "interpretation_limitations": [
            "Observed sales equal to zero does not prove true demand was zero.",
            "Observed sales equal to zero does not imply inventory was zero.",
            "M5 has no observed on-hand inventory, replenishment, supplier lead time, or purchase-order history; later inventory evaluation is a documented simulation.",
        ],
    }
    manifest_path = arguments.manifest_dir / "m5_file_manifest.json"
    audit_path = arguments.manifest_dir / "m5_audit.json"
    manifest_path.write_text(json.dumps(file_manifest, indent=2, sort_keys=True, default=json_default) + "\n", encoding="utf-8")
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True, default=json_default) + "\n", encoding="utf-8")
    write_summary(arguments.report_path, audit)
    print(f"Wrote {manifest_path}")
    print(f"Wrote {audit_path}")
    print(f"Wrote {arguments.report_path}")
    print(f"Audit completed in {audit['audit_metadata']['elapsed_seconds']} seconds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
