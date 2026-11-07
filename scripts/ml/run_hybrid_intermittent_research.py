"""P25-02 regime-aware hybrid forecasting research with strict pre-TEST isolation.

The script never imports the final-TEST loader.  For each evaluated fold it
fits immutable V1 parameters, creates V1 and candidate hybrid predictions from
pre-origin history, and only then opens that fold's validation actuals.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ml.data.m5_ca1_foods import load_rolling_fold_actuals
from ml.evaluation.forecast_analysis import horizon_metrics
from ml.evaluation.metrics import aggregate_metrics, per_series_metrics
from ml.features.builder import load_feature_config
from ml.models.intermittent import classify_intermittent, intermittent_forecast
from ml.models.xgboost_model import fit_global_model, load_model_config, predict_checked
from scripts.ml.run_xgboost_v3_research import _build_frame, _fold_context, _forecast, summarize_horizon_groups


def _git_revision() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_research_config(research: dict) -> None:
    expected = [
        ("d_1801", "d_1802", "d_1829"), ("d_1829", "d_1830", "d_1857"),
        ("d_1857", "d_1858", "d_1885"), ("d_1885", "d_1886", "d_1913"),
    ]
    observed = [(fold.get("train_end_d"), fold.get("validation_start_d"), fold.get("validation_end_d")) for fold in research.get("folds", [])]
    if observed != expected or research.get("horizon_days") != 28:
        raise ValueError("Hybrid research requires the four predeclared 28-day folds through d_1913.")
    if "TEST" not in str(research.get("test_policy", "")).upper():
        raise ValueError("Hybrid research must explicitly prohibit final-TEST access.")
    thresholds = research["regime"]["threshold_candidates"]
    if thresholds != [0.65, 0.75] or research["regime"]["history_window_days"] != 56:
        raise ValueError("Hybrid routing threshold family must remain preregistered at 0.65/0.75 over 56 days.")
    if research["selection_rule"].get("minimum_wape_fold_improvements") != 3:
        raise ValueError("Hybrid selection requires WAPE improvement in at least three folds.")


def _validate_candidate(candidate: dict) -> None:
    required = {"name", "method", "zero_rate_threshold"}
    if required.difference(candidate) or candidate["method"] not in {"CROSTON_CLASSIC", "SBA", "TSB"}:
        raise ValueError("Invalid hybrid candidate definition.")
    if candidate["zero_rate_threshold"] not in {0.65, 0.75}:
        raise ValueError("Hybrid candidates may use only preregistered routing thresholds.")
    if candidate["method"] in {"CROSTON_CLASSIC", "SBA"} and candidate.get("alpha") not in {0.05, 0.10, 0.20}:
        raise ValueError("Croston/SBA candidates require a preregistered alpha.")
    if candidate["method"] == "TSB" and (candidate.get("alpha_probability") not in {0.05, 0.10, 0.20} or candidate.get("alpha_size") not in {0.10}):
        raise ValueError("TSB candidates require preregistered probability/size smoothing.")


def _method_parameters(candidate: dict) -> dict[str, float]:
    if candidate["method"] == "TSB":
        return {"alpha_probability": candidate["alpha_probability"], "alpha_size": candidate["alpha_size"]}
    return {"alpha": candidate["alpha"]}


def hybrid_forecast(v1_forecast: np.ndarray, history: np.ndarray, candidate: dict, horizon_days: int) -> tuple[np.ndarray, np.ndarray]:
    """Route only pre-origin intermittent series to a transparent method."""
    _validate_candidate(candidate)
    v1 = np.asarray(v1_forecast, dtype=float)
    mask = classify_intermittent(history, candidate["zero_rate_threshold"], window=56)
    intermittent = intermittent_forecast(history, candidate["method"], horizon_days, **_method_parameters(candidate))
    if v1.shape != intermittent.shape or v1.shape[1] != horizon_days:
        raise ValueError("V1 and intermittent forecasts must have matching (series, horizon) shapes.")
    hybrid = v1.copy()
    hybrid[mask] = intermittent[mask]
    if not np.isfinite(hybrid).all() or (hybrid < 0).any():
        raise ValueError("Hybrid forecast must be finite and nonnegative.")
    return hybrid, mask


def _fit_v1_forecast(context, v1_features: dict, v1_config: dict, models_dir: Path) -> tuple[np.ndarray, dict]:
    """Fit unchanged V1 parameters and forecast before any fold actuals are opened."""
    build = _build_frame(context, v1_features)
    names = build.feature_names
    started = time.perf_counter()
    model, schema = fit_global_model(build.frame.loc[:, names], build.frame["sales_target"], v1_config, context.schema_levels)
    training_seconds = time.perf_counter() - started
    models_dir.mkdir(parents=True, exist_ok=True)
    model_path = models_dir / f"hybrid_xgboost_v1_{context.definition['name']}.json"
    model.save_model(model_path)
    started = time.perf_counter()
    forecast = _forecast(model, schema, context, v1_features, names)
    prediction_seconds = time.perf_counter() - started
    if forecast.shape != (len(context.source.metadata), 28) or not np.isfinite(forecast).all() or (forecast < 0).any():
        raise ValueError("V1 recursive forecast failed nonnegative shape contract.")
    return forecast, {
        "feature_set": v1_features["feature_set"], "feature_count": len(names), "training_seconds": training_seconds,
        "prediction_seconds": prediction_seconds, "model_size_MiB": model_path.stat().st_size / 1024**2,
        "model_sha256": _digest(model_path), "raw_min_prediction": float(forecast.min()),
    }


def _score(context, actual: np.ndarray, dates: tuple[str, ...], forecast: np.ndarray, candidate: str, stage: str, detail: dict) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    item_ids = tuple(context.source.metadata["item_id"].astype(str))
    record = {"candidate": candidate, "stage": stage, "fold": context.definition["name"], **context.definition, **detail, **aggregate_metrics(actual, forecast)}
    history_zero_rate = (context.source.train_sales[:, -56:] == 0).mean(axis=1)
    per_series = per_series_metrics(actual, forecast, item_ids).assign(
        candidate=candidate, stage=stage, fold=context.definition["name"],
        dept_id=context.source.metadata["dept_id"].astype(str).to_numpy(), zero_rate_56_history=history_zero_rate,
    )
    horizon = horizon_metrics(actual, forecast, dates).assign(
        candidate=candidate, stage=stage, fold=context.definition["name"], series_count=actual.shape[0]
    )
    return record, per_series, horizon


def _routing_row(context, candidate: dict, mask: np.ndarray, stage: str) -> dict:
    return {
        "candidate": candidate["name"], "stage": stage, "fold": context.definition["name"],
        "method": candidate["method"], "zero_rate_threshold": candidate["zero_rate_threshold"],
        "intermittent_series": int(mask.sum()), "regular_series": int((~mask).sum()),
        "intermittent_percent": float(mask.mean() * 100), "history_window_days": 56,
        **_method_parameters(candidate),
    }


def _diagnostics(records: list[pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    all_rows = pd.concat(records, ignore_index=True)
    sparse = all_rows.copy()
    sparse["sparsity_band"] = pd.cut(
        sparse["zero_rate_56_history"], [-0.001, .25, .50, .75, 1.0],
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


def _summary(metrics: pd.DataFrame, baseline_name: str) -> pd.DataFrame:
    scored = metrics.loc[metrics["stage"].isin(["baseline", "stage_2"])].copy()
    summary = scored.groupby(["candidate", "feature_set"], observed=True).agg(
        folds=("fold", "nunique"), mean_MAE=("MAE", "mean"), median_MAE=("MAE", "median"), std_MAE=("MAE", "std"), worst_MAE=("MAE", "max"),
        mean_RMSE=("RMSE", "mean"), median_RMSE=("RMSE", "median"), std_RMSE=("RMSE", "std"), worst_RMSE=("RMSE", "max"),
        mean_WAPE_percent=("WAPE_percent", "mean"), median_WAPE_percent=("WAPE_percent", "median"), std_WAPE_percent=("WAPE_percent", "std"), worst_WAPE_percent=("WAPE_percent", "max"),
        total_training_seconds=("training_seconds", "sum"), mean_prediction_seconds=("prediction_seconds", "mean"), mean_model_size_MiB=("model_size_MiB", "mean"),
    ).reset_index()
    baseline_folds = scored.loc[scored["candidate"].eq(baseline_name), ["fold", "WAPE_percent"]].set_index("fold")["WAPE_percent"]
    for index, row in summary.iterrows():
        values = scored.loc[scored["candidate"].eq(row["candidate"]), ["fold", "WAPE_percent"]].set_index("fold")["WAPE_percent"]
        aligned = values.reindex(baseline_folds.index)
        if aligned.isna().any() or len(aligned) != len(baseline_folds):
            raise ValueError("Every full-stage candidate must have one WAPE value for each V1 fold.")
        summary.loc[index, "wape_folds_improved_vs_v1"] = 0 if row["candidate"] == baseline_name else int((aligned < baseline_folds).sum())
    return summary


def select_candidate(summary: pd.DataFrame, sparse: pd.DataFrame, volume: pd.DataFrame, rule: dict, baseline_name: str) -> tuple[str | None, pd.DataFrame]:
    baseline = summary.loc[summary["candidate"].eq(baseline_name)].iloc[0]
    baseline_sparse = float(sparse.loc[sparse["candidate"].eq(baseline_name) & sparse["sparsity_band"].eq(rule["sparse_band"]), "MAE"].iloc[0])
    baseline_dense = float(sparse.loc[sparse["candidate"].eq(baseline_name) & sparse["sparsity_band"].eq(rule["dense_band"]), "MAE"].iloc[0])
    baseline_high = float(volume.loc[volume["candidate"].eq(baseline_name) & volume["volume_quartile"].eq(rule["high_volume_band"]), "MAE"].iloc[0])
    result = summary.copy()
    allowance = 1 + float(rule["dense_high_volume_max_mae_regression_percent"]) / 100
    for index, row in result.iterrows():
        if row["candidate"] == baseline_name:
            result.loc[index, "credible_by_predeclared_rule"] = False
            continue
        candidate_sparse = float(sparse.loc[sparse["candidate"].eq(row["candidate"]) & sparse["sparsity_band"].eq(rule["sparse_band"]), "MAE"].iloc[0])
        candidate_dense = float(sparse.loc[sparse["candidate"].eq(row["candidate"]) & sparse["sparsity_band"].eq(rule["dense_band"]), "MAE"].iloc[0])
        candidate_high = float(volume.loc[volume["candidate"].eq(row["candidate"]) & volume["volume_quartile"].eq(rule["high_volume_band"]), "MAE"].iloc[0])
        result.loc[index, "sparse_mae_vs_v1"] = candidate_sparse - baseline_sparse
        result.loc[index, "dense_mae_vs_v1"] = candidate_dense - baseline_dense
        result.loc[index, "high_volume_mae_vs_v1"] = candidate_high - baseline_high
        result.loc[index, "credible_by_predeclared_rule"] = bool(
            row["folds"] == 4 and row["mean_WAPE_percent"] < baseline["mean_WAPE_percent"]
            and row["mean_MAE"] <= baseline["mean_MAE"] and row["mean_RMSE"] <= baseline["mean_RMSE"]
            and row["wape_folds_improved_vs_v1"] >= rule["minimum_wape_fold_improvements"]
            and candidate_sparse < baseline_sparse and candidate_dense <= baseline_dense * allowance and candidate_high <= baseline_high * allowance
        )
    eligible = result.loc[result["credible_by_predeclared_rule"].fillna(False)]
    return (None if eligible.empty else str(eligible.sort_values(["mean_WAPE_percent", "mean_MAE"], kind="stable").iloc[0]["candidate"])), result


def _plot_summary(summary: pd.DataFrame, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(7, 4.2))
    axis.bar(summary["candidate"], summary["mean_WAPE_percent"], color=["#2563eb" if value.startswith("XGBOOST_V1") else "#6366f1" for value in summary["candidate"]])
    axis.set(ylabel="Mean rolling WAPE (%)"); axis.tick_params(axis="x", rotation=20); axis.grid(axis="y", alpha=.25); figure.tight_layout(); figure.savefig(path, dpi=160); plt.close(figure)


def _plot_horizon(horizon: pd.DataFrame, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 4.4))
    for candidate, rows in horizon.groupby("candidate", observed=True):
        mean_daily = rows.groupby("horizon", observed=True)["MAE"].mean()
        axis.plot(mean_daily.index, mean_daily.values, label=candidate, linewidth=2)
    axis.set(xlabel="Recursive forecast horizon (days)", ylabel="Mean MAE across folds")
    axis.grid(axis="y", alpha=.25); axis.legend(frameon=False); figure.tight_layout(); figure.savefig(path, dpi=160); plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data/raw/m5")
    parser.add_argument("--protocol", type=Path, default=ROOT / "configs/data/m5_ca1_foods.yaml")
    parser.add_argument("--research-config", type=Path, default=ROOT / "configs/experiments/hybrid_intermittent_research.yaml")
    parser.add_argument("--tables-dir", type=Path, default=ROOT / "reports/tables")
    parser.add_argument("--figures-dir", type=Path, default=ROOT / "reports/figures")
    parser.add_argument("--manifests-dir", type=Path, default=ROOT / "data/manifests")
    parser.add_argument("--models-dir", type=Path, default=ROOT / "artifacts/models")
    args = parser.parse_args()

    research = yaml.safe_load(args.research_config.read_text(encoding="utf-8")); validate_research_config(research)
    candidates = research["stage_1"]["candidates"]
    for candidate in candidates: _validate_candidate(candidate)
    v1_features = load_feature_config(ROOT / research["v1_control"]["feature_config"])
    v1_config = load_model_config(ROOT / research["v1_control"]["model_config"])
    baseline_name = research["v1_control"]["model_name"]
    folds = {fold["name"]: fold for fold in research["folds"]}
    contexts = {name: _fold_context(args.raw_dir, args.protocol, fold) for name, fold in folds.items()}
    rows: list[dict] = []; diagnostics: list[pd.DataFrame] = []; horizons: list[pd.DataFrame] = []; routing: list[dict] = []
    stage1_cache: dict[tuple[str, str], tuple[dict, pd.DataFrame, pd.DataFrame, dict]] = {}
    baseline_cache: dict[str, tuple[np.ndarray, dict, np.ndarray, tuple[str, ...]]] = {}

    # Screen only folds 2 and 4. Hybrid predictions are generated before their actuals are opened.
    for fold_name in research["stage_1"]["folds"]:
        context = contexts[fold_name]
        v1_forecast, v1_detail = _fit_v1_forecast(context, v1_features, v1_config, args.models_dir)
        hybrid_predictions = {candidate["name"]: hybrid_forecast(v1_forecast, context.source.train_sales, candidate, 28) for candidate in candidates}
        item_ids, actual, dates = load_rolling_fold_actuals(args.raw_dir, args.protocol, context.definition["validation_start_d"], context.definition["validation_end_d"])
        if item_ids != tuple(context.source.metadata["item_id"].astype(str)):
            raise ValueError("Fold item ordering changed between prediction and scoring.")
        baseline_record, baseline_detail, baseline_horizon = _score(context, actual, dates, v1_forecast, baseline_name, "baseline", v1_detail)
        rows.append(baseline_record); diagnostics.append(baseline_detail); horizons.append(baseline_horizon)
        baseline_cache[fold_name] = (v1_forecast, v1_detail, actual, dates)
        for candidate in candidates:
            forecast, mask = hybrid_predictions[candidate["name"]]
            record, detail, horizon = _score(context, actual, dates, forecast, candidate["name"], "stage_1", {**v1_detail, "feature_set": "HYBRID_V1_INTERMITTENT"})
            route = _routing_row(context, candidate, mask, "stage_1")
            rows.append(record); routing.append(route); stage1_cache[(candidate["name"], fold_name)] = (record, detail, horizon, route)

    stage1 = pd.DataFrame(rows).query("stage == 'stage_1'").groupby("candidate", observed=True)["WAPE_percent"].mean().sort_values()
    finalists = list(stage1.index[: research["stage_1"]["retain_top_candidates"]])
    by_name = {candidate["name"]: candidate for candidate in candidates}

    # Complete all four folds only for finalists. For a new fold, build every
    # finalist's hybrid prediction before opening its actuals; this also trains
    # the immutable V1 control exactly once per origin.
    for fold_name, context in contexts.items():
        if fold_name in research["stage_1"]["folds"]:
            for name in finalists:
                record, detail, horizon, routing_row = stage1_cache[(name, fold_name)]
                rows.append({**record, "stage": "stage_2"})
                diagnostics.append(detail.assign(stage="stage_2")); horizons.append(horizon.assign(stage="stage_2"))
                routing.append({**routing_row, "stage": "stage_2"})
            continue
        v1_forecast, v1_detail = _fit_v1_forecast(context, v1_features, v1_config, args.models_dir)
        finalist_predictions = {name: hybrid_forecast(v1_forecast, context.source.train_sales, by_name[name], 28) for name in finalists}
        item_ids, actual, dates = load_rolling_fold_actuals(args.raw_dir, args.protocol, context.definition["validation_start_d"], context.definition["validation_end_d"])
        if item_ids != tuple(context.source.metadata["item_id"].astype(str)):
            raise ValueError("Fold item ordering changed between prediction and scoring.")
        baseline_record, baseline_detail, baseline_horizon = _score(context, actual, dates, v1_forecast, baseline_name, "baseline", v1_detail)
        rows.append(baseline_record); diagnostics.append(baseline_detail); horizons.append(baseline_horizon)
        for name, (hybrid, mask) in finalist_predictions.items():
            record, detail, horizon = _score(context, actual, dates, hybrid, name, "stage_2", {**v1_detail, "feature_set": "HYBRID_V1_INTERMITTENT"})
            rows.append(record); diagnostics.append(detail); horizons.append(horizon)
            routing.append(_routing_row(context, by_name[name], mask, "stage_2"))

    metrics = pd.DataFrame(rows)
    horizon_table = summarize_horizon_groups(pd.concat(horizons, ignore_index=True))
    diagnostic_rows = [row for row in diagnostics if row["stage"].iloc[0] in {"baseline", "stage_2"}]
    sparsity, volume, department = _diagnostics(diagnostic_rows)
    summary = _summary(metrics, baseline_name)
    winner, summary = select_candidate(summary, sparsity, volume, research["selection_rule"], baseline_name)
    routing_table = pd.DataFrame(routing)

    args.tables_dir.mkdir(parents=True, exist_ok=True); args.figures_dir.mkdir(parents=True, exist_ok=True); args.manifests_dir.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(args.tables_dir / "hybrid_rolling_metrics.csv", index=False)
    summary.to_csv(args.tables_dir / "hybrid_candidate_summary.csv", index=False)
    sparsity.to_csv(args.tables_dir / "hybrid_error_by_sparsity.csv", index=False)
    volume.to_csv(args.tables_dir / "hybrid_error_by_volume.csv", index=False)
    department.to_csv(args.tables_dir / "hybrid_error_by_department.csv", index=False)
    horizon_table.to_csv(args.tables_dir / "hybrid_horizon_metrics.csv", index=False)
    routing_table.to_csv(args.tables_dir / "hybrid_routing_summary.csv", index=False)
    _plot_horizon(horizon_table.loc[(horizon_table["stage"].isin(["baseline", "stage_2"])) & horizon_table["granularity"].eq("day")], args.figures_dir / "hybrid_horizon_mae.png")
    _plot_summary(summary, args.figures_dir / "hybrid_mean_rolling_wape.png")
    manifest = {
        "experiment_id": research["experiment_id"], "git_commit": _git_revision(), "selection_status": "CREDIBLE_IMPROVEMENT" if winner else "NO_CANDIDATE_SELECTED",
        "winner": winner, "scope": research["scope"], "folds": research["folds"], "regime": research["regime"],
        "stage_1_finalists": finalists, "selection_rule": research["selection_rule"], "test_actuals_accessed": False,
        "test_policy": research["test_policy"], "production_change": "NONE; XGBOOST_V1 remains selected/default.",
        "metrics": metrics.to_dict(orient="records"), "candidate_summary": summary.to_dict(orient="records"),
        "routing": routing_table.to_dict(orient="records"),
    }
    (args.manifests_dir / "hybrid_intermittent_research.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"winner": winner, "finalists": finalists, "summary": summary.to_dict(orient="records"), "test_actuals_accessed": False}, indent=2, default=str))


if __name__ == "__main__":
    main()
