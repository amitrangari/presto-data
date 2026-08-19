#!/usr/bin/env python3
"""TravisTorrent feature-importance pass, closing the gap flagged in STATUS.md's R7
row: the reimplemented adapter (run_pipeline_travistorrent.py) reports per-model
R^2/MAE/RMSE only, so the original submission's "repository age is the most
consistently predictive feature across all 7 projects" claim could not be
reverified after reimplementation and was flagged unverified in main.md.

This script reuses run_pipeline_travistorrent.py's own data loading and feature
engineering (imported, not duplicated) and adds one thing: for each project's
winning model (the "best" model already selected by the adapter's own holdout R^2),
compute permutation importance on the held-out test set. Permutation importance is
used (not each model's own .feature_importances_/.coef_) because the winning model
differs by project (Linear Regression, Random Forest, and Gradient Boosting all
appear), and permutation importance is comparable across model types -- the same
methodological choice the paper's own primary-domain RQ2 analysis (Section 4.5)
makes for exactly this reason.

Usage: python travistorrent_feature_importance.py [--verbose]
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.inspection import permutation_importance
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

import run_pipeline_travistorrent as rp  # noqa: E402


def run_project_importance(df_all: pd.DataFrame, project: str, verbose: bool = False) -> dict:
    df = df_all[df_all["gh_project_name"] == project].copy()
    df = rp.engineer(df)
    df = rp.remove_outliers(df)
    X, y = rp.prepare_features(df)

    split = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    # Reuse the adapter's own model selection: refit every model, pick the one
    # with the best holdout R^2, exactly as run_pipeline_travistorrent.py does.
    results = []
    fitted_models = {}
    for name, model in rp.build_models().items():
        model.fit(X_train_s, y_train)
        fitted_models[name] = model
        pred = model.predict(X_test_s)
        from sklearn.metrics import r2_score
        results.append({"name": name, "holdout_r2": float(r2_score(y_test, pred))})

    best = max(results, key=lambda r: r["holdout_r2"])
    best_model = fitted_models[best["name"]]

    if verbose:
        print(f"  [{project}] best model: {best['name']} (R2={best['holdout_r2']:.4f}), "
              f"computing permutation importance ...")

    perm = permutation_importance(
        best_model, X_test_s, y_test, n_repeats=10, random_state=42, scoring="r2"
    )
    fi = (
        pd.DataFrame({"feature": X.columns, "importance": perm.importances_mean})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )

    return {
        "project": project,
        "best_model": best["name"],
        "holdout_r2": best["holdout_r2"],
        "top5": fi.head(5).to_dict("records"),
        "repo_age_rank": int(fi.index[fi["feature"] == "gh_repo_age"][0]) + 1
        if "gh_repo_age" in fi["feature"].values else None,
        "repo_age_importance": float(fi.loc[fi["feature"] == "gh_repo_age", "importance"].iloc[0])
        if "gh_repo_age" in fi["feature"].values else None,
    }


def format_report(all_results: list[dict]) -> str:
    lines = ["# TravisTorrent Feature Importance (Permutation, Winning Model Per Project)", ""]
    lines.append(
        "Closes the gap flagged in STATUS.md's R7 row: the reimplemented adapter "
        "(`run_pipeline_travistorrent.py`) reports per-model R2/MAE/RMSE only. This "
        "script adds permutation importance (n_repeats=10, on the holdout test set) "
        "for each project's own winning model, so the original submission's "
        "\"repository age is the most consistently predictive feature\" claim can be "
        "checked directly against the reimplemented pipeline."
    )
    lines.append("")
    lines.append("| Project | Best Model | Holdout R² | Top feature (perm. importance) | `gh_repo_age` rank |")
    lines.append("|---|---|---:|---|---|")
    n_top1 = 0
    n_top5 = 0
    for res in all_results:
        top1 = res["top5"][0]
        rank = res["repo_age_rank"]
        rank_str = f"#{rank} ({res['repo_age_importance']*100:.1f}%)" if rank else "n/a"
        if rank == 1:
            n_top1 += 1
        if rank and rank <= 5:
            n_top5 += 1
        lines.append(
            f"| {res['project']} | {res['best_model']} | {res['holdout_r2']:.4f} | "
            f"{top1['feature']} ({top1['importance']*100:.1f}%) | {rank_str} |"
        )
    lines.append("")
    lines.append(f"`gh_repo_age` is the #1 feature in {n_top1}/7 projects, and top-5 in {n_top5}/7 projects.")
    lines.append("")
    lines.append("## Top 5 features per project")
    lines.append("")
    for res in all_results:
        lines.append(f"### {res['project']} ({res['best_model']}, R²={res['holdout_r2']:.4f})")
        lines.append("")
        lines.append("| Rank | Feature | Importance |")
        lines.append("|---:|---|---:|")
        for i, row in enumerate(res["top5"], start=1):
            lines.append(f"| {i} | {row['feature']} | {row['importance']*100:.2f}% |")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    verbose = "--verbose" in sys.argv
    df_all = rp.load_all(verbose=False)

    all_results = []
    for project in rp.PROJECTS:
        print(f"\n=== {project} ===")
        all_results.append(run_project_importance(df_all, project, verbose=verbose))

    report = format_report(all_results)
    out_path = _SCRIPT_DIR / "TRAVISTORRENT_FEATURE_IMPORTANCE_RESULTS.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"\nReport saved to: {out_path}")
    print(report)


if __name__ == "__main__":
    main()
