#!/usr/bin/env python3
"""Phase-Aware Recursive Feature Elimination (PA-RFE) -- R7/R4 reimplementation.

The paper's PA-RFE numbers (Table `parfe_comparison`, Figures 9/10) were carried over from the
original submission with no implementation in the deposited reproducibility package -- confirmed
missing by an exhaustive search of this machine (see STATUS.md, R7). This script implements PA-RFE
faithfully from the algorithm pseudocode in `paper-work/overleaf/main.md` (Stage 6 / Algorithm
alg:parfe) and reruns it against the corrected (post-R2-fix) synthetic data, so the reported numbers
are backed by actual, deposited, runnable code.

Algorithm (verbatim from the paper):
    Require: feature matrix X, target y, phase map phi: feature -> phase, k_min per phase, step s
    F <- all features
    while |F| > k_min * |phases| do
        train Gradient Boosting on X_train[F]
        pi <- PermutationImportance(model, X_val[F], n_repeats=10)
        record (|F|, R2_val)
        sort F by pi ascending; build elimination batch E of up to s features,
            skipping any feature whose removal would leave its phase below k_min
        if E empty: break
        F <- F minus E
    F* <- argmax over recorded (|F|, R2_val)

k_min = 2 per SDLC phase (8 phases -> floor 16), step s = 5. quality_score/stability_score form a
virtual 9th "cross_phase" group with k_min = 0 (freely eliminable). 60/20/20 temporal train/val/test
split; validation R2 selects F*, test R2 (evaluated once) is the reported metric.

Runs PA-RFE plus two comparison baselines (standard/phase-agnostic RFE, SelectKBest) targeting the
same final feature count as PA-RFE, across all three synthetic domains.

Usage: python pa_rfe.py [--domain abc-cloud-provider] [--verbose]
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.feature_selection import RFE, SelectKBest, f_regression
from sklearn.inspection import permutation_importance
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import run_pipeline as pipe  # noqa: E402  (reuse load_and_merge / engineer_features / prepare_features)

CANONICAL_DATA_DIR = Path("/Volumes/4TB/research-data/presto/synthetic-data-projects")
ALL_DOMAINS = ["abc-cloud-provider", "card-payment-processor", "xyz-sales-force"]

PHASE_ORDER = [
    "production_run_metrics", "build_metrics", "code_metrics", "test_metrics",
    "performance_testing_metrics", "chaos_testing_metrics", "requirements_metrics", "uat_metrics",
]
PHASE_LABELS = {
    "production_run_metrics": "Production", "build_metrics": "Build", "code_metrics": "Code",
    "test_metrics": "Test", "performance_testing_metrics": "Performance Test",
    "chaos_testing_metrics": "Chaos", "requirements_metrics": "Requirements", "uat_metrics": "UAT",
}
CROSS_PHASE_FEATURES = {"quality_score", "stability_score"}
K_MIN = 2
STEP = 5
N_REPEATS = 10
RANDOM_STATE = 42


# ---------------------------------------------------------------------------
# Phase mapping
# ---------------------------------------------------------------------------
def _phase_headers(domain_dir: Path) -> Dict[str, set]:
    headers = {}
    for stem in PHASE_ORDER:
        df = pd.read_csv(domain_dir / f"{stem}.csv", nrows=0)
        headers[stem] = {c for c in df.columns if c not in ("Date", "Release Number")}
    return headers


def _base_column_phase(col: str, headers: Dict[str, set]) -> Optional[str]:
    for stem in PHASE_ORDER:
        if col in headers[stem]:
            return stem
    return None


def _resolve_merged_column_phase(col: str, headers: Dict[str, set]) -> Optional[str]:
    for stem in PHASE_ORDER:
        suffix = f"_{stem}"
        if col.endswith(suffix) and col[: -len(suffix)] in headers[stem]:
            return stem
    return _base_column_phase(col, headers)


def build_feature_phase_map(feature_cols: List[str], domain_dir: Path) -> Dict[str, str]:
    """Map every engineered feature name to a phase label (or 'cross_phase')."""
    headers = _phase_headers(domain_dir)
    phase_map: Dict[str, str] = {}
    for col in feature_cols:
        if col in CROSS_PHASE_FEATURES:
            phase_map[col] = "cross_phase"
            continue
        # Derived features: strip known suffixes to find the parent metric name.
        base = col
        for marker in ("_rolling_mean_", "_rolling_std_", "_rolling_min_", "_rolling_max_",
                        "_rolling_cv_", "_lag_", "_pct_change_", "_diff_"):
            idx = col.find(marker)
            if idx != -1:
                base = col[:idx]
                break
        stem = _resolve_merged_column_phase(base, headers)
        if stem is None:
            # Fallback: try the full column name directly (shouldn't normally trigger).
            stem = _resolve_merged_column_phase(col, headers)
        phase_map[col] = PHASE_LABELS.get(stem, "Unknown") if stem else "Unknown"
    return phase_map


# ---------------------------------------------------------------------------
# Data loading (reuses run_pipeline's exact merge/engineer/prepare logic)
# ---------------------------------------------------------------------------
def load_domain(domain_dir: Path):
    merged = pipe.load_and_merge(domain_dir)
    engineered = pipe.engineer_features(merged)
    X, y, leakage_cols = pipe.prepare_features(engineered, exclude_leakage=True)
    phase_map = build_feature_phase_map(list(X.columns), domain_dir)
    return X, y, phase_map


def three_way_split(X: pd.DataFrame, y: pd.Series):
    n = len(X)
    train_end = int(n * 0.6)
    val_end = int(n * 0.8)
    return (
        X.iloc[:train_end], y.iloc[:train_end],
        X.iloc[train_end:val_end], y.iloc[train_end:val_end],
        X.iloc[val_end:], y.iloc[val_end:],
    )


def gb_model() -> GradientBoostingRegressor:
    return GradientBoostingRegressor(
        n_estimators=100, max_depth=6, learning_rate=0.1,
        min_samples_split=5, min_samples_leaf=2, random_state=RANDOM_STATE,
    )


# ---------------------------------------------------------------------------
# PA-RFE
# ---------------------------------------------------------------------------
def pa_rfe(
    X_train, y_train, X_val, y_val, phase_map: Dict[str, str], verbose: bool = False
) -> Tuple[List[str], List[Tuple[int, float]], Dict[str, float]]:
    phases = sorted(set(phase_map.values()))
    k_min_of = {p: (0 if p == "cross_phase" else K_MIN) for p in phases}
    floor = sum(k_min_of.values())

    F = list(X_train.columns)
    curve: List[Tuple[int, float]] = []
    per_feature_importance_at_optimum: Dict[str, float] = {}
    scaler_cache = {}

    def fit_eval(features: List[str]):
        scaler = StandardScaler()
        Xtr = scaler.fit_transform(X_train[features])
        Xv = scaler.transform(X_val[features])
        model = gb_model()
        model.fit(Xtr, y_train)
        r2 = r2_score(y_val, model.predict(Xv))
        return model, scaler, r2

    best_r2 = -np.inf
    best_F: List[str] = list(F)

    while len(F) > floor:
        model, scaler, r2_val = fit_eval(F)
        curve.append((len(F), r2_val))
        if verbose:
            print(f"    |F|={len(F):3d}  val R2={r2_val:.4f}")
        if r2_val > best_r2:
            best_r2 = r2_val
            best_F = list(F)
            Xv_s = scaler.transform(X_val[F])
            pi_at_best = permutation_importance(
                model, Xv_s, y_val, n_repeats=N_REPEATS, random_state=RANDOM_STATE
            )
            per_feature_importance_at_optimum = dict(zip(F, pi_at_best.importances_mean))

        Xv_s = scaler.transform(X_val[F])
        pi = permutation_importance(
            model, Xv_s, y_val, n_repeats=N_REPEATS, random_state=RANDOM_STATE
        )
        importances = dict(zip(F, pi.importances_mean))
        F_sorted = sorted(F, key=lambda f: importances[f])  # ascending: least important first

        remaining = set(F)
        E: List[str] = []
        for f in F_sorted:
            if len(E) >= STEP:
                break
            phase = phase_map[f]
            same_phase_remaining = sum(
                1 for g in remaining if g not in E and phase_map[g] == phase
            )
            if same_phase_remaining > k_min_of[phase]:
                E.append(f)
        if not E:
            break
        F = [f for f in F if f not in E]

    # Final check at the floor (loop may exit without evaluating the floor-sized F).
    if len(F) <= floor and (not curve or curve[-1][0] != len(F)):
        model, scaler, r2_val = fit_eval(F)
        curve.append((len(F), r2_val))
        if r2_val > best_r2:
            best_r2 = r2_val
            best_F = list(F)
            Xv_s = scaler.transform(X_val[F])
            pi_at_best = permutation_importance(
                model, Xv_s, y_val, n_repeats=N_REPEATS, random_state=RANDOM_STATE
            )
            per_feature_importance_at_optimum = dict(zip(F, pi_at_best.importances_mean))

    return best_F, curve, per_feature_importance_at_optimum


def evaluate_on_test(features: List[str], X_train, y_train, X_test, y_test) -> float:
    scaler = StandardScaler()
    Xtr = scaler.fit_transform(X_train[features])
    Xte = scaler.transform(X_test[features])
    model = gb_model()
    model.fit(Xtr, y_train)
    return float(r2_score(y_test, model.predict(Xte)))


# ---------------------------------------------------------------------------
# Comparison baselines, targeting PA-RFE's final feature count
# ---------------------------------------------------------------------------
def standard_rfe(X_train, y_train, n_features_target: int) -> List[str]:
    scaler = StandardScaler()
    Xtr = scaler.fit_transform(X_train)
    selector = RFE(
        estimator=gb_model(), n_features_to_select=n_features_target, step=STEP,
    )
    selector.fit(Xtr, y_train)
    return list(X_train.columns[selector.support_])


def select_k_best(X_train, y_train, n_features_target: int) -> List[str]:
    scaler = StandardScaler()
    Xtr = scaler.fit_transform(X_train)
    selector = SelectKBest(score_func=f_regression, k=n_features_target)
    selector.fit(Xtr, y_train)
    return list(X_train.columns[selector.get_support()])


# ---------------------------------------------------------------------------
# Per-domain run
# ---------------------------------------------------------------------------
def run_domain(domain: str, verbose: bool = False) -> dict:
    domain_dir = CANONICAL_DATA_DIR / domain
    X, y, phase_map = load_domain(domain_dir)
    X_train, y_train, X_val, y_val, X_test, y_test = three_way_split(X, y)

    if verbose:
        print(f"  {domain}: {len(X)} rows, {X.shape[1]} features "
              f"(train={len(X_train)}, val={len(X_val)}, test={len(X_test)})")

    F_star, curve, importances_at_opt = pa_rfe(X_train, y_train, X_val, y_val, phase_map, verbose)
    parfe_test_r2 = evaluate_on_test(F_star, X_train, y_train, X_test, y_test)

    n_target = len(F_star)
    rfe_features = standard_rfe(X_train, y_train, n_target)
    rfe_test_r2 = evaluate_on_test(rfe_features, X_train, y_train, X_test, y_test)

    skb_features = select_k_best(X_train, y_train, n_target)
    skb_test_r2 = evaluate_on_test(skb_features, X_train, y_train, X_test, y_test)

    # Phase contribution at the optimal PA-RFE subset (sum of permutation importances by phase,
    # renormalized to percent of total).
    phase_totals: Dict[str, float] = {}
    for feat, imp in importances_at_opt.items():
        phase = phase_map[feat]
        phase_totals[phase] = phase_totals.get(phase, 0.0) + max(imp, 0.0)
    total = sum(phase_totals.values()) or 1.0
    phase_pct = {p: 100.0 * v / total for p, v in sorted(phase_totals.items(), key=lambda kv: -kv[1])}

    best_val_r2 = max(r2 for _, r2 in curve)

    return {
        "domain": domain,
        "n_total_features": X.shape[1],
        "n_selected": n_target,
        "parfe_val_r2_best": best_val_r2,
        "parfe_test_r2": parfe_test_r2,
        "rfe_test_r2": rfe_test_r2,
        "skb_test_r2": skb_test_r2,
        "ablation_curve": curve,
        "phase_pct_at_optimum": phase_pct,
        "phases_represented": len(phase_pct),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", choices=ALL_DOMAINS, default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    domains = [args.domain] if args.domain else ALL_DOMAINS
    all_results = []
    for domain in domains:
        print(f"=== {domain} ===")
        result = run_domain(domain, verbose=args.verbose)
        all_results.append(result)
        print(f"  {result['n_total_features']} -> {result['n_selected']} features")
        print(f"  PA-RFE  test R2 = {result['parfe_test_r2']:.3f}  (val R2 best = {result['parfe_val_r2_best']:.3f})")
        print(f"  Std RFE test R2 = {result['rfe_test_r2']:.3f}")
        print(f"  SKBest  test R2 = {result['skb_test_r2']:.3f}")
        print(f"  Phases represented at optimum: {result['phases_represented']} / "
              f"{len(PHASE_LABELS) + 1}")

    # ---- Write report ----
    report_path = SCRIPT_DIR / "PA_RFE_REIMPLEMENTATION_RESULTS.md"
    with open(report_path, "w") as f:
        f.write("# PA-RFE reimplementation results (R4/R7)\n\n")
        f.write(
            "**Date:** 2026-08-11  \n"
            "**Item:** ACTION_PLAN.md R4/R7 -- PA-RFE had no implementation anywhere in the "
            "deposited reproducibility package (confirmed by exhaustive search, see STATUS.md); "
            "these numbers are reimplemented from the algorithm pseudocode in "
            "`paper-work/overleaf/main.md` (Stage 6 / Algorithm alg:parfe) and rerun against the "
            "corrected (post-R2-fix) synthetic data. They supersede the unverified, "
            "carried-over-from-original-submission numbers previously in the paper.\n\n"
        )
        f.write(
            "**Method:** k_min=2 per SDLC phase (8 phases, floor 16), step s=5, Gradient Boosting, "
            "permutation importance (n_repeats=10) on a held-out validation split, 60/20/20 "
            "train/validation/test temporal split. `quality_score`/`stability_score` form a virtual "
            "cross-phase group with k_min=0. Standard RFE and SelectKBest baselines target the same "
            "final feature count PA-RFE converges to, for a fair comparison.\n\n"
        )
        f.write("## Comparison table (test R^2, evaluated once)\n\n")
        f.write("| Domain | Features | PA-RFE | Std RFE | SelectKBest |\n")
        f.write("|---|---|---:|---:|---:|\n")
        for r in all_results:
            f.write(
                f"| {r['domain']} | {r['n_total_features']}->{r['n_selected']} | "
                f"{r['parfe_test_r2']:.3f} | {r['rfe_test_r2']:.3f} | {r['skb_test_r2']:.3f} |\n"
            )
        f.write("\n## Validation-set ablation curves\n\n")
        for r in all_results:
            f.write(f"### {r['domain']}\n\n")
            f.write("| |F| | Validation R^2 |\n|---:|---:|\n")
            for n_feat, r2 in r["ablation_curve"]:
                f.write(f"| {n_feat} | {r2:.4f} |\n")
            f.write("\n")
        f.write("## Phase contribution at PA-RFE's optimal subset\n\n")
        for r in all_results:
            f.write(f"### {r['domain']} ({r['phases_represented']} phase groups represented)\n\n")
            f.write("| Phase | % of permutation importance |\n|---|---:|\n")
            for phase, pct in r["phase_pct_at_optimum"].items():
                f.write(f"| {phase} | {pct:.1f}% |\n")
            f.write("\n")
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
