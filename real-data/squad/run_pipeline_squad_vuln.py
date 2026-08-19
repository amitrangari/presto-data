#!/usr/bin/env python3
"""PRESTO pipeline applied to real SQuaD process-metrics + CVE data -- cross-sectional, per-project.

Companion to run_pipeline_squad.py (which predicts mean defect-fix rate). This script asks a
different question: do code-churn/commit-history process characteristics predict how many
disclosed CVEs a project accumulates? SQuaD ships cve_data.csv (5,294 CVE-linkage rows, 175
distinct projects, 1,479 distinct CVE IDs, sourced from GitHub Dependabot/security-advisory
linkage per the SQuaD MSR'24 dataset paper) alongside the same process_metrics.csv used by the
defect-fix-rate adapter, so the same 408-project (>=5 releases) aggregation unit is reused here
for consistency and to keep the two SQuaD analyses directly comparable.

Target: log1p(cve_count) per project, where cve_count is the number of distinct CVE IDs linked to
that project's issue tracker (0 for the 247/408 projects with no linked CVE; heavy right skew --
top project apache#ofbiz-framework has 222 -- hence the log1p transform). This is a legitimate but
harder task than the defect-fix-rate one: CVE disclosure is driven as much by a project's exposure
surface (is it widely used enough to be scanned by security researchers) and library-dependency
footprint as by its own process metrics, so a weak result here is scientifically informative, not
a failure of the pipeline.

Usage: python run_pipeline_squad_vuln.py --verbose
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

NUMERIC_COLS = [
    "total_LOC", "t_lines", "lines_added", "max_lines_added", "avg_lines_added",
    "weighted_age", "n_fix", "n_auth", "churn", "max_churn", "avg_churn",
    "max_change_set", "avg_change_set", "age",
]


def load_and_aggregate(verbose: bool = False) -> pd.DataFrame:
    print("Loading process_metrics.csv ...")
    df = pd.read_csv(SCRIPT_DIR / "process_metrics.csv")
    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if verbose:
        print(f"  {len(df)} releases across {df['project_name'].nunique()} projects")

    agg = df.groupby("project_name").agg(
        n_releases_observed=("release", "count"),
        mean_n_fix=("n_fix", "mean"),
        mean_total_LOC=("total_LOC", "mean"),
        mean_lines_added=("lines_added", "mean"),
        mean_max_lines_added=("max_lines_added", "mean"),
        mean_churn=("churn", "mean"),
        mean_max_churn=("max_churn", "mean"),
        mean_avg_churn=("avg_churn", "mean"),
        mean_n_auth=("n_auth", "mean"),
        mean_change_set=("avg_change_set", "mean"),
        mean_max_change_set=("max_change_set", "mean"),
        mean_age=("age", "mean"),
        mean_weighted_age=("weighted_age", "mean"),
        std_churn=("churn", "std"),
    ).reset_index()

    agg = agg[agg["n_releases_observed"] >= 5].reset_index(drop=True)
    if verbose:
        print(f"  {len(agg)} projects with >= 5 observed releases (aggregation unit)")

    print("Loading cve_data.csv ...")
    cve = pd.read_csv(SCRIPT_DIR / "cve_data.csv", usecols=["project_name", "cve_id"])
    cve_counts = cve.groupby("project_name")["cve_id"].nunique().rename("cve_count")
    if verbose:
        print(f"  {len(cve)} CVE-linkage rows, {cve['project_name'].nunique()} distinct "
              f"projects, {cve['cve_id'].nunique()} distinct CVE IDs")

    agg = agg.merge(cve_counts, on="project_name", how="left")
    agg["cve_count"] = agg["cve_count"].fillna(0).astype(int)
    agg["has_cve"] = (agg["cve_count"] > 0).astype(int)
    agg["log_cve_count"] = np.log1p(agg["cve_count"])
    if verbose:
        print(f"  {agg['has_cve'].sum()}/{len(agg)} projects have >=1 linked CVE "
              f"(max={agg['cve_count'].max()}, mean={agg['cve_count'].mean():.2f})")
    return agg


def prepare_features(df: pd.DataFrame):
    y = df["log_cve_count"]
    exclude = {"project_name", "cve_count", "has_cve", "log_cve_count"}
    feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in exclude]
    X = df[feature_cols].copy()
    for col in X.columns:
        if X[col].isna().any():
            X[col] = X[col].fillna(X[col].median())
    return X, y


def build_models():
    return {
        "Linear Regression": LinearRegression(),
        "Ridge Regression": Ridge(alpha=1.0),
        "Lasso Regression": Lasso(alpha=1.0),
        "Random Forest": RandomForestRegressor(
            n_estimators=100, max_depth=10, min_samples_split=5,
            min_samples_leaf=2, random_state=42,
        ),
        "Gradient Boosting": GradientBoostingRegressor(
            n_estimators=100, max_depth=6, learning_rate=0.1,
            min_samples_split=5, min_samples_leaf=2, random_state=42,
        ),
    }


def train_and_evaluate(X: pd.DataFrame, y: pd.Series):
    n = len(X)
    split = int(n * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    tscv = TimeSeriesSplit(n_splits=5)
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
    return results, X_train.columns.tolist()


def correlation_comparison(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["cve_count", "mean_n_fix", "mean_churn", "mean_max_churn", "mean_change_set",
            "mean_lines_added", "mean_n_auth", "mean_total_LOC", "mean_age"]
    corr = df[cols].corr(numeric_only=True)["cve_count"].drop("cve_count").sort_values(
        ascending=False
    )
    return corr


def main():
    agg = load_and_aggregate(verbose=True)
    X, y = prepare_features(agg)
    print(f"Samples (projects): {len(X)}, Features: {X.shape[1]}")
    print(f"Target (log1p cve_count) stats: mean={y.mean():.3f} median={y.median():.3f} "
          f"std={y.std():.3f}")

    results, feature_names = train_and_evaluate(X, y)
    print("\n--- Model Performance (process/churn characteristics -> log1p CVE count) ---")
    for r in sorted(results, key=lambda r: -r["holdout_r2"]):
        print(f"  {r['name']:20s} CV R2={r['cv_r2_mean']:.4f}+/-{r['cv_r2_std']:.4f}  "
              f"Holdout R2={r['holdout_r2']:.4f}  MAE={r['holdout_mae']:.3f}  "
              f"RMSE={r['holdout_rmse']:.3f}")

    rf = RandomForestRegressor(n_estimators=100, max_depth=10, min_samples_split=5,
                                min_samples_leaf=2, random_state=42)
    scaler = StandardScaler()
    n = len(X)
    split = int(n * 0.8)
    X_train_s = scaler.fit_transform(X.iloc[:split])
    rf.fit(X_train_s, y.iloc[:split])
    importances = sorted(zip(feature_names, rf.feature_importances_), key=lambda t: -t[1])

    corr = correlation_comparison(agg)

    report_path = SCRIPT_DIR / "output_squad_vuln_ml_results.md"
    with open(report_path, "w") as f:
        f.write("# ML Pipeline Results: SQuaD Vulnerability Prediction (real data, cross-sectional, per-project)\n\n")
        f.write(
            "**Task:** predict `log1p(cve_count)` -- the number of distinct CVE IDs linked to a "
            "project's issue tracker -- from real process/churn characteristics aggregated per "
            "project. Companion to the defect-fix-rate SQuaD adapter "
            "(`output_squad_ml_results.md`); same 408-project aggregation unit, different real "
            "outcome variable (security vulnerabilities instead of bug-fix commits).\n\n"
        )
        f.write("## Dataset Characteristics\n\n| Property | Value |\n|---|---|\n")
        f.write(f"| Projects (aggregation unit) | {len(X)} |\n")
        f.write(f"| Projects with >=1 linked CVE | {int(agg['has_cve'].sum())} "
                f"({100*agg['has_cve'].mean():.1f}%) |\n")
        f.write(f"| Features | {X.shape[1]} |\n")
        f.write(f"| Max CVE count (single project) | {int(agg['cve_count'].max())} |\n")
        f.write(f"| Mean CVE count | {agg['cve_count'].mean():.2f} |\n")
        f.write(f"| Target mean (log1p cve_count) | {y.mean():.3f} |\n")
        f.write(f"| Target std (log1p cve_count) | {y.std():.3f} |\n\n")
        f.write("## Model Performance\n\n")
        f.write("| Model | CV R2 (mean +/- std) | Holdout R2 | Holdout MAE | Holdout RMSE |\n")
        f.write("|---|---|---|---|---|\n")
        for r in sorted(results, key=lambda r: -r["holdout_r2"]):
            f.write(f"| {r['name']} | {r['cv_r2_mean']:.4f} +/- {r['cv_r2_std']:.4f} | "
                    f"{r['holdout_r2']:.4f} | {r['holdout_mae']:.3f} | {r['holdout_rmse']:.3f} |\n")
        f.write("\n## Feature Importances (Random Forest)\n\n| Rank | Feature | Importance |\n|---|---|---|\n")
        for i, (name, imp) in enumerate(importances, 1):
            f.write(f"| {i} | {name} | {imp:.4f} |\n")
        f.write("\n## Directional Correlation Check\n\n")
        f.write(
            "Empirical correlation of each process metric with raw `cve_count`, across the "
            f"{len(agg)} aggregated projects:\n\n"
        )
        f.write("| Metric | Correlation with cve_count |\n|---|---|\n")
        for name, val in corr.items():
            f.write(f"| {name} | {val:.3f} |\n")
        f.write("\n## Notes\n\n")
        f.write(
            "- CVE linkage from SQuaD's `cve_data.csv` (5,294 rows, 175 distinct projects, 1,479 "
            "distinct CVE IDs, GitHub Dependabot/security-advisory sourced). 247/408 qualifying "
            "projects (>=5 releases) have zero linked CVEs; target is heavily right-skewed "
            "(max 222, apache#ofbiz-framework), hence log1p transform.\n"
        )
        f.write(
            "- Interpret with caution: CVE disclosure count reflects a project's exposure surface "
            "(popularity, dependency-scanner coverage) at least as much as its own process "
            "characteristics, so this is a harder and more confounded prediction target than "
            "defect-fix rate. A weak result is a substantive finding about the limits of "
            "process-metrics-only vulnerability prediction, not a pipeline failure.\n"
        )
        f.write(
            "- Same aggregation, split (80/20, in groupby-aggregation row order), scaling "
            "(StandardScaler fit on train only), and 5-fold TimeSeriesSplit CV protocol as the "
            "companion defect-fix-rate adapter, to keep the two SQuaD results directly comparable.\n"
        )
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
