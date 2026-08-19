#!/usr/bin/env python3
"""TravisTorrent feature-importance, excluding test-duration-derived features.

Addresses the 2026-08-13 consensus review's finding (IEEE stream, "F2"): the
manuscript's claim that "Test-phase metrics lead 5 of 7 TravisTorrent
projects" is confounded because the regression target is build duration
(`tr_duration`) and the leading Test-phase feature in most projects is
`tr_log_testduration` or a rolling/lag derivative of it -- the duration of the
test phase, parsed from the same build log whose *total* duration is the
target. Test duration is an additive component of build duration, so a model
ranking it #1 has found a definitional/arithmetic relationship, not a
testing-infrastructure effect -- the same failure mode the manuscript
correctly flags for GHALogs' `mean_n_steps` two sections later.

This script reruns run_project_importance() (imported from the existing
travistorrent_feature_importance.py, not duplicated) with every feature whose
name contains "testduration" removed from the feature matrix before fitting
and computing permutation importance, and reports whether the "Test-phase
leads" pattern survives.

Usage: python travistorrent_feature_importance_excl_testduration.py [--verbose]
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

import run_pipeline_travistorrent as rp  # noqa: E402


def run_project_importance_excl(df_all: pd.DataFrame, project: str, verbose: bool = False) -> dict:
    df = df_all[df_all["gh_project_name"] == project].copy()
    df = rp.engineer(df)
    df = rp.remove_outliers(df)
    X, y = rp.prepare_features(df)

    excluded = [c for c in X.columns if "testduration" in c]
    X = X.drop(columns=excluded)

    split = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

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
        print(f"  [{project}] excluded {len(excluded)} testduration-derived features; "
              f"best model: {best['name']} (R2={best['holdout_r2']:.4f})")

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
        "n_excluded": len(excluded),
        "top5": fi.head(5).to_dict("records"),
    }


PHASE_PREFIXES = {
    "Test": ["tr_log_num_tests", "gh_test_lines_per_kloc", "gh_asserts_cases_per_kloc", "tr_log_buildduration"],
    "Project": ["gh_team_size", "gh_repo_age", "gh_repo_num_commits", "gh_num_commits_on_files_touched",
                "gh_sloc", "gh_first_pr", "gh_diff_files"],
    "Build": ["tr_log_setup_time", "build_test_ratio"],
    "Code": ["git_diff_src_churn", "git_num_all_built_commits"],
}


def classify(feature: str) -> str:
    base = feature.split("_rolling_")[0].split("_lag_")[0].split("_diff_")[0]
    for phase, prefixes in PHASE_PREFIXES.items():
        if any(base == p or base.startswith(p) for p in prefixes):
            return phase
    return "Other"


def main() -> None:
    verbose = "--verbose" in sys.argv
    df_all = rp.load_all(verbose=False)
    projects = sorted(df_all["gh_project_name"].unique())

    all_results = []
    for project in projects:
        try:
            res = run_project_importance_excl(df_all, project, verbose=verbose)
            all_results.append(res)
        except Exception as e:
            print(f"  [{project}] FAILED: {e}")

    lines = ["# TravisTorrent Feature Importance, Excluding Test-Duration-Derived Features", ""]
    lines.append(
        "Reruns permutation importance with every `tr_log_testduration`-derived feature "
        "(base feature + rolling/lag/diff variants) removed before fitting, to check whether "
        "the \"Test-phase metrics lead 5 of 7 projects\" claim survives once the "
        "definitionally-entangled feature (test duration is a component of the build-duration "
        "target) is excluded."
    )
    lines.append("")
    lines.append("| Project | Best Model | Holdout R² | # excluded | Top feature (perm. importance) | Phase |")
    lines.append("|---|---|---:|---:|---|---|")
    phase_counts = {}
    for res in all_results:
        top1 = res["top5"][0]
        phase = classify(top1["feature"])
        phase_counts[phase] = phase_counts.get(phase, 0) + 1
        lines.append(
            f"| {res['project']} | {res['best_model']} | {res['holdout_r2']:.4f} | "
            f"{res['n_excluded']} | {top1['feature']} ({top1['importance']*100:.1f}%) | {phase} |"
        )
    lines.append("")
    lines.append("Leading-feature phase tally (excluding test-duration-derived features): " +
                  ", ".join(f"{k} {v}/{len(all_results)}" for k, v in sorted(phase_counts.items(), key=lambda kv: -kv[1])))
    lines.append("")
    lines.append("## Top 5 features per project (excluding test-duration-derived)")
    lines.append("")
    for res in all_results:
        lines.append(f"### {res['project']} ({res['best_model']}, R²={res['holdout_r2']:.4f})")
        lines.append("")
        lines.append("| Rank | Feature | Importance | Phase |")
        lines.append("|---:|---|---:|---|")
        for i, row in enumerate(res["top5"], start=1):
            lines.append(f"| {i} | {row['feature']} | {row['importance']*100:.2f}% | {classify(row['feature'])} |")
        lines.append("")

    out_path = _SCRIPT_DIR / "TRAVISTORRENT_FEATURE_IMPORTANCE_EXCL_TESTDURATION_RESULTS.md"
    out_path.write_text("\n".join(lines))
    print(f"\nReport written to {out_path}")
    print("Phase tally:", phase_counts)


if __name__ == "__main__":
    main()
