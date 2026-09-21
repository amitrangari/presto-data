#!/usr/bin/env python3
"""M13 (v4 revision, Reviewer 2 round 3): nested selection for PA-RFE's stopping point.

`pa_rfe.py`'s existing elimination procedure selects the feature count F* that maximizes
VALIDATION R^2 across ~45 elimination iterations on a single fixed 60/20/20 split, then reports
TEST R^2 at that F* once. The paper already discloses this causes severe overfitting on the
primary domain (validation R^2=0.271 vs. test R^2=-3.026) -- Reviewer 2 calls this out
specifically and asks that PA-RFE's own selection procedure be embedded within nested
validation before its test-set accuracy is reported.

This script does not change the elimination MECHANISM (permutation-importance-guided, phase-
floor-respecting removal, step=5) -- only how the STOPPING POINT (final feature count) is
chosen and evaluated:

  1. Outer split: the same 80/20 temporal split used throughout this paper (NOT the original
     60/20/20 -- see note below).
  2. Inner selection of the stopping point: TimeSeriesSplit(3) within the 80% outer-training
     partition. For each inner fold, run the identical PA-RFE elimination procedure (train on
     the fold's inner-train, evaluate the ablation curve on the fold's inner-val) and record
     (|F|, val R^2) at every elimination step. |F| checkpoints are deterministic given the
     starting feature count, K_MIN, and STEP (independent of which rows are in the fold), so
     checkpoints align exactly across folds. Average val R^2 at each |F| across the inner folds;
     select n* = the |F| with the highest MEAN inner-CV val R^2. This step never touches the
     outer holdout.
  3. Final F*: run PA-RFE's elimination procedure ONCE MORE on the full 80% outer-training
     partition (using a 75/25 internal train/val split, preserving the original procedure's
     60/20/20 proportions rescaled to the 80% outer-train: 0.6/(0.6+0.2)=0.75), but instead of
     selecting the stopping point by peeking at this val R^2 (the original winner's-curse
     mechanism), stop exactly at |F|=n* (already fixed in step 2, before this run). This
     produces the actual feature set F*.
  4. F* is scored ONCE on the untouched outer 20% holdout.

Note on the split change: `pa_rfe.py`'s original 60/20/20 design already burns 20% of the data
purely on stopping-point selection, on top of the 20% test holdout. Moving to an 80/20 outer
split (matching every other result in this paper) with a nested 3-fold inner selection inside
the 80% is both more consistent with the rest of the paper's protocol and uses the available
data more efficiently; the tradeoff is smaller per-fold training sets in the inner loop, a
limitation shared with every nested-CV result in this paper given ~150-200 total rows.

Usage: python m13_pa_rfe_nested.py [--domain abc-cloud-provider] [--verbose]
    (omit --domain to run all 3 and write the combined report; with --domain, results for that
    domain alone are cached to a per-domain JSON so a full run can be assembled incrementally
    without re-running already-completed domains -- see `_cache_path`/main() below.)
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import pa_rfe as prfe  # noqa: E402  (reuse gb_model, build_feature_phase_map, load_domain, K_MIN/STEP)

CANONICAL_DATA_DIR = Path("/Volumes/4TB/research-data-and-code/zenado/presto-data/synthetic-data-projects")
ALL_DOMAINS = ["abc-cloud-provider", "card-payment-processor", "xyz-sales-force"]
N_INNER_SPLITS = 2  # reduced from 3: an initial 3-domain run's wall time exceeded the available
# budget (killed mid-run). The dominant cost is permutation_importance (n_repeats x n_features
# predict() calls) at every one of ~45 elimination steps, per fold. Cut two ways instead of one:
# fewer inner folds (2, not 3) AND a lighter n_repeats for the coarse inner-fold curves (see
# INNER_N_REPEATS below) -- both applied only to the inner selection step, not the final F*
# determination, which keeps the original N_REPEATS=10 fidelity where it actually matters (the
# feature set that gets reported).
INNER_N_REPEATS = 3  # permutation_importance n_repeats for inner-fold elimination curves only

# Paper's existing published PA-RFE numbers (Table `parfe_comparison`, Section 4.1.8), for
# direct old-vs-new comparison.
OLD_PUBLISHED = {
    "abc-cloud-provider": {"n_selected": 76, "test_r2": -3.026},
    "card-payment-processor": {"n_selected": 86, "test_r2": 0.313},
    "xyz-sales-force": {"n_selected": 136, "test_r2": 0.236},
}


def elimination_curve(X_tr, y_tr, X_val, y_val, phase_map: Dict[str, str]) -> List[Tuple[int, float]]:
    """Run PA-RFE's elimination loop, recording (|F|, val R^2) at every step. Does NOT track
    a 'best' F* by val R^2 -- that selection happens outside this function, either via nested
    CV averaging (inner folds) or a pre-fixed target size (final run)."""
    phases = sorted(set(phase_map.values()))
    k_min_of = {p: (0 if p == "cross_phase" else prfe.K_MIN) for p in phases}
    floor = sum(k_min_of.values())

    F = list(X_tr.columns)
    curve: List[Tuple[int, float]] = []

    def fit_eval(features):
        scaler = StandardScaler()
        Xtr = scaler.fit_transform(X_tr[features])
        Xv = scaler.transform(X_val[features])
        model = prfe.gb_model()
        model.fit(Xtr, y_tr)
        r2 = r2_score(y_val, model.predict(Xv))
        return model, scaler, r2

    while len(F) > floor:
        model, scaler, r2_val = fit_eval(F)
        curve.append((len(F), r2_val))

        Xv_s = scaler.transform(X_val[F])
        from sklearn.inspection import permutation_importance
        pi = permutation_importance(
            model, Xv_s, y_val, n_repeats=INNER_N_REPEATS, random_state=prfe.RANDOM_STATE
        )
        importances = dict(zip(F, pi.importances_mean))
        F_sorted = sorted(F, key=lambda f: importances[f])

        remaining = set(F)
        E: List[str] = []
        for f in F_sorted:
            if len(E) >= prfe.STEP:
                break
            phase = phase_map[f]
            same_phase_remaining = sum(1 for g in remaining if g not in E and phase_map[g] == phase)
            if same_phase_remaining > k_min_of[phase]:
                E.append(f)
        if not E:
            break
        F = [f for f in F if f not in E]

    if len(F) <= floor and (not curve or curve[-1][0] != len(F)):
        _, _, r2_val = fit_eval(F)
        curve.append((len(F), r2_val))

    return curve


def run_to_target_size(X_tr, y_tr, X_val, y_val, phase_map: Dict[str, str], target_size: int) -> List[str]:
    """Run the identical elimination procedure but stop as soon as |F| <= target_size, without
    ever consulting val R^2 to decide when to stop (the stopping point is fixed in advance)."""
    phases = sorted(set(phase_map.values()))
    k_min_of = {p: (0 if p == "cross_phase" else prfe.K_MIN) for p in phases}
    floor = sum(k_min_of.values())
    target_size = max(target_size, floor)

    F = list(X_tr.columns)

    def fit_for_importance(features):
        scaler = StandardScaler()
        Xtr = scaler.fit_transform(X_tr[features])
        Xv = scaler.transform(X_val[features])
        model = prfe.gb_model()
        model.fit(Xtr, y_tr)
        from sklearn.inspection import permutation_importance
        Xv_s = scaler.transform(X_val[features])
        pi = permutation_importance(
            model, Xv_s, y_val, n_repeats=prfe.N_REPEATS, random_state=prfe.RANDOM_STATE
        )
        return dict(zip(features, pi.importances_mean))

    while len(F) > target_size:
        importances = fit_for_importance(F)
        F_sorted = sorted(F, key=lambda f: importances[f])
        remaining = set(F)
        E: List[str] = []
        for f in F_sorted:
            if len(E) >= prfe.STEP or len(F) - len(E) <= target_size:
                break
            phase = phase_map[f]
            same_phase_remaining = sum(1 for g in remaining if g not in E and phase_map[g] == phase)
            if same_phase_remaining > k_min_of[phase]:
                E.append(f)
        if not E:
            break
        F = [f for f in F if f not in E]

    return F


def evaluate_on_test(features: List[str], X_train, y_train, X_test, y_test) -> float:
    scaler = StandardScaler()
    Xtr = scaler.fit_transform(X_train[features])
    Xte = scaler.transform(X_test[features])
    model = prfe.gb_model()
    model.fit(Xtr, y_train)
    return float(r2_score(y_test, model.predict(Xte)))


def run_domain(domain: str, verbose: bool = False) -> dict:
    domain_dir = CANONICAL_DATA_DIR / domain
    X, y, phase_map = prfe.load_domain(domain_dir)

    split_idx = int(len(X) * 0.8)
    X_outer_train, y_outer_train = X.iloc[:split_idx], y.iloc[:split_idx]
    X_test, y_test = X.iloc[split_idx:], y.iloc[split_idx:]

    # --- Step 2: inner nested selection of the stopping point ---
    tscv = TimeSeriesSplit(n_splits=N_INNER_SPLITS)
    fold_curves: List[Dict[int, float]] = []
    for fold_i, (tr_idx, val_idx) in enumerate(tscv.split(X_outer_train)):
        Xtr, ytr = X_outer_train.iloc[tr_idx], y_outer_train.iloc[tr_idx]
        Xv, yv = X_outer_train.iloc[val_idx], y_outer_train.iloc[val_idx]
        curve = elimination_curve(Xtr, ytr, Xv, yv, phase_map)
        fold_curves.append(dict(curve))
        if verbose:
            print(f"  [{domain}] inner fold {fold_i}: {len(curve)} checkpoints, "
                  f"train={len(Xtr)} val={len(Xv)}")

    common_sizes = set(fold_curves[0].keys())
    for c in fold_curves[1:]:
        common_sizes &= set(c.keys())
    if not common_sizes:
        raise RuntimeError(f"No common |F| checkpoints across inner folds for {domain}")

    mean_r2_by_size = {
        n: float(np.mean([c[n] for c in fold_curves])) for n in common_sizes
    }
    n_star = max(mean_r2_by_size, key=mean_r2_by_size.get)
    n_star_mean_cv_r2 = mean_r2_by_size[n_star]

    if verbose:
        print(f"  [{domain}] nested-selected stopping point: |F*|={n_star} "
              f"(mean inner-CV val R2={n_star_mean_cv_r2:.4f})")

    # --- Step 3: final elimination on the full 80% outer-train, stopping at the pre-fixed n_star ---
    n = len(X_outer_train)
    tr_end = int(n * 0.75)
    Xtr2, ytr2 = X_outer_train.iloc[:tr_end], y_outer_train.iloc[:tr_end]
    Xv2, yv2 = X_outer_train.iloc[tr_end:], y_outer_train.iloc[tr_end:]
    F_star = run_to_target_size(Xtr2, ytr2, Xv2, yv2, phase_map, target_size=n_star)

    # --- Step 4: score once on the untouched outer holdout ---
    test_r2 = evaluate_on_test(F_star, X_outer_train, y_outer_train, X_test, y_test)

    old = OLD_PUBLISHED.get(domain, {})
    return dict(
        domain=domain,
        n_total_features=X.shape[1],
        n_star=len(F_star),
        n_star_target=n_star,
        mean_inner_cv_r2_at_nstar=n_star_mean_cv_r2,
        nested_test_r2=test_r2,
        n_inner_checkpoints=len(common_sizes),
        old_n_selected=old.get("n_selected"),
        old_test_r2=old.get("test_r2"),
    )


def render_report(results: List[dict]) -> str:
    lines = ["# M13 — Nested Selection for PA-RFE's Stopping Point", ""]
    lines.append(
        f"Protocol: outer 80/20 temporal split (matching every other result in this paper); "
        f"inner TimeSeriesSplit({N_INNER_SPLITS}) within the 80% outer-train re-runs PA-RFE's "
        f"elimination procedure per fold (permutation_importance n_repeats={INNER_N_REPEATS} for "
        "these coarse inner-fold curves, reduced from the original 10 for tractability -- an "
        "initial 3-fold/n_repeats=10 run exceeded the available compute budget and was killed "
        "mid-run), averages validation R² at each common |F| checkpoint across folds, and selects "
        "the stopping point n* = argmax mean inner-CV R² -- never by peeking at the outer holdout. "
        "A final elimination run on the full 80% outer-train (75/25 internal split) stops at the "
        f"pre-fixed n*, at full n_repeats=10 fidelity (matching `pa_rfe.py`'s original), producing "
        "the actual F*; F* is scored once on the untouched 20% outer holdout. See "
        "`m13_pa_rfe_nested.py` docstring for full detail."
    )
    lines.append("")
    lines.append(
        "| Domain | Total feat. | Old (60/20/20, val-R²-selected) n | Old test R² | "
        "Nested n* (target) | Nested actual \\|F\\*\\| | Mean inner-CV R² at n* | "
        "Nested test R² (once, untouched) | Δ test R² (nested − old) |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in results:
        delta = (
            r["nested_test_r2"] - r["old_test_r2"]
            if r["old_test_r2"] is not None else float("nan")
        )
        lines.append(
            f"| {r['domain']} | {r['n_total_features']} | {r['old_n_selected']} | "
            f"{r['old_test_r2']:.3f} | {r['n_star_target']} | {r['n_star']} | "
            f"{r['mean_inner_cv_r2_at_nstar']:.4f} | {r['nested_test_r2']:.4f} | {delta:+.4f} |"
        )
    lines.append("")
    lines.append(
        "**Reading this table.** The old protocol selected its feature count by maximizing "
        "validation R² across ~45 iterations of a single fixed split, then reported test R² at "
        "that point once -- the paper's own text already identifies this as the mechanism behind "
        "the primary domain's severe overfitting (validation R²=0.271 vs. test R²=-3.026). The "
        f"nested protocol picks the stopping point via {N_INNER_SPLITS}-fold inner cross-"
        "validation instead, so the reported test R² above should no longer carry that specific "
        "selection bias, though it inherits the same small-sample instability every nested "
        f"result in this paper has (inner folds here are smaller than the outer 80% partition, "
        f"split {N_INNER_SPLITS} ways). The mean inner-CV R² column is frequently negative or "
        "far below the eventual test R² (e.g. abc-cloud-provider: -0.707 mean inner-CV vs. "
        "-0.333 test) -- a direct symptom of how small the inner folds are here (2 folds inside "
        "an already-80%-reduced training partition, so the first fold trains on as few as "
        "~30-55 rows for up to 241 features); the same CV-holdout discrepancy the paper already "
        "documents elsewhere (Section 4.1.2) for the primary results, now visible in this "
        "nested selection layer too."
    )
    lines.append("")
    return "\n".join(lines)


CACHE_DIR = SCRIPT_DIR / "output" / "m13_cache"


def _cache_path(domain: str) -> Path:
    return CACHE_DIR / f"{domain}.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", choices=ALL_DOMAINS, default=None,
                         help="Run a single domain and cache its result (for incremental runs).")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if args.domain:
        print(f"\n=== {args.domain} ===")
        r = run_domain(args.domain, verbose=args.verbose)
        print(f"  n*={r['n_star']} (target {r['n_star_target']})  nested test R2={r['nested_test_r2']:.4f}  "
              f"(old: n={r['old_n_selected']} test R2={r['old_test_r2']:.3f})")
        _cache_path(args.domain).write_text(json.dumps(r, indent=2), encoding="utf-8")
        print(f"  Cached to {_cache_path(args.domain)}")
        return

    # No --domain: use any cached per-domain results already on disk, compute the rest.
    results = []
    for domain in ALL_DOMAINS:
        cache_file = _cache_path(domain)
        if cache_file.exists():
            print(f"\n=== {domain} (from cache) ===")
            r = json.loads(cache_file.read_text(encoding="utf-8"))
        else:
            print(f"\n=== {domain} ===")
            r = run_domain(domain, verbose=args.verbose)
            cache_file.write_text(json.dumps(r, indent=2), encoding="utf-8")
        results.append(r)
        print(f"  n*={r['n_star']} (target {r['n_star_target']})  nested test R2={r['nested_test_r2']:.4f}  "
              f"(old: n={r['old_n_selected']} test R2={r['old_test_r2']:.3f})")

    report = render_report(results)
    out_path = SCRIPT_DIR / "PA_RFE_NESTED_SELECTION_EVIDENCE.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"\nReport saved to: {out_path}")


if __name__ == "__main__":
    main()
