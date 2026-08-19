#!/usr/bin/env python3
"""PRESTO pipeline applied to real SQuaD process-metrics data -- cross-sectional, per-project.

Scope note, read before citing this as a "correlation validation": SQuaD's `process_metrics.csv`
(62,449 releases, 440 open-source projects, CC-BY-4.0) records code-churn/commit-history process
metrics (LOC, lines added, churn, commit-author count, change-set size, release age) -- it does
**not** contain PRESTO's own 164-metric taxonomy (Test Pass Rate, Build Success Rate, System
Uptime, etc.), so there is no direct 1:1 name match to validate the copula's 84 hand-specified
correlation coefficients against. What this script *can* do honestly: test whether real
process-metric characteristics predict a real outcome -- here, defect-fix rate (`n_fix`, a
well-established process-metrics-predict-defects proxy in the SE literature, e.g. Nagappan et al.)
-- giving a fourth, independent real-world data point for RQ1 alongside TravisTorrent (build
duration), Perfherder (runtime performance), and GHALogs (CI duration).

Design mirrors GHALogs' cross-sectional adapter: aggregate to one row per project (440 rows) rather
than per-release (62,449 rows, dominated 27% by a single project -- apache#servicemix-bundles --
which would badly skew a release-level split). No historical target values are used as features
(mean_n_fix_per_release is computed once per project, not lagged), so like GHALogs this is a clean
test with no autoregressive-leakage risk.

Usage: python run_pipeline_squad.py --verbose
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

    # Require a minimum number of releases per project for a stable per-project mean.
    agg = agg[agg["n_releases_observed"] >= 5].reset_index(drop=True)
    if verbose:
        print(f"  {len(agg)} projects with >= 5 observed releases (aggregation unit)")
    return agg


def prepare_features(df: pd.DataFrame):
    y = df["mean_n_fix"]
    exclude = {"project_name", "mean_n_fix"}
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
    """Empirical correlation among SQuaD's available process metrics.

    Not a 1:1 check against the copula's 84 hand-specified pairs (no matching metric names exist
    in this dataset -- see module docstring) but a directional sanity check: does churn/change-set
    volume correlate positively with defect-fix rate, as classical process-metrics literature (and
    PRESTO's own copula assumptions in spirit, if not in exact metric identity) would predict?
    """
    cols = ["mean_n_fix", "mean_churn", "mean_max_churn", "mean_change_set",
            "mean_lines_added", "mean_n_auth", "mean_total_LOC", "mean_age"]
    corr = df[cols].corr(numeric_only=True)["mean_n_fix"].drop("mean_n_fix").sort_values(
        ascending=False
    )
    return corr


def main():
    agg = load_and_aggregate(verbose=True)
    X, y = prepare_features(agg)
    print(f"Samples (projects): {len(X)}, Features: {X.shape[1]}")
    print(f"Target (mean_n_fix per release) stats: mean={y.mean():.2f} "
          f"median={y.median():.2f} std={y.std():.2f}")

    results, feature_names = train_and_evaluate(X, y)
    print("\n--- Model Performance (process/churn characteristics -> mean defect-fix rate) ---")
    for r in sorted(results, key=lambda r: -r["holdout_r2"]):
        print(f"  {r['name']:20s} CV R2={r['cv_r2_mean']:.4f}+/-{r['cv_r2_std']:.4f}  "
              f"Holdout R2={r['holdout_r2']:.4f}  MAE={r['holdout_mae']:.2f}  "
              f"RMSE={r['holdout_rmse']:.2f}")

    rf = RandomForestRegressor(n_estimators=100, max_depth=10, min_samples_split=5,
                                min_samples_leaf=2, random_state=42)
    scaler = StandardScaler()
    n = len(X)
    split = int(n * 0.8)
    X_train_s = scaler.fit_transform(X.iloc[:split])
    rf.fit(X_train_s, y.iloc[:split])
    importances = sorted(zip(feature_names, rf.feature_importances_), key=lambda t: -t[1])

    corr = correlation_comparison(agg)

    report_path = SCRIPT_DIR / "output_squad_ml_results.md"
    with open(report_path, "w") as f:
        f.write("# ML Pipeline Results: SQuaD (real data, cross-sectional, per-project)\n\n")
        f.write(
            "**Task:** predict mean per-release defect-fix rate (`n_fix`) from real process/churn "
            "characteristics aggregated per project. **Not** a 1:1 validation of the copula's 84 "
            "hand-specified correlations -- SQuaD has no matching metric names for that (see script "
            "docstring); this is an independent real-world process-metrics-predict-outcome test.\n\n"
        )
        f.write("## Dataset Characteristics\n\n| Property | Value |\n|---|---|\n")
        f.write(f"| Projects (aggregation unit) | {len(X)} |\n")
        f.write(f"| Features | {X.shape[1]} |\n")
        f.write(f"| Target mean (n_fix/release) | {y.mean():.2f} |\n")
        f.write(f"| Target median (n_fix/release) | {y.median():.2f} |\n")
        f.write(f"| Target std (n_fix/release) | {y.std():.2f} |\n\n")
        f.write("## Model Performance\n\n")
        f.write("| Model | CV R2 (mean +/- std) | Holdout R2 | Holdout MAE | Holdout RMSE |\n")
        f.write("|---|---|---|---|---|\n")
        for r in sorted(results, key=lambda r: -r["holdout_r2"]):
            f.write(f"| {r['name']} | {r['cv_r2_mean']:.4f} +/- {r['cv_r2_std']:.4f} | "
                    f"{r['holdout_r2']:.4f} | {r['holdout_mae']:.2f} | {r['holdout_rmse']:.2f} |\n")
        f.write("\n## Feature Importances (Random Forest)\n\n| Rank | Feature | Importance |\n|---|---|---|\n")
        for i, (name, imp) in enumerate(importances, 1):
            f.write(f"| {i} | {name} | {imp:.4f} |\n")
        f.write("\n## Directional Correlation Check (not a 1:1 copula validation)\n\n")
        f.write(
            "Empirical correlation of each process metric with `mean_n_fix` "
            "(defect-fix rate), across the 440 aggregated projects:\n\n"
        )
        f.write("| Metric | Correlation with mean_n_fix |\n|---|---|\n")
        for name, val in corr.items():
            f.write(f"| {name} | {val:.3f} |\n")
        f.write("\n## Notes\n\n")
        f.write(
            "- Real SQuaD data (CC-BY-4.0), 62,449 releases across 440 open-source projects, "
            "aggregated to one row per project (>= 5 releases required) to avoid a single "
            "dominant project (apache#servicemix-bundles, 27% of raw rows) skewing a release-level split.\n"
        )
        f.write(
            "- No SQuaD metric maps 1:1 to any of PRESTO's 164 SDLC metrics or the copula's 84 "
            "hand-specified correlation pairs -- this adapter tests the paper's general "
            "process-metrics-predict-outcome thesis on independent real data, not the specific "
            "copula correlation values themselves.\n"
        )
        f.write(
            "- 80/20 split (rows in `process_metrics.csv` groupby-aggregation order, not "
            "date-sorted -- SQuaD's process_metrics.csv has no per-project release date column, "
            "unlike release_data.csv), StandardScaler fit on train only, 5-fold TimeSeriesSplit CV.\n"
        )
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
