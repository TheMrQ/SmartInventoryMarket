"""Leakage-safe loading for the frozen M5 CA_1/FOODS protocol.

The preparation manifest checks the full protocol structurally, including the
sealed test column names and calendar dates. Validation experiments intentionally
load sales *values* only through ``d_1913`` and therefore cannot evaluate test.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml


IDENTIFIER_COLUMNS = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]


@dataclass(frozen=True)
class ValidationDataset:
    """Frozen scope sales values available to validation-only experiments."""

    item_ids: tuple[str, ...]
    train_sales: np.ndarray
    validation_actuals: np.ndarray
    train_day_keys: tuple[str, ...]
    validation_day_keys: tuple[str, ...]
    validation_dates: tuple[str, ...]


@dataclass(frozen=True)
class TrainingFeatureSource:
    """Train sales plus calendar metadata for leakage-safe feature construction."""

    metadata: pd.DataFrame
    train_sales: np.ndarray
    train_calendar: pd.DataFrame
    validation_calendar: pd.DataFrame
    train_day_keys: tuple[str, ...]


def load_protocol(config_path: str | Path) -> dict[str, Any]:
    """Load and validate the version-controlled frozen protocol."""
    with Path(config_path).open(encoding="utf-8") as file:
        protocol = yaml.safe_load(file)
    if not isinstance(protocol, dict):
        raise ValueError("The M5 protocol YAML must contain a mapping.")
    required = {
        "source_sales_file",
        "store_id",
        "category_id",
        "departments",
        "expected_item_store_series",
        "forecast_horizon_days",
        "train",
        "validation",
        "test",
    }
    missing = required.difference(protocol)
    if missing:
        raise ValueError(f"M5 protocol is missing keys: {sorted(missing)}")
    if protocol["forecast_horizon_days"] != 28:
        raise ValueError("The frozen M5 protocol requires a 28-day horizon.")
    return protocol


def day_keys(start_day: str, end_day: str) -> tuple[str, ...]:
    """Return inclusive M5 day keys and reject malformed/reversed ranges."""
    try:
        start = int(start_day.removeprefix("d_"))
        end = int(end_day.removeprefix("d_"))
    except ValueError as exc:
        raise ValueError(f"Invalid M5 day range: {start_day} to {end_day}") from exc
    if not start_day.startswith("d_") or not end_day.startswith("d_") or start > end:
        raise ValueError(f"Invalid M5 day range: {start_day} to {end_day}")
    return tuple(f"d_{day}" for day in range(start, end + 1))


def select_frozen_scope(metadata: pd.DataFrame, protocol: dict[str, Any]) -> pd.DataFrame:
    """Filter metadata and verify the exact store/category/department scope."""
    required = {"item_id", "dept_id", "cat_id", "store_id"}
    missing = required.difference(metadata.columns)
    if missing:
        raise ValueError(f"Sales metadata is missing columns: {sorted(missing)}")

    selected = metadata.loc[
        (metadata["store_id"] == protocol["store_id"])
        & (metadata["cat_id"] == protocol["category_id"])
        & (metadata["dept_id"].isin(protocol["departments"]))
    ].copy()
    expected = int(protocol["expected_item_store_series"])
    if len(selected) != expected or selected["item_id"].nunique() != expected:
        raise ValueError(
            "Frozen scope cardinality mismatch: "
            f"rows={len(selected)}, unique_items={selected['item_id'].nunique()}, expected={expected}."
        )
    if set(selected["dept_id"].unique()) != set(protocol["departments"]):
        raise ValueError("Frozen scope does not contain exactly the configured departments.")
    return selected


def _source_paths(raw_directory: str | Path, protocol: dict[str, Any]) -> tuple[Path, Path]:
    raw_path = Path(raw_directory)
    sales_path = raw_path / protocol["source_sales_file"]
    calendar_path = raw_path / "calendar.csv"
    for path in (sales_path, calendar_path):
        if not path.is_file():
            raise FileNotFoundError(f"Required local M5 file is missing: {path}")
    return sales_path, calendar_path


def _read_header(sales_path: Path) -> list[str]:
    return pd.read_csv(sales_path, nrows=0).columns.tolist()


def _validate_header(header: list[str], protocol: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    required_days = {
        "train": day_keys(protocol["train"]["start_d"], protocol["train"]["end_d"]),
        "validation": day_keys(protocol["validation"]["start_d"], protocol["validation"]["end_d"]),
        "test": day_keys(protocol["test"]["start_d"], protocol["test"]["end_d"]),
    }
    missing_identifiers = set(IDENTIFIER_COLUMNS).difference(header)
    missing_days = [day for days in required_days.values() for day in days if day not in header]
    if missing_identifiers or missing_days:
        raise ValueError(
            f"M5 evaluation sales file does not match the frozen protocol; "
            f"missing identifiers={sorted(missing_identifiers)}, missing day keys={missing_days[:5]}."
        )
    return required_days


def _calendar_dates(calendar_path: Path, required_days: tuple[str, ...]) -> dict[str, str]:
    calendar = pd.read_csv(calendar_path, usecols=["d", "date"], dtype={"d": "string", "date": "string"})
    dates = calendar.set_index("d")["date"].to_dict()
    missing = [day for day in required_days if day not in dates]
    if missing:
        raise ValueError(f"calendar.csv is missing M5 keys: {missing[:5]}")
    return {day: str(dates[day]) for day in required_days}


def build_preparation_manifest(raw_directory: str | Path, config_path: str | Path) -> dict[str, Any]:
    """Validate the full frozen protocol without reading any daily sales values.

    Test columns are checked by name and date only. This preserves the test set
    for final forecasting evaluation while confirming the configured split exists.
    """
    protocol = load_protocol(config_path)
    sales_path, calendar_path = _source_paths(raw_directory, protocol)
    partition_days = _validate_header(_read_header(sales_path), protocol)
    metadata = pd.read_csv(sales_path, usecols=IDENTIFIER_COLUMNS, dtype="string")
    selected = select_frozen_scope(metadata, protocol)
    all_required_days = tuple(day for partition in ("train", "validation", "test") for day in partition_days[partition])
    dates = _calendar_dates(calendar_path, all_required_days)

    for partition in ("train", "validation", "test"):
        configured = protocol[partition]
        first, last = partition_days[partition][0], partition_days[partition][-1]
        if dates[first] != configured["start_date"] or dates[last] != configured["end_date"]:
            raise ValueError(f"Calendar mapping does not match frozen {partition} dates.")

    return {
        "scope": {
            "store_id": protocol["store_id"],
            "category_id": protocol["category_id"],
            "departments": protocol["departments"],
            "item_store_series": len(selected),
            "unique_item_ids": int(selected["item_id"].nunique()),
        },
        "source": {
            "sales_file": protocol["source_sales_file"],
            "raw_location": "data/raw/m5 (Git-ignored)",
            "daily_sales_values_read": False,
        },
        "partitions": {
            name: {
                "start_d": days[0],
                "end_d": days[-1],
                "days": len(days),
                "start_date": dates[days[0]],
                "end_date": dates[days[-1]],
            }
            for name, days in partition_days.items()
        },
        "test_access_policy": "Test sales values were not read; only configured column names and calendar dates were structurally verified.",
    }


def load_validation_dataset(raw_directory: str | Path, config_path: str | Path) -> ValidationDataset:
    """Load only training and validation sales values for fixed-origin baselines.

    The selected CSV columns stop at ``d_1913``. No test sales values are read.
    """
    protocol = load_protocol(config_path)
    sales_path, calendar_path = _source_paths(raw_directory, protocol)
    partition_days = _validate_header(_read_header(sales_path), protocol)
    train_days = partition_days["train"]
    validation_days = partition_days["validation"]
    usecols = IDENTIFIER_COLUMNS + list(train_days) + list(validation_days)
    sales = pd.read_csv(sales_path, usecols=usecols, dtype={column: "int32" for column in train_days + validation_days})
    selected = select_frozen_scope(sales, protocol)
    dates = _calendar_dates(calendar_path, validation_days)

    return ValidationDataset(
        item_ids=tuple(selected["item_id"].astype(str)),
        train_sales=selected.loc[:, list(train_days)].to_numpy(dtype=np.float64),
        validation_actuals=selected.loc[:, list(validation_days)].to_numpy(dtype=np.float64),
        train_day_keys=train_days,
        validation_day_keys=validation_days,
        validation_dates=tuple(dates[day] for day in validation_days),
    )


def load_training_feature_source(raw_directory: str | Path, config_path: str | Path) -> TrainingFeatureSource:
    """Load only train sales targets plus train/validation calendar metadata.

    Validation calendar data is non-target information needed for a later
    recursive forecast. Validation and test *sales values* are never read.
    """
    protocol = load_protocol(config_path)
    sales_path, calendar_path = _source_paths(raw_directory, protocol)
    partition_days = _validate_header(_read_header(sales_path), protocol)
    train_days = partition_days["train"]
    usecols = IDENTIFIER_COLUMNS + list(train_days)
    sales = pd.read_csv(sales_path, usecols=usecols, dtype={column: "int16" for column in train_days})
    selected = select_frozen_scope(sales, protocol).sort_values("item_id", kind="stable").reset_index(drop=True)

    calendar_columns = [
        "date",
        "wm_yr_wk",
        "weekday",
        "wday",
        "month",
        "year",
        "d",
        "event_name_1",
        "event_type_1",
        "event_name_2",
        "event_type_2",
        "snap_CA",
    ]
    calendar = pd.read_csv(calendar_path, usecols=calendar_columns)
    calendar["d_index"] = calendar["d"].str.removeprefix("d_").astype("int16")
    calendar = calendar.sort_values("d_index", kind="stable")
    train_calendar = calendar.loc[calendar["d"].isin(train_days)].reset_index(drop=True)
    validation_calendar = calendar.loc[calendar["d"].isin(partition_days["validation"])].reset_index(drop=True)
    if tuple(train_calendar["d"]) != train_days:
        raise ValueError("calendar.csv train keys do not match the frozen protocol.")
    if tuple(validation_calendar["d"]) != partition_days["validation"]:
        raise ValueError("calendar.csv validation keys do not match the frozen protocol.")
    if train_calendar.iloc[0]["date"] != protocol["train"]["start_date"] or train_calendar.iloc[-1]["date"] != protocol["train"]["end_date"]:
        raise ValueError("calendar.csv train dates do not match the frozen protocol.")

    return TrainingFeatureSource(
        metadata=selected.loc[:, IDENTIFIER_COLUMNS].copy(),
        train_sales=selected.loc[:, list(train_days)].to_numpy(dtype=np.int16),
        train_calendar=train_calendar,
        validation_calendar=validation_calendar,
        train_day_keys=train_days,
    )
