#!/usr/bin/env python3
"""M3 (consensus review, Phase 2): nested-CV alpha tuning for Ridge/Lasso.

The paper (Section 4.3 / 3.2.6) currently trains Ridge/Lasso with scikit-learn's
default alpha=1.0, untuned, and documents this as a deliberate choice (170 samples
risks overfitting hyperparameter search). M3 asks us to actually tune via nested CV
before concluding tree-based ensembles are "necessary" -- i.e. check whether an
untuned alpha is understating what linear models can do.

Protocol (nested, no holdout leakage):
  - Outer split: same fixed 80/20 temporal split used everywhere else in the paper.
  - Inner loop: GridSearchCV with TimeSeriesSplit(n_splits=5) *within the outer
    training set only* selects alpha from a log-spaced grid.
  - The selected alpha is then refit on the full outer training set and scored on
    the untouched outer holdout -- the holdout never participates in alpha selection.
  - Run for all 3 domains, in both the with-AR-features and without-AR-features
    (leakage-excluded) conditions, since the paper's "trees are necessary" framing
    (RQ3 / Section 4.3) is drawn primarily from the without-AR condition.

Usage: python m3_nested_cv_tuning.py [--verbose]
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.linear_model import Lasso, Ridge
from sklearn.metrics import r2_score
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

import run_pipeline as rp  # noqa: E402

ALPHA_GRID = {"alpha": np.logspace(-3, 6, 19).tolist()}  # 0.001 ... 1e6, 19 points


def tune_and_evaluate(X: pd.DataFrame, y: pd.Series, estimator_cls, verbose: bool = False):
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    tscv = TimeSeriesSplit(n_splits=5)
    grid = GridSearchCV(
        estimator_cls(), ALPHA_GRID, cv=tscv, scoring="r2", n_jobs=1
    )
    grid.fit(X_train_scaled, y_train)

    best_alpha = grid.best_params_["alpha"]
    best_inner_cv_r2 = grid.best_score_

    # Refit best alpha on full outer-train, score on the untouched outer holdout.
    tuned_model = estimator_cls(alpha=best_alpha)
    tuned_model.fit(X_train_scaled, y_train)
    y_pred = tuned_model.predict(X_test_scaled)
    tuned_holdout_r2 = float(r2_score(y_test, y_pred))

    # Baseline: fixed alpha=1.0, same split, for direct comparison.
    baseline_model = estimator_cls(alpha=1.0)
    baseline_model.fit(X_train_scaled, y_train)
    baseline_holdout_r2 = float(r2_score(y_test, baseline_model.predict(X_test_scaled)))

    if verbose:
        print(
            f"      best alpha={best_alpha:g}  inner CV R2={best_inner_cv_r2:.4f}  "
            f"tuned holdout R2={tuned_holdout_r2:.4f}  "
            f"(alpha=1.0 holdout R2={baseline_holdout_r2:.4f})"
        )

    return {
        "best_alpha": best_alpha,
        "inner_cv_r2": best_inner_cv_r2,
        "tuned_holdout_r2": tuned_holdout_r2,
        "baseline_holdout_r2": baseline_holdout_r2,
    }


DATA_ROOT = Path("/Volumes/4TB/research-data/presto/synthetic-data-projects")


def run_domain(domain: str, verbose: bool = False) -> dict:
    domain_dir = DATA_ROOT / domain
    df = rp.load_and_merge(domain_dir, verbose=False)
    df_eng = rp.engineer_features(df, verbose=False)

    X_with, y, _ = rp.prepare_features(df_eng, exclude_leakage=False)
    X_without, _, _ = rp.prepare_features(df_eng, exclude_leakage=True)

    out = {"domain": domain}
    for cond_name, X in (("with_AR", X_with), ("without_AR", X_without)):
        for model_name, cls in (("Ridge", Ridge), ("Lasso", Lasso)):
            if verbose:
                print(f"  [{domain}] {cond_name} / {model_name} ...")
            out[f"{cond_name}__{model_name}"] = tune_and_evaluate(X, y, cls, verbose=verbose)

    # Also grab Random Forest's without-AR holdout R2 for direct comparison
    # (same fixed hyperparameters as the rest of the paper -- RF/GB are not
    # in scope for M3, this is context only).
    rf = rp.build_models()["Random Forest"]
    split_idx = int(len(X_without) * 0.8)
    X_train, X_test = X_without.iloc[:split_idx], X_without.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    rf.fit(X_train_scaled, y_train)
    out["without_AR__RandomForest_holdout_r2"] = float(
        r2_score(y_test, rf.predict(X_test_scaled))
    )

    return out


def format_report(all_results: list[dict]) -> str:
    lines = ["# M3 — Nested-CV Alpha Tuning for Ridge/Lasso", ""]
    lines.append(
        "Protocol: GridSearchCV over alpha in [1e-3 .. 1e6] (19 log-spaced points -- "
        "widened from an initial [1e-3 .. 1e3] after two Ridge cases selected the "
        "grid boundary; all selected alphas are now interior points), inner "
        "cv=TimeSeriesSplit(5) within the fixed 80% outer-training split only; best "
        "alpha refit on the full outer-train, scored on the untouched 20% outer "
        "holdout. Compared against the paper's existing fixed alpha=1.0 baseline on "
        "the identical split."
    )
    lines.append("")
    for res in all_results:
        domain = res["domain"]
        lines.append(f"## {domain}")
        lines.append("")
        lines.append(
            "| Condition | Model | Best alpha | Inner CV R² | Tuned Holdout R² | "
            "alpha=1.0 Holdout R² | Δ (tuned − baseline) |"
        )
        lines.append("|---|---|---:|---:|---:|---:|---:|")
        for cond_name in ("with_AR", "without_AR"):
            for model_name in ("Ridge", "Lasso"):
                r = res[f"{cond_name}__{model_name}"]
                delta = r["tuned_holdout_r2"] - r["baseline_holdout_r2"]
                lines.append(
                    f"| {cond_name} | {model_name} | {r['best_alpha']:g} | "
                    f"{r['inner_cv_r2']:.4f} | {r['tuned_holdout_r2']:.4f} | "
                    f"{r['baseline_holdout_r2']:.4f} | {delta:+.4f} |"
                )
        lines.append("")
        lines.append(
            f"For context, Random Forest (fixed hyperparameters, unchanged) scores "
            f"holdout R² = {res['without_AR__RandomForest_holdout_r2']:.4f} on the "
            f"without-AR condition."
        )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    verbose = "--verbose" in sys.argv
    all_results = []
    for domain in rp.ALL_DOMAINS:
        print(f"\n=== {domain} ===")
        all_results.append(run_domain(domain, verbose=verbose))

    report = format_report(all_results)
    out_path = _SCRIPT_DIR / "M3_NESTED_CV_TUNING_EVIDENCE.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"\nReport saved to: {out_path}")
    print(report)


if __name__ == "__main__":
    main()
