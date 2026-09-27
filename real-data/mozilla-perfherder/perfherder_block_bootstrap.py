#!/usr/bin/env python3
"""Mozilla Perfherder moving-block bootstrap (PRESTO v5 revision, Item 5 / Task A1).

Extends `code/synthetic_data_generator/m11_block_bootstrap.py`'s moving-block bootstrap
method to Perfherder's 3 within-signature temporal holdouts, with-AR condition -- matching
`real-data/bootstrap_real_world_ci.py`'s `run_perfherder()` scope (with-AR only; that
script's docstring names the with-AR condition specifically, and Perfherder's with-AR
results are part of this paper's confirmatory set, Section 4.1 opening note). Perfherder
pushes are ordered by `push_timestamp` per signature (the same ordering variable
`run_pipeline_perfherder.py`'s 80/20 split already uses), so consecutive holdout rows can
share autocorrelated residuals just as the synthetic domains' releases do; this was
flagged as follow-on scope in `BLOCK_BOOTSTRAP_EVIDENCE.md` and is filled in here.

Method: identical to `m11_block_bootstrap.py` -- `block_size_for()` (n^(1/3) rule,
floored at 2), `bootstrap_r2_ci_pairs()`, `bootstrap_r2_ci_moving_block()`, same seed
convention (20260810), same n_boot (2000), reused (not reimplemented) via direct import.
Model: Random Forest only, matching this evidence family's headline-model convention.
Data loading reuses `run_pipeline_perfherder.py`'s `load_alerts_lookup()`,
`load_signature_series()`, `engineer_features()`, `prepare_features()` directly (via
importlib, following `real-data/bootstrap_real_world_ci.py`'s `run_perfherder()` pattern)
-- not reimplemented.

Usage: python perfherder_block_bootstrap.py [--n-boot 2000] [--seed 20260810] [--verbose]
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler

# NOTE: `run_pipeline_perfherder.py`'s own train_and_evaluate() hardcodes an
# UNCONSTRAINED Random Forest (n_estimators=100, random_state=42, no max_depth /
# min_samples_split / min_samples_leaf). `real-data/bootstrap_real_world_ci.py` --
# whose already-published pairs-bootstrap Perfherder numbers this script must match
# for direct comparability -- instead evaluates Perfherder through its OWN
# build_models(), which uses the CONSTRAINED Random Forest below (identical to
# run_pipeline_travistorrent.py's and the synthetic pipeline's RF). This script
# follows bootstrap_real_world_ci.py's choice (verified against
# REAL_WORLD_BOOTSTRAP_CI_EVIDENCE_slow.md: espn-loadtime RF R2=0.2353 CI
# [0.1473,0.3109]; instagram-speedindex RF R2=0.1527 CI [0.1081,0.1912];
# nytimes-speedindex RF R2=0.1261 CI [0.0386,0.2001] -- reproduced exactly below),
# not run_pipeline_perfherder.py's own inline model dict.

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
SYNTH_DIR = REPO_ROOT / "code" / "synthetic_data_generator"
sys.path.insert(0, str(SYNTH_DIR))

from m11_block_bootstrap import (  # noqa: E402
    block_size_for,
    bootstrap_r2_ci_moving_block,
    bootstrap_r2_ci_pairs,
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def fit_and_predict_holdout_rf(X: pd.DataFrame, y: pd.Series) -> Tuple[np.ndarray, np.ndarray]:
    """Random Forest only, same 80/20 split (chronological row order) + scaling
    bootstrap_real_world_ci.py uses. See module-level NOTE: uses the CONSTRAINED RF
    (max_depth=10, min_samples_split=5, min_samples_leaf=2) to match
    bootstrap_real_world_ci.py's build_models(), not run_pipeline_perfherder.py's own
    unconstrained RF."""
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    rf = RandomForestRegressor(
        n_estimators=100, max_depth=10, min_samples_split=5,
        min_samples_leaf=2, random_state=42,
    )
    rf.fit(X_train_s, y_train)
    y_pred = rf.predict(X_test_s)
    return y_test.to_numpy(), y_pred


def run_case(mod, name: str, spec: dict, alerts_lookup: dict, n_boot: int, seed: int, verbose: bool) -> dict:
    path = SCRIPT_DIR / spec["path"]
    if not path.exists():
        found = mod.find_signature_file(spec["id"])
        if found is None:
            raise FileNotFoundError(f"signature file not found for {spec['id']}")
        path = found
    df = mod.load_signature_series(path, spec["id"], alerts_lookup, verbose=verbose)
    df_eng = mod.engineer_features(df, verbose=verbose)
    X_with, y, target_derived = mod.prepare_features(df_eng, exclude_target_derived=False)

    y_true, y_pred = fit_and_predict_holdout_rf(X_with, y)
    point_r2 = float(r2_score(y_true, y_pred))
    n = len(y_true)
    bsize = block_size_for(n)

    pairs_lo, pairs_hi, _ = bootstrap_r2_ci_pairs(y_true, y_pred, n_boot, seed)
    block_lo, block_hi, _ = bootstrap_r2_ci_moving_block(y_true, y_pred, n_boot, seed, block_size=bsize)

    if verbose:
        print(
            f"  [{name}] n={n} block_size={bsize} point_r2={point_r2:.4f}  "
            f"pairs CI=[{pairs_lo:.3f},{pairs_hi:.3f}]  block CI=[{block_lo:.3f},{block_hi:.3f}]"
        )

    return dict(
        signature=name, n=n, block_size=bsize, point_r2=point_r2,
        pairs_ci=(pairs_lo, pairs_hi), pairs_width=pairs_hi - pairs_lo,
        block_ci=(block_lo, block_hi), block_width=block_hi - block_lo,
        pairs_excludes_zero=bool(pairs_lo > 0 or pairs_hi < 0),
        block_excludes_zero=bool(block_lo > 0 or block_hi < 0),
    )


def render_report(results: list[dict], n_boot: int, seed: int) -> str:
    lines = ["# Mozilla Perfherder — Moving-Block Bootstrap for Temporally-Ordered Holdouts", ""]
    lines.append(
        f"**Method:** moving-block bootstrap, {n_boot} resamples per signature, seed {seed}. "
        "Identical procedure to `code/synthetic_data_generator/m11_block_bootstrap.py` "
        "(`block_size_for()`, `bootstrap_r2_ci_pairs()`, `bootstrap_r2_ci_moving_block()`, "
        "imported directly, not reimplemented), applied here to Perfherder's 3 "
        "within-signature temporal holdouts, with-AR (target-derived-features-included) "
        "condition, matching `real-data/bootstrap_real_world_ci.py`'s `run_perfherder()` "
        "scope. Filling the follow-on scope flagged in `BLOCK_BOOTSTRAP_EVIDENCE.md`. "
        "Block length follows n^(1/3), rounded, floored at 2, reported per signature. "
        "Ordering variable: `push_timestamp` per signature, the same ordering "
        "`run_pipeline_perfherder.py`'s 80/20 split already uses."
    )
    lines.append("")
    lines.append(
        "**Model:** Random Forest only, matching this evidence family's headline-model "
        "convention (`m11_block_bootstrap.py`, `BLOCK_BOOTSTRAP_EVIDENCE.md`) -- the paper's "
        "*fixed-hyperparameter, secondary/untuned-baseline* protocol, not the primary "
        "nested-CV-selected protocol introduced this revision (Section 3.2.5). Data loading "
        "(`load_alerts_lookup`, `load_signature_series`, `engineer_features`, "
        "`prepare_features`) reused directly from `run_pipeline_perfherder.py` via "
        "importlib -- not reimplemented. Scope: with-AR condition only, matching "
        "`bootstrap_real_world_ci.py`'s `run_perfherder()`, since Perfherder's with-AR "
        "results are part of this paper's confirmatory set (Section 4.1 opening note); the "
        "without-AR (alert-history-only) condition is covered separately in the "
        "paired-difference bootstrap (`PAIRED_DIFFERENCE_BOOTSTRAP_EVIDENCE.md`, comparison "
        "B1), not here."
    )
    lines.append("")
    lines.append(
        "| Signature | n (test) | Block size | Point R² | Pairs-bootstrap 95% CI (width) | "
        "Block-bootstrap 95% CI (width) | Pairs excl. 0? | Block excl. 0? |"
    )
    lines.append("|---|---:|---:|---:|---|---|:---:|:---:|")
    for r in results:
        lines.append(
            f"| {r['signature']} | {r['n']} | {r['block_size']} | {r['point_r2']:.3f} | "
            f"[{r['pairs_ci'][0]:.3f}, {r['pairs_ci'][1]:.3f}] ({r['pairs_width']:.3f}) | "
            f"[{r['block_ci'][0]:.3f}, {r['block_ci'][1]:.3f}] ({r['block_width']:.3f}) | "
            f"{'yes' if r['pairs_excludes_zero'] else 'no'} | "
            f"{'yes' if r['block_excludes_zero'] else 'no'} |"
        )
    lines.append("")

    mean_widening = np.mean([r["block_width"] - r["pairs_width"] for r in results])
    n_flip = sum(1 for r in results if r["pairs_excludes_zero"] != r["block_excludes_zero"])
    lines.append(
        f"**Summary:** mean CI width change (block − pairs) across these {len(results)} "
        f"signatures: {mean_widening:+.3f} R² units. {n_flip} of {len(results)} signature(s) "
        "change significance status (excludes-zero vs. not) between the two bootstrap "
        "methods."
    )
    lines.append("")
    lines.append(
        "**Interpretation.** Perfherder's with-AR results are part of this paper's "
        "confirmatory set. A significance-status flip here (pairs says significant, block "
        "does not, or vice versa) would directly affect that designation and should be read "
        "from the table above, not assumed from the synthetic-domain pattern."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-boot", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260810)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    mod = load_module("perfherder_pipeline", SCRIPT_DIR / "run_pipeline_perfherder.py")
    alerts_lookup = mod.load_alerts_lookup(SCRIPT_DIR / "alerts_data.csv")

    results = []
    for name, spec in mod.SIGNATURES.items():
        print(f"=== {name} ===")
        results.append(run_case(mod, name, spec, alerts_lookup, args.n_boot, args.seed, args.verbose))

    report = render_report(results, args.n_boot, args.seed)
    out_path = SCRIPT_DIR / "PERFHERDER_BLOCK_BOOTSTRAP_EVIDENCE.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"\nReport saved to: {out_path}")


if __name__ == "__main__":
    main()
