"""P25 rolling-origin XGBoost V3 research with strict pre-TEST isolation.

This module never imports the final-TEST loader and rejects a validation fold
ending after d_1913.  For every fold/model, recursive forecasts are complete
before that fold's actual sales are opened for scoring.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ml.data.m5_ca1_foods import load_rolling_fold_actuals, load_rolling_fold_feature_source
from ml.evaluation.forecast_analysis import horizon_metrics
from ml.evaluation.metrics import aggregate_metrics, per_series_metrics
from ml.features.builder import (
    build_daily_price_matrix,
    build_encodings,
    build_training_features,
    encode_calendar_features,
    load_feature_config,
    load_train_price_rows,
)
from ml.models.recursive import recursive_forecast
from ml.models.xgboost_model import build_categorical_schema, fit_global_model, load_model_config, predict_checked


@dataclass
class FoldContext:
    definition: dict
    source: object
    prices: np.ndarray
    encodings: object
    schema_levels: dict[str, list[int]]
    frames: dict[str, object]


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_revision() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def candidate_config(candidate: dict, seed: int, feature_set: str) -> dict:
    required = {
        "name", "objective", "n_estimators", "learning_rate", "max_depth", "min_child_weight",
        "subsample", "colsample_bytree", "reg_alpha", "reg_lambda",
    }
    if required.difference(candidate) or candidate["objective"] not in {"count:poisson", "reg:squarederror"}:
        raise ValueError("invalid V3 candidate definition")
    return {
        "model_name": candidate["name"], "feature_set": feature_set, "tree_method": "hist",
        "random_state": seed, "n_jobs": -1,
        **{key: candidate[key] for key in required if key != "name"},
    }


def validate_research_config(research: dict) -> None:
    folds = research.get("folds", [])
    expected = [
        ("d_1801", "d_1802", "d_1829"), ("d_1829", "d_1830", "d_1857"),
        ("d_1857", "d_1858", "d_1885"), ("d_1885", "d_1886", "d_1913"),
    ]
    observed = [(fold.get("train_end_d"), fold.get("validation_start_d"), fold.get("validation_end_d")) for fold in folds]
    if research.get("horizon_days") != 28 or observed != expected:
        raise ValueError("V3 requires the four predeclared 28-day rolling folds through d_1913.")
    if "TEST" not in str(research.get("test_policy", "")).upper() or any(int(fold[2][2:]) > 1913 for fold in observed):
        raise ValueError("V3 rolling research must not access TEST actuals.")
    if research["selection_rule"].get("minimum_wape_fold_improvements") != 3:
        raise ValueError("V3 selection requires WAPE improvement on at least three folds.")


def _schema_levels(encodings, train_calendar: pd.DataFrame, validation_calendar: pd.DataFrame) -> dict[str, list[int]]:
    encoded = encode_calendar_features(pd.concat([train_calendar, validation_calendar], ignore_index=True), encodings)
    levels = {column: sorted(encoded[column].astype(int).unique().tolist()) for column in encoded.columns}
    levels["item_code"] = sorted(encodings.item_codes.values())
    levels["dept_code"] = sorted(encodings.dept_codes.values())
    return levels


def _fold_context(raw_dir: Path, protocol: Path, definition: dict) -> FoldContext:
    source = load_rolling_fold_feature_source(
        raw_dir, protocol, definition["train_end_d"], definition["validation_start_d"], definition["validation_end_d"]
    )
    item_ids = tuple(source.metadata["item_id"].astype(str))
    encodings = build_encodings(source.metadata, pd.concat([source.train_calendar, source.validation_calendar], ignore_index=True))
    prices = build_daily_price_matrix(
        load_train_price_rows(raw_dir, item_ids, source.train_calendar), item_ids, source.train_calendar
    )
    return FoldContext(definition, source, prices, encodings, _schema_levels(encodings, source.train_calendar, source.validation_calendar), {})


def _build_frame(context: FoldContext, config: dict):
    key = config["feature_set"]
    if key not in context.frames:
        context.frames[key] = build_training_features(
            context.source.metadata, context.source.train_sales, context.source.train_calendar,
            pd.concat([context.source.train_calendar, context.source.validation_calendar], ignore_index=True),
            context.prices, config,
        )
    return context.frames[key]


def _forecast(model, schema, context: FoldContext, config: dict, names: tuple[str, ...]) -> np.ndarray:
    return recursive_forecast(
        lambda frame: predict_checked(model, frame, schema), context.source.train_sales, context.prices,
        context.source.validation_calendar, context.source.metadata, context.encodings, config, names,
    )


def _run_model(
    *, context: FoldContext, config: dict, feature_config: dict, label: str, stage: str,
    raw_dir: Path, protocol: Path, models_dir: Path,
) -> tuple[dict, pd.DataFrame | None, pd.DataFrame | None, np.ndarray | None, np.ndarray | None]:
    """Fit/predict one fold before opening the fold's validation actuals."""
    build = _build_frame(context, feature_config)
    names = build.feature_names
    started = time.perf_counter()
    model, schema = fit_global_model(build.frame.loc[:, names], build.frame["sales_target"], config, context.schema_levels)
    fit_seconds = time.perf_counter() - started
    model_path = models_dir / f"xgboost_v3_{label.lower()}_{context.definition['name']}.json"
    models_dir.mkdir(parents=True, exist_ok=True)
    model.save_model(model_path)
    predict_started = time.perf_counter()
    try:
        forecast = _forecast(model, schema, context, feature_config, names)
    except ValueError as exc:
        if "negative" not in str(exc).lower():
            raise
        return ({
            "candidate": label, "stage": stage, "fold": context.definition["name"], **context.definition,
            "feature_set": feature_config["feature_set"], "feature_count": len(names),
            "training_seconds": fit_seconds, "prediction_seconds": time.perf_counter() - predict_started,
            "model_size_MiB": model_path.stat().st_size / 1024**2, "model_sha256": _digest(model_path),
            "raw_min_prediction": np.nan, "disqualification_reason": str(exc),
        }, None, None, None, None)
    prediction_seconds = time.perf_counter() - predict_started
    if forecast.shape != (len(context.source.metadata), 28) or float(forecast.min()) < 0:
        raise ValueError("Recursive forecast dimensions or nonnegative-demand contract failed.")

    # Actuals are deliberately opened only after every recursive step above.
    item_ids, actual, dates = load_rolling_fold_actuals(
        raw_dir, protocol, context.definition["validation_start_d"], context.definition["validation_end_d"]
    )
    expected_ids = tuple(context.source.metadata["item_id"].astype(str))
    if item_ids != expected_ids:
        raise ValueError("Rolling fold item ordering changed between prediction and scoring.")
    metrics = aggregate_metrics(actual, forecast)
    record = {
        "candidate": label, "stage": stage, "fold": context.definition["name"], **context.definition,
        "feature_set": feature_config["feature_set"], "feature_count": len(names),
        "training_seconds": fit_seconds, "prediction_seconds": prediction_seconds,
        "model_size_MiB": model_path.stat().st_size / 1024**2, "model_sha256": _digest(model_path),
        "raw_min_prediction": float(forecast.min()), "disqualification_reason": None, **metrics,
    }
    per_series = per_series_metrics(actual, forecast, item_ids).assign(
        candidate=label, stage=stage, fold=context.definition["name"],
        dept_id=context.source.metadata["dept_id"].astype(str).to_numpy(),
        zero_demand_rate=(actual == 0).mean(axis=1),
    )
    horizon = horizon_metrics(actual, forecast, dates).assign(candidate=label, stage=stage, fold=context.definition["name"])
    return record, per_series, horizon, actual, forecast


def _diagnose_per_series(records: list[pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    all_rows = pd.concat(records, ignore_index=True)
    sparse = all_rows.copy()
    sparse["sparsity_band"] = pd.cut(
        sparse["zero_demand_rate"], [-0.001, .25, .50, .75, 1.0],
        labels=["0-25% zero", "25-50% zero", "50-75% zero", "75-100% zero"], include_lowest=True,
    )
    by_sparsity = sparse.groupby(["candidate", "stage", "sparsity_band"], observed=True).agg(
        series_fold_observations=("MAE", "size"), MAE=("MAE", "mean"), RMSE=("RMSE", "mean"), WAPE_percent=("WAPE_percent", "mean")
    ).reset_index()
    volume = all_rows.copy()
    volume["volume_quartile"] = volume.groupby(["candidate", "stage", "fold"], group_keys=False)["validation_actual_sum"].apply(
        lambda values: pd.qcut(values.rank(method="first"), 4, labels=["Q1 low", "Q2", "Q3", "Q4 high"])
    )
    by_volume = volume.groupby(["candidate", "stage", "volume_quartile"], observed=True).agg(
        series_fold_observations=("MAE", "size"), MAE=("MAE", "mean"), RMSE=("RMSE", "mean"), WAPE_percent=("WAPE_percent", "mean")
    ).reset_index()
    by_department = all_rows.groupby(["candidate", "stage", "dept_id"], observed=True).agg(
        series_fold_observations=("MAE", "size"), MAE=("MAE", "mean"), RMSE=("RMSE", "mean"), WAPE_percent=("WAPE_percent", "mean")
    ).reset_index()
    return by_sparsity, by_volume, by_department


def _candidate_summary(metrics: pd.DataFrame, baseline_name: str) -> pd.DataFrame:
    scored = metrics.loc[metrics["stage"].isin(["baseline", "stage_2"]) & metrics["MAE"].notna()].copy()
    grouped = scored.groupby(["candidate", "feature_set"], observed=True)
    summary = grouped.agg(
        folds=("fold", "nunique"), mean_MAE=("MAE", "mean"), median_MAE=("MAE", "median"), std_MAE=("MAE", "std"), worst_MAE=("MAE", "max"),
        mean_RMSE=("RMSE", "mean"), median_RMSE=("RMSE", "median"), std_RMSE=("RMSE", "std"), worst_RMSE=("RMSE", "max"),
        mean_WAPE_percent=("WAPE_percent", "mean"), median_WAPE_percent=("WAPE_percent", "median"), std_WAPE_percent=("WAPE_percent", "std"), worst_WAPE_percent=("WAPE_percent", "max"),
        total_training_seconds=("training_seconds", "sum"), mean_prediction_seconds=("prediction_seconds", "mean"), mean_model_size_MiB=("model_size_MiB", "mean"),
    ).reset_index()
    baseline_folds = scored.loc[scored["candidate"].eq(baseline_name), ["fold", "WAPE_percent"]].set_index("fold")["WAPE_percent"]
    for index, row in summary.iterrows():
        candidate_folds = scored.loc[scored["candidate"].eq(row["candidate"]), ["fold", "WAPE_percent"]].set_index("fold")["WAPE_percent"]
        summary.loc[index, "wape_folds_improved_vs_v1"] = int((candidate_folds < baseline_folds).sum()) if row["candidate"] != baseline_name else 0
    return summary


def select_candidate(summary: pd.DataFrame, selection_rule: dict, baseline_name: str) -> tuple[str | None, pd.DataFrame]:
    baseline = summary.loc[summary["candidate"].eq(baseline_name)].iloc[0]
    result = summary.copy()
    contender = result.loc[~result["candidate"].eq(baseline_name)].copy()
    contender["credible_by_predeclared_rule"] = (
        (contender["folds"] == 4)
        & (contender["mean_WAPE_percent"] < baseline["mean_WAPE_percent"])
        & (contender["mean_MAE"] <= baseline["mean_MAE"])
        & (contender["mean_RMSE"] <= baseline["mean_RMSE"])
        & (contender["wape_folds_improved_vs_v1"] >= selection_rule["minimum_wape_fold_improvements"])
    )
    result = result.merge(contender[["candidate", "credible_by_predeclared_rule"]], on="candidate", how="left")
    result["credible_by_predeclared_rule"] = result["credible_by_predeclared_rule"].fillna(False)
    eligible = result.loc[result["credible_by_predeclared_rule"]]
    if eligible.empty:
        return None, result
    return str(eligible.sort_values(["mean_WAPE_percent", "mean_MAE", "mean_RMSE"], kind="stable").iloc[0]["candidate"]), result


def _plot_horizon(horizon: pd.DataFrame, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 4.4))
    for candidate, rows in horizon.groupby("candidate", observed=True):
        daily = rows.groupby("horizon", observed=True)["MAE"].mean()
        axis.plot(daily.index, daily.values, label=candidate, linewidth=2)
    axis.set(xlabel="Recursive forecast horizon (days)", ylabel="Mean MAE across folds")
    axis.grid(axis="y", alpha=.25); axis.legend(frameon=False); figure.tight_layout(); figure.savefig(path, dpi=160); plt.close(figure)


def _plot_summary(summary: pd.DataFrame, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(7, 4.2))
    axis.bar(summary["candidate"], summary["mean_WAPE_percent"], color=["#2563eb" if name.startswith("XGBOOST_V1") else "#6366f1" for name in summary["candidate"]])
    axis.set(ylabel="Mean rolling WAPE (%)"); axis.tick_params(axis="x", rotation=20); axis.grid(axis="y", alpha=.25); figure.tight_layout(); figure.savefig(path, dpi=160); plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data/raw/m5")
    parser.add_argument("--protocol", type=Path, default=ROOT / "configs/data/m5_ca1_foods.yaml")
    parser.add_argument("--research-config", type=Path, default=ROOT / "configs/experiments/xgboost_v3_research.yaml")
    parser.add_argument("--feature-config", type=Path, default=ROOT / "configs/features/ml_features_v3.yaml")
    parser.add_argument("--v1-feature-config", type=Path, default=ROOT / "configs/features/ml_features_v1.yaml")
    parser.add_argument("--v1-model-config", type=Path, default=ROOT / "configs/models/xgboost_v1.yaml")
    parser.add_argument("--tables-dir", type=Path, default=ROOT / "reports/tables")
    parser.add_argument("--figures-dir", type=Path, default=ROOT / "reports/figures")
    parser.add_argument("--manifests-dir", type=Path, default=ROOT / "data/manifests")
    parser.add_argument("--models-dir", type=Path, default=ROOT / "artifacts/models")
    args = parser.parse_args()

    research = yaml.safe_load(args.research_config.read_text(encoding="utf-8")); validate_research_config(research)
    v3_features, v1_features, v1_model_config = load_feature_config(args.feature_config), load_feature_config(args.v1_feature_config), load_model_config(args.v1_model_config)
    contexts = {fold["name"]: _fold_context(args.raw_dir, args.protocol, fold) for fold in research["folds"]}
    rows: list[dict] = []; per_series: list[pd.DataFrame] = []; horizons: list[pd.DataFrame] = []
    baseline_name = research["v1_baseline"]["model_name"]

    for fold in research["folds"]:
        record, detail, horizon, _, _ = _run_model(
            context=contexts[fold["name"]], config=v1_model_config, feature_config=v1_features, label=baseline_name,
            stage="baseline", raw_dir=args.raw_dir, protocol=args.protocol, models_dir=args.models_dir,
        )
        rows.append(record); per_series.append(detail); horizons.append(horizon)

    stage1_runs: dict[tuple[str, str], tuple[dict, pd.DataFrame | None, pd.DataFrame | None]] = {}
    for candidate in research["stage_1"]["candidates"]:
        config = candidate_config(candidate, int(research["random_state"]), v3_features["feature_set"])
        for fold_name in research["stage_1"]["folds"]:
            record, detail, horizon, _, _ = _run_model(
                context=contexts[fold_name], config=config, feature_config=v3_features, label=candidate["name"],
                stage="stage_1", raw_dir=args.raw_dir, protocol=args.protocol, models_dir=args.models_dir,
            )
            rows.append(record); stage1_runs[(candidate["name"], fold_name)] = (record, detail, horizon)
    stage1 = pd.DataFrame(rows).query("stage == 'stage_1' and MAE == MAE").groupby("candidate", observed=True)["WAPE_percent"].mean().sort_values()
    finalists = [name for name in stage1.index if all(stage1_runs[(name, fold)][0]["disqualification_reason"] is None for fold in research["stage_1"]["folds"])][: research["stage_1"]["retain_top_candidates"]]
    if not finalists:
        raise ValueError("No V3 candidate survived stage 1 without negative recursive demand.")

    by_name = {candidate["name"]: candidate for candidate in research["stage_1"]["candidates"]}
    for name in finalists:
        config = candidate_config(by_name[name], int(research["random_state"]), v3_features["feature_set"])
        for fold in research["folds"]:
            record, detail, horizon = stage1_runs.get((name, fold["name"]), (None, None, None))
            if record is None:
                record, detail, horizon, _, _ = _run_model(
                    context=contexts[fold["name"]], config=config, feature_config=v3_features, label=name,
                    stage="stage_2", raw_dir=args.raw_dir, protocol=args.protocol, models_dir=args.models_dir,
                )
                rows.append(record)
            else:
                record = {**record, "stage": "stage_2"}; rows.append(record)
                if detail is not None: detail = detail.assign(stage="stage_2")
                if horizon is not None: horizon = horizon.assign(stage="stage_2")
            if detail is not None: per_series.append(detail)
            if horizon is not None: horizons.append(horizon)

    metrics = pd.DataFrame(rows)
    summary = _candidate_summary(metrics, baseline_name)
    winner, summary = select_candidate(summary, research["selection_rule"], baseline_name)
    horizon_table = pd.concat(horizons, ignore_index=True)
    sparsity, volume, department = _diagnose_per_series(per_series)
    args.tables_dir.mkdir(parents=True, exist_ok=True); args.figures_dir.mkdir(parents=True, exist_ok=True); args.manifests_dir.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(args.tables_dir / "xgboost_v3_rolling_metrics.csv", index=False)
    summary.to_csv(args.tables_dir / "xgboost_v3_candidate_summary.csv", index=False)
    sparsity.to_csv(args.tables_dir / "xgboost_v3_error_by_sparsity.csv", index=False)
    volume.to_csv(args.tables_dir / "xgboost_v3_error_by_volume.csv", index=False)
    department.to_csv(args.tables_dir / "xgboost_v3_error_by_department.csv", index=False)
    horizon_table.to_csv(args.tables_dir / "xgboost_v3_horizon_metrics.csv", index=False)
    _plot_horizon(horizon_table.loc[horizon_table["stage"].isin(["baseline", "stage_2"])], args.figures_dir / "xgboost_v3_horizon_mae.png")
    _plot_summary(summary, args.figures_dir / "xgboost_v3_mean_rolling_wape.png")
    manifest = {
        "experiment_id": research["experiment_id"], "git_commit": _git_revision(), "selection_status": "CREDIBLE_IMPROVEMENT" if winner else "NO_CANDIDATE_SELECTED",
        "winner": winner, "scope": research["scope"], "folds": research["folds"], "feature_set": {"name": v3_features["feature_set"], "feature_count": len(_build_frame(contexts["fold_4"], v3_features).feature_names), "definition": v3_features["intermittent_features"]},
        "selection_rule": research["selection_rule"], "stage_1_finalists": finalists, "test_actuals_accessed": False,
        "test_policy": research["test_policy"], "production_change": "NONE; XGBOOST_V1 remains selected/default.",
        "metrics": metrics.to_dict(orient="records"), "candidate_summary": summary.to_dict(orient="records"),
    }
    (args.manifests_dir / "xgboost_v3_research.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"winner": winner, "finalists": finalists, "summary": summary.to_dict(orient="records"), "test_actuals_accessed": False}, indent=2, default=str))


if __name__ == "__main__":
    main()
