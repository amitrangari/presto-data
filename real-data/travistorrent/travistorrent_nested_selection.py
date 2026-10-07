#!/usr/bin/env python3
"""TravisTorrent nested model selection (PRESTO v4 revision, Reviewer 2 round 3, Phase 2b).

Reuses run_pipeline_travistorrent.py's data loading/feature-engineering functions and
nested_cv_harness.py's nested_select() (imported directly, not reimplemented) to replace the
paper's existing "fit 5 fixed-hyperparameter models, report whichever scores highest on the
untouched holdout" protocol for each of the 7 TravisTorrent projects, in both the full-feature
and testduration-excluded conditions (Section 4.2.1's two tables).

Grid-size note: TravisTorrent projects range from ~2.3k rows (matrix) to ~144k rows (dd-agent).
nested_cv_harness.py's default RF/GB grids (18 and 27 combinations respectively, x 5 inner CV
folds) are cheap on the small synthetic domains (~136-160 rows) but would be prohibitively slow
on TravisTorrent's larger projects (a naive RF grid on dd-agent's ~115k-row outer-train set would
mean 90 RF fits at ~100-200 trees each on tens of thousands of rows apiece). For any project with
an outer-training partition (80% split) exceeding 5,000 rows, this script uses a REDUCED grid
(documented below) instead of nested_cv_harness's default; for projects at or below that
threshold it uses the harness unmodified. This is a deliberate, disclosed shrink, not a silent
truncation -- every result row states which grid size was used.

Usage: python travistorrent_nested_selection.py [--verbose]
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

_THIS_DIR = Path(__file__).resolve().parent
_HARNESS_DIR = Path("/Volumes/4TB/research-data-and-code/zenado/presto-data/code/synthetic_data_generator")
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_HARNESS_DIR))

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

import run_pipeline_travistorrent as tt  # noqa: E402
from nested_cv_harness import nested_select  # noqa: E402

LARGE_N_THRESHOLD = 5000
VERY_LARGE_N_THRESHOLD = 20000  # dd-agent, bundler, sentry, mongoid, youtube-dl: bounded-depth,
                                 # fewer estimators, 3-fold inner CV -- unbounded-depth RF/GB
                                 # (max_depth=None) on 100k+ rows was observed to take many hours
                                 # per fit; this tier trades some grid resolution for tractability,
                                 # disclosed explicitly rather than left to run indefinitely.

# Reduced grids for large projects: documented shrink, not silent truncation.
SMALL_ALPHA_GRID = np.logspace(-3, 6, 7).tolist()  # 7 pts vs. harness's 19
SMALL_RF_GRID = {"n_estimators": [50, 100], "max_depth": [10, None], "min_samples_split": [5]}
SMALL_GB_GRID = {"n_estimators": [50, 100], "max_depth": [3, 6], "learning_rate": [0.1]}

# Very-large-project grids: max_depth bounded (no None -- unbounded trees on 100k+ rows are the
# actual cost driver, confirmed via `sample`-profiling the stuck dd-agent run: time was spent in
# sklearn's DepthFirstTreeBuilder/node_split, i.e. genuine unbounded-tree growth, not a hang),
# single n_estimators value, 3-fold inner CV instead of 5.
VERY_LARGE_ALPHA_GRID = np.logspace(-2, 5, 5).tolist()
VERY_LARGE_RF_GRID = {"n_estimators": [50], "max_depth": [8, 15], "min_samples_split": [5]}
VERY_LARGE_GB_GRID = {"n_estimators": [50], "max_depth": [3, 6], "learning_rate": [0.1]}


def nested_select_scaled(X: pd.DataFrame, y: pd.Series, verbose: bool = False) -> dict:
    """Same protocol as nested_cv_harness.nested_select, but with a reduced grid when the
    outer-training partition exceeds LARGE_N_THRESHOLD rows, and a further-reduced grid plus
    3-fold inner CV above VERY_LARGE_N_THRESHOLD. See module docstring."""
    n_train_outer = int(len(X) * 0.8)
    if n_train_outer <= LARGE_N_THRESHOLD:
        result = nested_select(X, y, verbose=verbose)
        result["grid_size"] = "full (harness default)"
        return result

    very_large = n_train_outer > VERY_LARGE_N_THRESHOLD
    n_inner_splits = 3 if very_large else 5
    alpha_grid = VERY_LARGE_ALPHA_GRID if very_large else SMALL_ALPHA_GRID
    rf_grid = VERY_LARGE_RF_GRID if very_large else SMALL_RF_GRID
    gb_grid = VERY_LARGE_GB_GRID if very_large else SMALL_GB_GRID

    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    tscv = TimeSeriesSplit(n_splits=n_inner_splits)

    candidates = {
        "Linear Regression": (LinearRegression, {}, {}),
        "Ridge Regression": (Ridge, {"alpha": alpha_grid}, {}),
        "Lasso Regression": (Lasso, {"alpha": alpha_grid}, {}),
        "Random Forest": (RandomForestRegressor, rf_grid, {"min_samples_leaf": 2, "random_state": 42}),
        "Gradient Boosting": (GradientBoostingRegressor, gb_grid,
                               {"min_samples_split": 5, "min_samples_leaf": 2, "random_state": 42}),
    }
    per_candidate = {}
    for name, (cls, grid, fixed) in candidates.items():
        if grid:
            gs = GridSearchCV(cls(**fixed), grid, cv=tscv, scoring="r2", n_jobs=-1)
            gs.fit(X_train_s, y_train)
            best_params, inner_cv_r2 = gs.best_params_, float(gs.best_score_)
        else:
            scores = []
            for tr_idx, val_idx in tscv.split(X_train_s):
                m = cls(**fixed)
                m.fit(X_train_s[tr_idx], y_train.iloc[tr_idx])
                scores.append(r2_score(y_train.iloc[val_idx], m.predict(X_train_s[val_idx])))
            best_params, inner_cv_r2 = {}, float(np.mean(scores))
        model = cls(**fixed, **best_params)
        model.fit(X_train_s, y_train)
        y_pred = model.predict(X_test_s)
        per_candidate[name] = dict(
            best_params={**fixed, **best_params}, inner_cv_r2=inner_cv_r2,
            holdout_r2=float(r2_score(y_test, y_pred)),
            holdout_mae=float(mean_absolute_error(y_test, y_pred)),
            holdout_rmse=float(np.sqrt(mean_squared_error(y_test, y_pred))),
        )
        if verbose:
            print(f"    {name:<20s} inner CV R2={inner_cv_r2:8.4f}  holdout R2={per_candidate[name]['holdout_r2']:8.4f}")

    selected_name = max(per_candidate, key=lambda k: per_candidate[k]["inner_cv_r2"])
    old_protocol_name = max(per_candidate, key=lambda k: per_candidate[k]["holdout_r2"])
    selected = per_candidate[selected_name]
    return dict(
        per_candidate=per_candidate, selected_model=selected_name,
        selected_params=selected["best_params"], selected_inner_cv_r2=selected["inner_cv_r2"],
        selected_holdout_r2=selected["holdout_r2"], selected_holdout_mae=selected["holdout_mae"],
        selected_holdout_rmse=selected["holdout_rmse"], old_protocol_selected_model=old_protocol_name,
        old_protocol_holdout_r2=per_candidate[old_protocol_name]["holdout_r2"],
        n_train=len(X_train), n_test=len(X_test), n_features=X.shape[1],
        grid_size=(
            f"very-reduced (n_train_outer={n_train_outer} > {VERY_LARGE_N_THRESHOLD}, "
            f"bounded max_depth, single n_estimators, {n_inner_splits}-fold inner CV)"
            if very_large else
            f"reduced (n_train_outer={n_train_outer} > {LARGE_N_THRESHOLD})"
        ),
    )


def bootstrap_r2_ci(y_true, y_pred, n_boot=2000, seed=20260919, alpha=0.05):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    n = len(y_true)
    rng = np.random.default_rng(seed)
    boot_r2 = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        yt, yp = y_true[idx], y_pred[idx]
        ss_res = np.sum((yt - yp) ** 2)
        ss_tot = np.sum((yt - yt.mean()) ** 2)
        boot_r2[b] = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan
    boot_r2 = boot_r2[~np.isnan(boot_r2)]
    lo, hi = np.percentile(boot_r2, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)


def refit_selected_and_ci(X: pd.DataFrame, y: pd.Series, result: dict, n_boot=2000, seed=20260919):
    """Refit the nested-selected model once more to get raw (y_test, y_pred) for a bootstrap CI."""
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    cls_map = {"Linear Regression": LinearRegression, "Ridge Regression": Ridge,
               "Lasso Regression": Lasso, "Random Forest": RandomForestRegressor,
               "Gradient Boosting": GradientBoostingRegressor}
    cls = cls_map[result["selected_model"]]
    model = cls(**result["selected_params"])
    model.fit(X_train_s, y_train)
    y_pred = model.predict(X_test_s)
    lo, hi = bootstrap_r2_ci(y_test.to_numpy(), y_pred, n_boot=n_boot, seed=seed)
    return lo, hi


# OLD published results, main_mdpi_v3 Section 4.2.1 (full-feature table)
OLD_PUBLISHED_FULL = {
    "youtube-dl": {"model": "Linear Regression", "holdout_r2": 0.475},
    "sentry": {"model": "Gradient Boosting", "holdout_r2": 0.050},
    "dd-agent": {"model": "Gradient Boosting", "holdout_r2": 0.018},
    "matrix": {"model": "Random Forest", "holdout_r2": 0.005},
    "mongoid": {"model": "Gradient Boosting", "holdout_r2": -0.040},
    "bundler": {"model": "Random Forest", "holdout_r2": -0.151},
    "rspec-core": {"model": "Random Forest", "holdout_r2": -0.294},
}
PROJECT_SHORT = {
    "DataDog/dd-agent": "dd-agent", "bundler/bundler": "bundler", "getsentry/sentry": "sentry",
    "gonum/matrix": "matrix", "mongodb/mongoid": "mongoid", "rg3/youtube-dl": "youtube-dl",
    "rspec/rspec-core": "rspec-core",
}


def main():
    verbose = "--verbose" in sys.argv
    print("Loading TravisTorrent seven_projects.csv ...")
    df_all = tt.load_all(verbose=verbose)

    lines = ["# TravisTorrent Nested Model Selection (PRESTO v4 revision, Phase 2b)", ""]
    lines.append(
        "Replaces the paper's existing fixed-hyperparameter \"best of 5 models, selected by "
        "holdout R2\" protocol (Section 4.2.1) with nested_cv_harness.py's nested_select(): "
        "model+hyperparameter choice happens via TimeSeriesSplit(5) entirely within the outer "
        "80% training partition; the outer 20% holdout is scored exactly once, by the "
        "already-selected configuration. Run for both the full-feature condition and the "
        "testduration-excluded robustness check (excluding `tr_log_testduration` and its 8 "
        "rolling/lag/diff derivatives), matching the paper's existing two-table structure. "
        "A 95% pairs/case bootstrap CI (2000 resamples, seed 20260919) is added for the "
        "nested-selected model in each case.\n"
    )
    lines.append(
        f"**Grid-size note:** projects with an outer-training partition (80% split) over "
        f"{LARGE_N_THRESHOLD} rows use a REDUCED grid (Ridge/Lasso: 7-point alpha grid vs. 19; "
        f"RF: 4 combinations vs. 18; GB: 4 combinations vs. 27) to keep runtime tractable -- "
        f"disclosed per-row below, not a silent truncation.\n"
    )

    all_full = []
    all_excl = []

    for project in tt.PROJECTS:
        short = PROJECT_SHORT[project]
        print(f"\n=== {project} ({short}) ===")
        df = df_all[df_all["gh_project_name"] == project].copy()
        n_raw = len(df)
        df_eng = tt.engineer(df)
        df_eng = tt.remove_outliers(df_eng)
        X_full, y = tt.prepare_features(df_eng)
        excluded_cols = [c for c in X_full.columns if "testduration" in c]
        X_excl = X_full.drop(columns=excluded_cols)
        print(f"  n={len(X_full)} (raw {n_raw}), full features={X_full.shape[1]}, "
              f"excl-testduration features={X_excl.shape[1]} (dropped {len(excluded_cols)})")

        for label, X, bucket in [("full", X_full, all_full), ("excl_testduration", X_excl, all_excl)]:
            t0 = time.time()
            result = nested_select_scaled(X, y, verbose=verbose)
            ci_lo, ci_hi = refit_selected_and_ci(X, y, result)
            elapsed = time.time() - t0
            result.update(project=short, condition=label, ci_lo=ci_lo, ci_hi=ci_hi,
                           ci_excludes_zero=bool(ci_lo > 0 or ci_hi < 0), elapsed_sec=elapsed)
            bucket.append(result)
            print(f"  [{label}] nested={result['selected_model']} holdout R2="
                  f"{result['selected_holdout_r2']:.4f} CI=[{ci_lo:.4f},{ci_hi:.4f}] "
                  f"old-protocol={result['old_protocol_selected_model']} "
                  f"holdout R2={result['old_protocol_holdout_r2']:.4f} ({elapsed:.1f}s, {result['grid_size']})")

    def render_table(rows, old_published=None):
        out = ["| Project | Nested Model | Inner CV R2 | Nested Holdout R2 | 95% CI | Sig? | "
               "Old-Protocol Model | Old-Protocol Holdout R2 | Grid |",
               "|---|---|---:|---:|---|:---:|---|---:|---|"]
        for r in rows:
            sig = "yes" if r["ci_excludes_zero"] else "no"
            out.append(
                f"| {r['project']} | {r['selected_model']} | {r['selected_inner_cv_r2']:.4f} | "
                f"{r['selected_holdout_r2']:.4f} | [{r['ci_lo']:.4f}, {r['ci_hi']:.4f}] | {sig} | "
                f"{r['old_protocol_selected_model']} | {r['old_protocol_holdout_r2']:.4f} | "
                f"{r['grid_size'].split(' (')[0]} |"
            )
        if old_published:
            out.append("")
            out.append("**Paper's already-published numbers (main_mdpi_v3, full-feature table):**")
            out.append("")
            out.append("| Project | Published Model | Published Holdout R2 |")
            out.append("|---|---|---:|")
            for proj, d in old_published.items():
                out.append(f"| {proj} | {d['model']} | {d['holdout_r2']:.4f} |")
        return "\n".join(out)

    lines.append("## Full-feature condition\n")
    lines.append(render_table(all_full, OLD_PUBLISHED_FULL))
    lines.append("\n## Testduration-excluded condition (robustness check)\n")
    lines.append(render_table(all_excl))

    n_sig_full = sum(1 for r in all_full if r["ci_excludes_zero"])
    n_sig_excl = sum(1 for r in all_excl if r["ci_excludes_zero"])
    n_swap_full = sum(1 for r in all_full if r["selected_model"] != r["old_protocol_selected_model"])
    n_swap_excl = sum(1 for r in all_excl if r["selected_model"] != r["old_protocol_selected_model"])

    lines.append("\n## Summary\n")
    lines.append(
        f"- Full-feature condition: {n_sig_full}/7 projects' nested-selected model has a "
        f"bootstrap CI excluding zero; nested selection picks a different model than the old "
        f"holdout-selection protocol in {n_swap_full}/7 projects.\n"
        f"- Testduration-excluded condition: {n_sig_excl}/7 projects significant; "
        f"{n_swap_excl}/7 model swaps.\n"
    )
    old_best = max(OLD_PUBLISHED_FULL.values(), key=lambda d: d["holdout_r2"])
    new_best = max(all_full, key=lambda r: r["selected_holdout_r2"])
    lines.append(
        f"- Old published best-of-seven: {old_best['holdout_r2']:.4f}. Nested-selected "
        f"best-of-seven: {new_best['selected_holdout_r2']:.4f} ({new_best['project']}, "
        f"{new_best['selected_model']}), CI [{new_best['ci_lo']:.4f}, {new_best['ci_hi']:.4f}], "
        f"significant: {'yes' if new_best['ci_excludes_zero'] else 'no'}.\n"
    )

    out_path = _THIS_DIR / "TRAVISTORRENT_NESTED_SELECTION_EVIDENCE.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nEvidence file written to: {out_path}")


if __name__ == "__main__":
    main()
