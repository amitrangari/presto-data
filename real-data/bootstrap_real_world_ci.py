#!/usr/bin/env python3
"""Bootstrap 95% CIs on real-world validation R^2 -- extends R1's synthetic-domain
bootstrap machinery (code/synthetic_data_generator/r1_analysis.py) to the four
real-world datasets, per the 2026-08-13 consensus review's Priority 1 finding:
all four review streams (IEEE, MDPI, ESE, ARS) independently converged on the
same gap -- the real-world results now carrying the paper's central "confirm"
claim have no CI, no significance measure, unlike the synthetic domains, which
were demoted specifically because their CIs showed most estimates could not be
distinguished from zero. This script closes that gap using the *exact* bootstrap
procedure already used for the synthetic domains (pairs/case bootstrap on the
holdout (y_true, y_pred) pairs, 2000 resamples, same seed), applied here to:

  - GHALogs (cross-sectional, n=28,443)
  - SQuaD defect-fix rate (cross-sectional, n=408)
  - SQuaD CVE-count (cross-sectional, n=408)
  - TravisTorrent (within-project temporal, 7 projects)
  - Mozilla Perfherder (within-signature temporal, 3 signatures, with-AR and
    alert-history-only conditions)

Each dataset's own load/prepare functions are imported directly from its
existing pipeline script (not reimplemented) to guarantee the bootstrapped
predictions come from the identical feature set and preprocessing already
reported in the manuscript. Only the final fit+predict+bootstrap step is new.

Usage: python bootstrap_real_world_ci.py [--n-boot 2000] [--seed 20260810]
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler

REAL_DATA_DIR = Path(__file__).resolve().parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def bootstrap_r2_ci(
    y_true: np.ndarray, y_pred: np.ndarray, n_boot: int, seed: int, alpha: float = 0.05
) -> Tuple[float, float, float]:
    """Identical procedure to r1_analysis.py's bootstrap_r2_ci: pairs/case
    bootstrap, fitted model held fixed, resamples (y_true_i, y_pred_i) pairs."""
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
    return float(lo), float(hi), float(np.median(boot_r2))


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


def fit_and_predict_holdout(X: pd.DataFrame, y: pd.Series) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    """Same 80/20 split (row order) + StandardScaler + 5-model set every real-data
    pipeline script in this repo already uses. Returns raw (y_test, y_pred) pairs."""
    n = len(X)
    split = int(n * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    out = {}
    for name, model in build_models().items():
        model.fit(X_train_s, y_train)
        y_pred = model.predict(X_test_s)
        out[name] = (y_test.to_numpy(), y_pred)
    return out


def evaluate_with_ci(X: pd.DataFrame, y: pd.Series, n_boot: int, seed: int) -> List[dict]:
    preds = fit_and_predict_holdout(X, y)
    rows = []
    for model_name, (y_test, y_pred) in preds.items():
        point_r2 = float(r2_score(y_test, y_pred))
        lo, hi, boot_median = bootstrap_r2_ci(y_test, y_pred, n_boot=n_boot, seed=seed)
        rows.append(dict(
            model=model_name, n_holdout=len(y_test), holdout_r2=point_r2,
            ci_lo=lo, ci_hi=hi, boot_median=boot_median,
            ci_excludes_zero=bool(lo > 0 or hi < 0),
        ))
    return rows


def fmt_row(r: dict) -> str:
    sig = "yes" if r["ci_excludes_zero"] else "no"
    return f"| {r['model']} | {r['holdout_r2']:.4f} | [{r['ci_lo']:.4f}, {r['ci_hi']:.4f}] | {sig} |"


def run_ghalogs(n_boot: int, seed: int) -> Tuple[str, List[dict]]:
    mod = load_module("ghalogs_pipeline", REAL_DATA_DIR / "ghalogs" / "run_pipeline_ghalogs.py")
    run_agg = mod.load_repo_aggregates(verbose=False)
    repo_meta = mod.load_repo_metadata(verbose=False)
    merged = run_agg.merge(repo_meta, on="repository_name", how="inner")
    merged = mod.engineer(merged)
    merged = merged.dropna(subset=["mean_total_time"])
    merged = merged.sort_values("pushedAt")  # chronological split, matching run_pipeline_ghalogs.py's main()
    X, y = mod.prepare_features(merged)
    return "GHALogs (mean CI run duration, n=%d)" % len(X), evaluate_with_ci(X, y, n_boot, seed)


def run_squad_defect(n_boot: int, seed: int) -> Tuple[str, List[dict]]:
    mod = load_module("squad_pipeline", REAL_DATA_DIR / "squad" / "run_pipeline_squad.py")
    agg = mod.load_and_aggregate(verbose=False)
    X, y = mod.prepare_features(agg)
    return "SQuaD defect-fix rate (n=%d)" % len(X), evaluate_with_ci(X, y, n_boot, seed)


def run_squad_vuln(n_boot: int, seed: int) -> Tuple[str, List[dict]]:
    mod = load_module("squad_vuln_pipeline", REAL_DATA_DIR / "squad" / "run_pipeline_squad_vuln.py")
    agg = mod.load_and_aggregate(verbose=False)
    X, y = mod.prepare_features(agg)
    return "SQuaD CVE-count, log1p (n=%d)" % len(X), evaluate_with_ci(X, y, n_boot, seed)


def run_travistorrent(n_boot: int, seed: int) -> List[Tuple[str, List[dict]]]:
    mod = load_module("travistorrent_pipeline", REAL_DATA_DIR / "travistorrent" / "run_pipeline_travistorrent.py")
    df_all = mod.load_all(verbose=False)
    results = []
    for project in sorted(df_all["gh_project_name"].unique()):
        df_p = df_all[df_all["gh_project_name"] == project].copy()
        df_p = mod.engineer(df_p)
        df_p = mod.remove_outliers(df_p)
        X, y = mod.prepare_features(df_p)
        if len(X) < 20:
            continue
        label = f"TravisTorrent {project} (n={len(X)})"
        results.append((label, evaluate_with_ci(X, y, n_boot, seed)))
    return results


def run_perfherder(n_boot: int, seed: int) -> List[Tuple[str, List[dict]]]:
    mod = load_module("perfherder_pipeline", REAL_DATA_DIR / "mozilla-perfherder" / "run_pipeline_perfherder.py")
    alerts_lookup = mod.load_alerts_lookup(REAL_DATA_DIR / "mozilla-perfherder" / "alerts_data.csv")
    results = []
    for name, spec in mod.SIGNATURES.items():
        path = REAL_DATA_DIR / "mozilla-perfherder" / spec["path"]
        if not path.exists():
            found = mod.find_signature_file(spec["id"])
            if found is None:
                continue
            path = found
        df = mod.load_signature_series(path, spec["id"], alerts_lookup, verbose=False)
        df_eng = mod.engineer_features(df, verbose=False)
        X_with, y, _ = mod.prepare_features(df_eng, exclude_target_derived=False)
        label = f"Perfherder {name}, with-AR (n={len(X_with)})"
        results.append((label, evaluate_with_ci(X_with, y, n_boot, seed)))
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-boot", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260810)
    parser.add_argument("--only", choices=["fast", "slow", "all"], default="all",
                         help="fast=GHALogs+SQuaD(x2); slow=TravisTorrent+Perfherder; all=everything")
    args = parser.parse_args()

    out_path = REAL_DATA_DIR / f"REAL_WORLD_BOOTSTRAP_CI_EVIDENCE_{args.only}.md"
    report_lines = [
        "# Real-World Bootstrap Confidence Intervals",
        "",
        "Extends `code/synthetic_data_generator/r1_analysis.py`'s bootstrap-CI procedure "
        "(pairs/case bootstrap on the holdout (y_true, y_pred) pairs, "
        f"{args.n_boot} resamples, seed {args.seed}, fitted model held fixed) to the four "
        "real-world validation datasets, per the 2026-08-13 consensus review's Priority 1 "
        "finding. Same method, same seed, same resample count as the synthetic-domain analysis "
        "for direct comparability.",
        "",
    ]
    out_path.write_text("\n".join(report_lines))

    def emit(label: str, rows: List[dict]):
        lines = [f"## {label}", "", "| Model | Holdout R2 | 95% CI | Excludes zero |", "|---|---|---|---|"]
        for r in sorted(rows, key=lambda r: -r["holdout_r2"]):
            lines.append(fmt_row(r))
        lines.append("")
        report_lines.extend(lines)
        out_path.write_text("\n".join(report_lines))
        best = max(rows, key=lambda r: r["holdout_r2"])
        print(f"{label}: best={best['model']} R2={best['holdout_r2']:.4f} "
              f"CI=[{best['ci_lo']:.4f}, {best['ci_hi']:.4f}] excl_zero={best['ci_excludes_zero']}",
              flush=True)

    if args.only in ("fast", "all"):
        print("Running GHALogs...", flush=True)
        emit(*run_ghalogs(args.n_boot, args.seed))

        print("Running SQuaD defect-fix...", flush=True)
        emit(*run_squad_defect(args.n_boot, args.seed))

        print("Running SQuaD CVE-count...", flush=True)
        emit(*run_squad_vuln(args.n_boot, args.seed))

    if args.only in ("slow", "all"):
        print("Running Perfherder (3 signatures, with-AR)...", flush=True)
        for label, rows in run_perfherder(args.n_boot, args.seed):
            emit(label, rows)

        print("Running TravisTorrent (7 projects)...", flush=True)
        for label, rows in run_travistorrent(args.n_boot, args.seed):
            emit(label, rows)

    print(f"\nReport written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
