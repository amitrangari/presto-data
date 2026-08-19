#!/usr/bin/env python3
"""PRESTO pipeline extension: does bug-triage metadata beat a bare alert flag?

Companion to run_pipeline_perfherder.py, which showed that the "WITHOUT target-derived (AR)
features" condition -- alert-history flags plus inter-push time gap only -- is a very weak
predictor of future performance values (no SDLC process-metric analog exists in Perfherder). This
script asks a narrower, honest follow-up: if we enrich that alert-history signal with the actual
bug-triage metadata Mozilla recorded once a regression got escalated to Bugzilla (severity,
priority, comment_count, confirmation status, from bugs_data.csv), does the non-AR feature set get
any more predictive, or is the ceiling really that low?

Signature selection note: the three curated signatures in run_pipeline_perfherder.py
(espn-loadtime, instagram-speedindex, nytimes-speedindex) each have only 0-2 alerts with a linked
bug number in the full 17,989-row alerts_data.csv -- nowhere near enough to fit a bug-metadata
feature. This script instead uses the two Perfherder signatures with the richest bug-linked alert
history that also have downloaded per-push timeseries data: signature 2614662 ("installer size",
osx-cross, autoland4, 90 bug-linked rows after push-level dedup) and signature 2922314
(osx-aarch64-shippable, autoland4, 52 bug-linked rows). Both are still real Perfherder regression
metrics (build-artifact-size regression tracking), just not the three page-load/speed-index
signatures used for the main AR comparison -- a different, deliberately bug-history-rich subset of
the same real dataset, chosen for this specific question.

Usage: python run_pipeline_perfherder_bugs.py --verbose
"""
from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

SCRIPT_DIR = Path(__file__).resolve().parent

SIGNATURES = {
    "installer-size-osx-cross": {
        "id": "2614662",
        "path": "timeseries-data/autoland4/autoland4/2614662_timeseries_data.csv",
        "description": "Installer size (bytes), osx-cross, autoland4",
    },
    "build-metric-osx-aarch64": {
        "id": "2922314",
        "path": "timeseries-data/autoland4/autoland4/2922314_timeseries_data.csv",
        "description": "Build metric, osx-aarch64-shippable, autoland4",
    },
}

LAG_STEPS = [1, 2, 3, 5]

SEVERITY_MAP = {"S1": 4, "S2": 3, "S3": 2, "S4": 1}
PRIORITY_MAP = {"P1": 5, "P2": 4, "P3": 3, "P4": 2, "P5": 1}


def load_bug_metadata() -> pd.DataFrame:
    bugs = pd.read_csv(
        SCRIPT_DIR / "bugs_data.csv",
        usecols=["id", "severity", "priority", "comment_count", "is_confirmed"],
    )
    bugs["severity_ord"] = bugs["severity"].map(SEVERITY_MAP).fillna(0).astype(int)
    bugs["priority_ord"] = bugs["priority"].map(PRIORITY_MAP).fillna(0).astype(int)
    bugs["comment_count"] = pd.to_numeric(bugs["comment_count"], errors="coerce").fillna(0)
    bugs["is_confirmed"] = bugs["is_confirmed"].astype(str).str.lower().eq("true").astype(int)
    return bugs.set_index("id")[["severity_ord", "priority_ord", "comment_count", "is_confirmed"]]


def load_signature_series(path: Path, bug_meta: pd.DataFrame, verbose: bool = False) -> pd.DataFrame:
    df = pd.read_csv(
        path, usecols=["push_timestamp", "value", "revision", "alert_summary_bug_number"]
    )
    df["push_timestamp"] = pd.to_datetime(df["push_timestamp"])
    df = df.sort_values("push_timestamp").reset_index(drop=True)

    def first_bug(s: pd.Series):
        s = s.dropna()
        return s.iloc[0] if len(s) else np.nan

    df = df.groupby("push_timestamp", as_index=False).agg(
        value=("value", "mean"),
        revision=("revision", "first"),
        alert_summary_bug_number=("alert_summary_bug_number", first_bug),
    )
    df["had_alert"] = df["alert_summary_bug_number"].notna().astype(int)

    df["bug_id"] = df["alert_summary_bug_number"]
    joined = df.join(bug_meta, on="bug_id")
    for col in ["severity_ord", "priority_ord", "comment_count", "is_confirmed"]:
        df[col] = joined[col].fillna(0)

    if verbose:
        print(f"  Loaded {len(df)} pushes, {df['had_alert'].sum()} with a linked bug, "
              f"mean severity_ord (non-zero)={df.loc[df['had_alert']==1, 'severity_ord'].mean():.2f}")
    return df


def add_lag_and_history_features(df: pd.DataFrame, verbose: bool = False) -> pd.DataFrame:
    df_out = df.copy()
    for lag in LAG_STEPS:
        df_out[f"had_alert_lag_{lag}"] = df_out["had_alert"].shift(lag)
        df_out[f"severity_lag_{lag}"] = df_out["severity_ord"].shift(lag)
        df_out[f"priority_lag_{lag}"] = df_out["priority_ord"].shift(lag)
        df_out[f"comment_count_lag_{lag}"] = df_out["comment_count"].shift(lag)

    # cumulative history up to (not including) the current row -- no leakage
    shifted_alert = df_out["had_alert"].shift(1).fillna(0)
    shifted_sev = df_out["severity_ord"].shift(1).fillna(0)
    shifted_pri = df_out["priority_ord"].shift(1).fillna(0)
    df_out["n_alerts_so_far"] = shifted_alert.cumsum()
    df_out["mean_severity_so_far"] = shifted_sev.replace(0, np.nan).expanding().mean().fillna(0)
    df_out["max_severity_so_far"] = shifted_sev.cummax()
    df_out["mean_priority_so_far"] = shifted_pri.replace(0, np.nan).expanding().mean().fillna(0)

    # pushes since the last bug-linked alert
    last_alert_idx = pd.Series(np.where(shifted_alert == 1, np.arange(len(df_out)), np.nan))
    last_alert_idx = last_alert_idx.ffill()
    df_out["pushes_since_last_bug"] = (np.arange(len(df_out)) - last_alert_idx).fillna(len(df_out))

    df_out["push_gap_hours"] = df_out["push_timestamp"].diff().dt.total_seconds() / 3600.0
    df_out = df_out.ffill().bfill()
    for col in df_out.select_dtypes(include=[np.number]).columns:
        if df_out[col].isna().any():
            df_out[col] = df_out[col].fillna(df_out[col].mean())
    df_out = df_out.replace([np.inf, -np.inf], np.nan)
    for col in df_out.select_dtypes(include=[np.number]).columns:
        if df_out[col].isna().any():
            df_out[col] = df_out[col].fillna(df_out[col].mean())
    if verbose:
        print(f"  Feature engineering done: {df_out.shape[1]} columns")
    return df_out


def prepare_feature_sets(df: pd.DataFrame):
    y = df["value"].copy()
    alert_only_cols = [f"had_alert_lag_{lag}" for lag in LAG_STEPS] + ["push_gap_hours"]
    bug_enriched_cols = alert_only_cols + [
        f"severity_lag_{lag}" for lag in LAG_STEPS
    ] + [
        f"priority_lag_{lag}" for lag in LAG_STEPS
    ] + [
        f"comment_count_lag_{lag}" for lag in LAG_STEPS
    ] + [
        "n_alerts_so_far", "mean_severity_so_far", "max_severity_so_far",
        "mean_priority_so_far", "pushes_since_last_bug",
    ]
    return y, df[alert_only_cols].copy(), df[bug_enriched_cols].copy()


def build_models():
    return {
        "Linear Regression": LinearRegression(),
        "Ridge Regression": Ridge(alpha=1.0),
        "Lasso Regression": Lasso(alpha=1.0),
        "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(random_state=42),
    }


def train_and_evaluate(X: pd.DataFrame, y: pd.Series):
    n = len(X)
    split_idx = int(n * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    n_splits = min(5, max(2, split_idx // 20))
    tscv = TimeSeriesSplit(n_splits=n_splits)
    results = []
    for name, model in build_models().items():
        cv_scores = []
        for tr_idx, val_idx in tscv.split(X_train_s):
            model.fit(X_train_s[tr_idx], y_train.iloc[tr_idx])
            pred = model.predict(X_train_s[val_idx])
            cv_scores.append(r2_score(y_train.iloc[val_idx], pred))
        model.fit(X_train_s, y_train)
        pred_test = model.predict(X_test_s)
        results.append({
            "name": name,
            "cv_r2_mean": float(np.mean(cv_scores)),
            "cv_r2_std": float(np.std(cv_scores)),
            "holdout_r2": float(r2_score(y_test, pred_test)),
            "holdout_mae": float(mean_absolute_error(y_test, pred_test)),
            "holdout_rmse": float(np.sqrt(mean_squared_error(y_test, pred_test))),
        })
    return results


def run_signature(name: str, spec: dict, bug_meta: pd.DataFrame, verbose: bool = False):
    print(f"\n{'='*70}\n  Signature: {name} ({spec['description']})\n{'='*70}")
    path = SCRIPT_DIR / spec["path"]
    df = load_signature_series(path, bug_meta, verbose=verbose)
    df_eng = add_lag_and_history_features(df, verbose=verbose)
    y, X_alert_only, X_bug_enriched = prepare_feature_sets(df_eng)

    print(f"  Samples: {len(df_eng)}, alert-only features: {X_alert_only.shape[1]}, "
          f"bug-enriched features: {X_bug_enriched.shape[1]}")

    print("\n  --- Alert-flag-only baseline ---")
    results_baseline = train_and_evaluate(X_alert_only, y)
    for r in sorted(results_baseline, key=lambda r: -r["holdout_r2"]):
        print(f"    {r['name']:20s} CV R2={r['cv_r2_mean']:.4f}+/-{r['cv_r2_std']:.4f}  "
              f"Holdout R2={r['holdout_r2']:.4f}")

    print("\n  --- Bug-metadata-enriched ---")
    results_enriched = train_and_evaluate(X_bug_enriched, y)
    for r in sorted(results_enriched, key=lambda r: -r["holdout_r2"]):
        print(f"    {r['name']:20s} CV R2={r['cv_r2_mean']:.4f}+/-{r['cv_r2_std']:.4f}  "
              f"Holdout R2={r['holdout_r2']:.4f}")

    return results_baseline, results_enriched, len(df_eng), int(df_eng["had_alert"].sum())


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    bug_meta = load_bug_metadata()
    all_results = {}
    for name, spec in SIGNATURES.items():
        all_results[name] = run_signature(name, spec, bug_meta, verbose=args.verbose)

    report_path = SCRIPT_DIR / "output" / "bug_enrichment_ml_results.md"
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, "w") as f:
        f.write("# ML Pipeline Results: Bug-Metadata Enrichment (Mozilla Perfherder, real data)\n\n")
        f.write(
            "**Question:** does enriching the non-AR (\"WITHOUT target-derived features\") "
            "condition from `run_pipeline_perfherder.py` with real Bugzilla triage metadata "
            "(severity, priority, comment_count from `bugs_data.csv`, joined via "
            "`alert_summary_bug_number`) improve on a bare alert-flag baseline?\n\n"
        )
        f.write(
            "Signature note: the three original AR-comparison signatures (espn-loadtime, "
            "instagram-speedindex, nytimes-speedindex) each have only 0-2 bug-linked alerts in "
            "the full alerts history -- too sparse for this question. Ran instead on the two "
            "signatures with the richest bug-linked alert history among downloaded timeseries "
            "data.\n\n"
        )
        for name, spec in SIGNATURES.items():
            results_baseline, results_enriched, n_samples, n_alerts = all_results[name]
            f.write(f"## {name} ({spec['description']})\n\n")
            f.write(f"Samples (pushes): {n_samples}, bug-linked alert rows: {n_alerts}\n\n")
            f.write("### Alert-flag-only baseline\n\n")
            f.write("| Model | CV R2 | Holdout R2 | Holdout MAE | Holdout RMSE |\n|---|---|---|---|---|\n")
            for r in sorted(results_baseline, key=lambda r: -r["holdout_r2"]):
                f.write(f"| {r['name']} | {r['cv_r2_mean']:.4f}+/-{r['cv_r2_std']:.4f} | "
                        f"{r['holdout_r2']:.4f} | {r['holdout_mae']:.2f} | {r['holdout_rmse']:.2f} |\n")
            f.write("\n### Bug-metadata-enriched\n\n")
            f.write("| Model | CV R2 | Holdout R2 | Holdout MAE | Holdout RMSE |\n|---|---|---|---|---|\n")
            for r in sorted(results_enriched, key=lambda r: -r["holdout_r2"]):
                f.write(f"| {r['name']} | {r['cv_r2_mean']:.4f}+/-{r['cv_r2_std']:.4f} | "
                        f"{r['holdout_r2']:.4f} | {r['holdout_mae']:.2f} | {r['holdout_rmse']:.2f} |\n")
            best_base = max(results_baseline, key=lambda r: r["holdout_r2"])
            best_enr = max(results_enriched, key=lambda r: r["holdout_r2"])
            f.write(f"\nBest holdout R2: baseline={best_base['holdout_r2']:.4f} "
                    f"({best_base['name']}) vs. bug-enriched={best_enr['holdout_r2']:.4f} "
                    f"({best_enr['name']}); delta={best_enr['holdout_r2']-best_base['holdout_r2']:+.4f}\n\n")
        f.write("## Notes\n\n")
        f.write(
            "- Real Mozilla Perfherder + Bugzilla data (CC-BY-4.0). Severity mapped S1=4..S4=1, "
            "priority P1=5..P5=1, unset/\"--\" = 0.\n"
        )
        f.write(
            "- All bug-metadata features are lagged or built from `.shift(1)`-then-cumulative "
            "history, so no row uses its own or a future push's bug outcome -- no look-ahead "
            "leakage.\n"
        )
        f.write(
            "- 80/20 temporal split, TimeSeriesSplit CV, StandardScaler fit on train only -- same "
            "protocol as `run_pipeline_perfherder.py`.\n"
        )
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
