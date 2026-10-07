#!/usr/bin/env python3
"""GHALogs mean_n_steps ablation (PRESTO v4 revision, Reviewer 2 comment).

Reviewer 2 (MDPI round-3 review) flagged that GHALogs' top Random Forest feature,
mean_n_steps (48.6% importance in the full-feature result reported in the paper),
is largely definitional: workflows with more steps mechanically take longer, the
same circularity mechanism already conceded for TravisTorrent's tr_log_testduration
(see travistorrent_feature_importance_excl_testduration.py). This script reruns the
GHALogs cross-sectional validation with mean_n_steps removed, holding every other
part of run_pipeline_ghalogs.py's pipeline (chronological 80/20 split, TimeSeriesSplit
CV, StandardScaler fit on train only, same 5 models) fixed, and adds a pairs/case
bootstrap 95% CI (2000 resamples, identical procedure to bootstrap_real_world_ci.py)
so the ablated result is directly comparable to the paper's existing GHALogs table.

Usage: python run_pipeline_ghalogs_ablation.py --verbose
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent

# fields that are mechanically/arithmetically entangled with the duration target
# (mean_total_time is already excluded as the target itself; mean_build_time /
# mean_test_time / mean_setup_time are already excluded upstream in
# run_pipeline_ghalogs.py's prepare_features(). mean_n_steps is the one duration-
# adjacent field that DOES currently enter the feature matrix.)
CIRCULAR_FEATURES = ["mean_n_steps"]


def load_base_module():
    spec = importlib.util.spec_from_file_location(
        "ghalogs_pipeline", SCRIPT_DIR / "run_pipeline_ghalogs.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["ghalogs_pipeline"] = mod
    spec.loader.exec_module(mod)
    return mod


def bootstrap_r2_ci(y_true, y_pred, n_boot=2000, seed=20260919, alpha=0.05):
    """Identical pairs/case bootstrap procedure used throughout this repo
    (r1_analysis.py, bootstrap_real_world_ci.py)."""
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


def train_and_evaluate(X: pd.DataFrame, y: pd.Series, n_boot: int, seed: int):
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
        ci_lo, ci_hi = bootstrap_r2_ci(y_test.to_numpy(), pred_test, n_boot=n_boot, seed=seed)
        results.append({
            "name": name,
            "cv_r2_mean": float(np.mean(cv_scores)),
            "cv_r2_std": float(np.std(cv_scores)),
            "holdout_r2": float(r2_score(y_test, pred_test)),
            "holdout_mae": float(mean_absolute_error(y_test, pred_test)),
            "holdout_rmse": float(np.sqrt(mean_squared_error(y_test, pred_test))),
            "ci_lo": ci_lo, "ci_hi": ci_hi,
            "ci_excludes_zero": bool(ci_lo > 0 or ci_hi < 0),
        })
    return results, X_train.columns.tolist()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20260919)
    args = ap.parse_args()

    mod = load_base_module()
    run_agg = mod.load_repo_aggregates(verbose=args.verbose)
    repo_meta = mod.load_repo_metadata(verbose=args.verbose)
    merged = run_agg.merge(repo_meta, on="repository_name", how="inner")
    merged = mod.engineer(merged)
    merged = merged.dropna(subset=["mean_total_time"])
    merged = merged.sort_values("pushedAt")

    X_full, y = mod.prepare_features(merged)
    dropped = [c for c in CIRCULAR_FEATURES if c in X_full.columns]
    X_ablated = X_full.drop(columns=dropped)
    print(f"Full feature set: {X_full.shape[1]} features. Dropping: {dropped}. "
          f"Ablated feature set: {X_ablated.shape[1]} features. n={len(X_ablated)}")

    results, feature_names = train_and_evaluate(X_ablated, y, args.n_boot, args.seed)
    print("\n--- Ablated model performance (mean_n_steps excluded) ---")
    for r in sorted(results, key=lambda r: -r["holdout_r2"]):
        sig = "yes" if r["ci_excludes_zero"] else "no"
        print(f"  {r['name']:20s} Holdout R2={r['holdout_r2']:.4f}  95% CI=[{r['ci_lo']:.4f}, {r['ci_hi']:.4f}]  "
              f"sig={sig}  MAE={r['holdout_mae']:.2f}  RMSE={r['holdout_rmse']:.2f}")

    # feature importance via Random Forest, ablated feature set
    rf = RandomForestRegressor(n_estimators=100, max_depth=10, min_samples_split=5,
                                min_samples_leaf=2, random_state=42)
    scaler = StandardScaler()
    n = len(X_ablated)
    split = int(n * 0.8)
    X_train_s = scaler.fit_transform(X_ablated.iloc[:split])
    rf.fit(X_train_s, y.iloc[:split])
    importances = sorted(zip(feature_names, rf.feature_importances_), key=lambda t: -t[1])[:15]

    out_path = SCRIPT_DIR.parent.parent / "code" / "synthetic_data_generator" / "GHALOGS_ABLATION_EVIDENCE.md"
    with open(out_path, "w") as f:
        f.write("# GHALogs mean_n_steps Ablation (PRESTO v4 revision)\n\n")
        f.write("**Reviewer comment addressed:** MDPI round-3 review, Reviewer 2: \"the most influential "
                "feature is mean_n_steps, accounting for approximately 48.6% of Random Forest importance, "
                "... largely definitional ... analogous to the circularity problem subsequently identified "
                "for TravisTorrent.\"\n\n")
        f.write("**Method.** Identical pipeline to `real-data/ghalogs/run_pipeline_ghalogs.py` "
                "(chronological 80/20 split, TimeSeriesSplit(5) CV, StandardScaler fit on train only, "
                "same 5 models), with `mean_n_steps` removed from the feature matrix before fitting. "
                "A pairs/case bootstrap 95% CI (2000 resamples, seed 20260919) was added, matching the "
                "procedure already used in `bootstrap_real_world_ci.py` for the full-feature GHALogs result, "
                "so the two tables are directly comparable.\n\n")
        f.write(f"Full feature set: {X_full.shape[1]} features. Ablated: {X_ablated.shape[1]} "
                f"(dropped: {', '.join(dropped)}). n={len(X_ablated)} repositories (unchanged from "
                "the full-feature result).\n\n")
        f.write("## Ablated Model Performance (mean_n_steps excluded)\n\n")
        f.write("| Model | CV R2 (mean +/- std) | Holdout R2 | 95% Bootstrap CI | Significant? | MAE | RMSE |\n")
        f.write("|---|---|---|---|:---:|---|---|\n")
        for r in sorted(results, key=lambda r: -r["holdout_r2"]):
            sig = "yes" if r["ci_excludes_zero"] else "no"
            f.write(f"| {r['name']} | {r['cv_r2_mean']:.4f} +/- {r['cv_r2_std']:.4f} | "
                    f"{r['holdout_r2']:.4f} | [{r['ci_lo']:.4f}, {r['ci_hi']:.4f}] | {sig} | "
                    f"{r['holdout_mae']:.2f} | {r['holdout_rmse']:.2f} |\n")
        f.write("\n## Full-Feature Result, For Comparison (from output_ghalogs_ml_results.md)\n\n")
        f.write("| Model | Holdout R2 | 95% Bootstrap CI (paper Table, Sec 4.2.3) |\n|---|---|---|\n")
        f.write("| Gradient Boosting | 0.1130 | [0.050, 0.356] |\n")
        f.write("| Lasso Regression | 0.1000 | [0.062, 0.267] |\n")
        f.write("| Ridge Regression | 0.1000 | [0.062, 0.267] |\n")
        f.write("| Linear Regression | 0.1000 | [0.062, 0.267] |\n")
        f.write("| Random Forest | 0.0960 | [0.021, 0.299] |\n")
        f.write("\n## Top 15 Feature Importances After Ablation (Random Forest)\n\n")
        f.write("| Rank | Feature | Importance |\n|---|---|---|\n")
        for i, (name, imp) in enumerate(importances, 1):
            f.write(f"| {i} | {name} | {imp:.4f} |\n")
        f.write("\n## Interpretation\n\n")
        best = max(results, key=lambda r: r["holdout_r2"])
        f.write(f"With `mean_n_steps` removed, the best model's holdout R2 is {best['holdout_r2']:.4f} "
                f"({best['name']}), versus {0.1130 if best['name']=='Gradient Boosting' else 0.1000:.4f} "
                "in the full-feature result. [FILL IN: state plainly whether the ablated CI still excludes "
                "zero for at least one model, i.e. whether GHALogs' significance claim survives removing "
                "the definitionally-circular feature, and update the paper's Section 4.2.3 'cleanest real-data "
                "test' framing accordingly -- this is the load-bearing sentence for the manuscript text.]\n")
    print(f"\nEvidence file written to: {out_path}")


if __name__ == "__main__":
    main()
