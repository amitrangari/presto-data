#!/usr/bin/env python3
"""PRESTO pipeline applied to real GHALogs CI/CD data -- cross-sectional variant.

Scope note: GHALogs samples a maximum of 5 runs per repository+workflow (117,295 combinations,
mean 4.4 runs each) -- too short for the within-entity time-series forecasting used for the
synthetic domains and the Perfherder/TravisTorrent validations. This precludes lag/rolling
autoregressive features entirely, which turns out to be a methodological advantage here: this
script tests PRESTO's actual headline claim -- do real process/repository characteristics predict
CI performance? -- with **zero possibility of target-derived leakage**, since no historical target
values exist per repository to leak from. Complementary to Perfherder (validates the AR-features
side on real data) and TravisTorrent (validates within-project temporal prediction).

Pipeline: repositories.json.gz (repo-level process/popularity metrics) joined with
run_features.csv (per-run build/test timing, produced by extract_run_features.py) aggregated to
one row per repository, predicting mean total CI run duration from repo characteristics.

Usage: python run_pipeline_ghalogs.py --verbose
"""
from __future__ import annotations

import csv
import gzip
import json
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
REPO_FEATURES = ["commits", "branches", "releases", "contributors", "watchers", "stargazers",
                  "forks", "size", "totalIssues", "openIssues", "totalPullRequests",
                  "openPullRequests", "blankLines", "codeLines", "commentLines"]


def load_repo_aggregates(verbose=False) -> pd.DataFrame:
    print("Loading run_features.csv and aggregating per repository...")
    df = pd.read_csv(SCRIPT_DIR / "run_features.csv")
    df["is_success"] = (df["conclusion"] == "success").astype(int)
    agg = df.groupby("repository_name").agg(
        n_runs_sampled=("run_number", "count"),
        mean_total_time=("total_step_time_sec", "mean"),
        mean_build_time=("build_time_sec", "mean"),
        mean_test_time=("test_time_sec", "mean"),
        mean_setup_time=("setup_time_sec", "mean"),
        mean_n_steps=("n_steps", "mean"),
        success_rate=("is_success", "mean"),
    ).reset_index()
    if verbose:
        print(f"  {len(agg)} repositories with run data")
    return agg


def load_repo_metadata(verbose=False) -> pd.DataFrame:
    print("Streaming repositories.json.gz...")
    rows = []
    with gzip.open(SCRIPT_DIR / "repositories.json.gz", "rt") as f:
        for i, line in enumerate(f):
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            repo = d.get("repo") or {}
            if not repo:
                continue
            row = {"repository_name": repo.get("name")}
            for k in REPO_FEATURES:
                row[k] = repo.get(k)
            row["mainLanguage"] = repo.get("mainLanguage") or "unknown"
            row["pushedAt"] = repo.get("pushedAt")
            row["createdAt"] = repo.get("createdAt")
            row["isArchived"] = int(bool(repo.get("isArchived")))
            row["hasWiki"] = int(bool(repo.get("hasWiki")))
            rows.append(row)
    df = pd.DataFrame(rows)
    if verbose:
        print(f"  {len(df)} repositories in metadata")
    return df


def engineer(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["pushedAt"] = pd.to_datetime(df["pushedAt"], errors="coerce")
    df["createdAt"] = pd.to_datetime(df["createdAt"], errors="coerce")
    df["repo_age_days"] = (df["pushedAt"] - df["createdAt"]).dt.total_seconds() / 86400.0
    # cross-phase-style composite features, mirroring the synthetic pipeline's stability_score/quality_score
    df["issue_resolution_rate"] = 1 - (df["openIssues"] / (df["totalIssues"] + 1))
    df["pr_resolution_rate"] = 1 - (df["openPullRequests"] / (df["totalPullRequests"] + 1))
    df["comment_density"] = df["commentLines"] / (df["codeLines"] + 1)
    # top-10 languages one-hot, rest bucketed as "other"
    top_langs = df["mainLanguage"].value_counts().head(10).index
    df["mainLanguage"] = df["mainLanguage"].where(df["mainLanguage"].isin(top_langs), "other")
    df = pd.get_dummies(df, columns=["mainLanguage"], prefix="lang")
    return df


def prepare_features(df: pd.DataFrame):
    y = df["mean_total_time"]
    exclude = {"repository_name", "pushedAt", "createdAt", "mean_total_time", "mean_build_time",
               "mean_test_time", "mean_setup_time", "n_runs_sampled"}
    feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in exclude]
    X = df[feature_cols].copy()
    for col in X.columns:
        if X[col].isna().any():
            X[col] = X[col].fillna(X[col].median())
    return X, y


def train_and_evaluate(X, y):
    n = len(X)
    split = int(n * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    models = {
        "Linear Regression": LinearRegression(),
        "Ridge Regression": Ridge(alpha=1.0),
        "Lasso Regression": Lasso(alpha=1.0),
        "Random Forest": RandomForestRegressor(n_estimators=100, max_depth=10, min_samples_split=5,
                                                min_samples_leaf=2, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=100, max_depth=6, learning_rate=0.1,
                                                         min_samples_split=5, min_samples_leaf=2, random_state=42),
    }
    tscv = TimeSeriesSplit(n_splits=5)
    results = []
    for name, model in models.items():
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
    return results, X_train.columns.tolist()


def main():
    run_agg = load_repo_aggregates(verbose=True)
    repo_meta = load_repo_metadata(verbose=True)
    merged = run_agg.merge(repo_meta, on="repository_name", how="inner")
    print(f"Merged: {len(merged)} repositories with both run data and metadata")

    merged = engineer(merged)
    merged = merged.dropna(subset=["mean_total_time"])
    merged = merged.sort_values("pushedAt")  # chronological split, not random

    X, y = prepare_features(merged)
    print(f"Samples: {len(X)}, Features: {X.shape[1]}")
    print(f"Target (mean_total_time) stats: mean={y.mean():.1f}s std={y.std():.1f}s "
          f"median={y.median():.1f}s")

    results, feature_names = train_and_evaluate(X, y)
    print("\n--- Model Performance (repo process characteristics -> mean CI run duration) ---")
    for r in sorted(results, key=lambda r: -r["holdout_r2"]):
        print(f"  {r['name']:20s} CV R2={r['cv_r2_mean']:.4f}+/-{r['cv_r2_std']:.4f}  "
              f"Holdout R2={r['holdout_r2']:.4f}  MAE={r['holdout_mae']:.2f}  RMSE={r['holdout_rmse']:.2f}")

    # feature importance via Random Forest
    rf = RandomForestRegressor(n_estimators=100, max_depth=10, min_samples_split=5,
                                min_samples_leaf=2, random_state=42)
    scaler = StandardScaler()
    n = len(X)
    split = int(n * 0.8)
    X_train_s = scaler.fit_transform(X.iloc[:split])
    rf.fit(X_train_s, y.iloc[:split])
    importances = sorted(zip(feature_names, rf.feature_importances_), key=lambda t: -t[1])[:15]

    report_path = SCRIPT_DIR / "output_ghalogs_ml_results.md"
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, "w") as f:
        f.write("# ML Pipeline Results: GHALogs (real data, cross-sectional)\n\n")
        f.write("**Task:** predict mean CI run duration (seconds) from real repository "
                "process/popularity characteristics -- no target-derived features possible "
                "(cross-sectional, not time series; see README_VALIDATION.md for why).\n\n")
        f.write("## Dataset Characteristics\n\n| Property | Value |\n|---|---|\n")
        f.write(f"| Repositories | {len(X)} |\n| Features | {X.shape[1]} |\n")
        f.write(f"| Target mean (sec) | {y.mean():.1f} |\n| Target std (sec) | {y.std():.1f} |\n")
        f.write(f"| Target median (sec) | {y.median():.1f} |\n\n")
        f.write("## Model Performance\n\n")
        f.write("| Model | CV R2 (mean +/- std) | Holdout R2 | Holdout MAE | Holdout RMSE |\n|---|---|---|---|---|\n")
        for r in sorted(results, key=lambda r: -r["holdout_r2"]):
            f.write(f"| {r['name']} | {r['cv_r2_mean']:.4f} +/- {r['cv_r2_std']:.4f} | "
                     f"{r['holdout_r2']:.4f} | {r['holdout_mae']:.2f} | {r['holdout_rmse']:.2f} |\n")
        f.write("\n## Top 15 Feature Importances (Random Forest)\n\n| Rank | Feature | Importance |\n|---|---|---|\n")
        for i, (name, imp) in enumerate(importances, 1):
            f.write(f"| {i} | {name} | {imp:.4f} |\n")
        f.write("\n## Notes\n\n")
        f.write("- Real GHALogs data (CC-BY-SA-4.0), 117,295 repo+workflow combinations, capped at 5 runs each -- too short for within-entity AR features.\n")
        f.write("- Cross-sectional design: chronological (pushedAt-sorted) 80/20 split, TimeSeriesSplit CV, StandardScaler fit on train only.\n")
        f.write("- Zero target-derived features possible -- this is a clean test of the process-metrics-predict-performance claim with no leakage risk at all.\n")
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
