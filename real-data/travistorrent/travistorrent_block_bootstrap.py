#!/usr/bin/env python3
"""TravisTorrent moving-block bootstrap (PRESTO v5 revision, Item 5 / Task A1).

Extends `code/synthetic_data_generator/m11_block_bootstrap.py`'s moving-block bootstrap
method -- added there for the 3 synthetic domains to address whether the standard
pairs/case bootstrap's exchangeability assumption is appropriate for temporally-ordered
holdouts -- to TravisTorrent's 7 within-project temporal holdouts. TravisTorrent builds
are ordered by `gh_build_started_at` per project (the same ordering variable
`run_pipeline_travistorrent.py`'s 80/20 split already uses), so consecutive holdout rows
can share autocorrelated residuals just as the synthetic domains' releases do; this was
flagged as follow-on scope in `BLOCK_BOOTSTRAP_EVIDENCE.md` and is filled in here.

Method: identical to `m11_block_bootstrap.py` -- `block_size_for()` (n^(1/3) rule,
floored at 2), `bootstrap_r2_ci_pairs()`, `bootstrap_r2_ci_moving_block()`, same seed
convention (20260810), same n_boot (2000), reused (not reimplemented) via direct import.
Model: Random Forest only, matching the paper's headline model choice for this evidence
family (`m11_block_bootstrap.py`, `BLOCK_BOOTSTRAP_EVIDENCE.md`'s fixed-hyperparameter
baseline) -- this is the paper's *secondary, untuned-baseline* protocol, not the primary
nested-CV-selected protocol introduced this revision (Section 3.2.5); see this script's
evidence doc for that scoping note. Data loading reuses
`run_pipeline_travistorrent.py`'s `load_all()`, `engineer()`, `remove_outliers()`,
`prepare_features()`, `build_models()` directly (via importlib, following
`real-data/bootstrap_real_world_ci.py`'s pattern) -- not reimplemented.

Usage: python travistorrent_block_bootstrap.py [--n-boot 2000] [--seed 20260810] [--verbose]
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
SYNTH_DIR = REPO_ROOT / "code" / "synthetic_data_generator"
sys.path.insert(0, str(SYNTH_DIR))

from m11_block_bootstrap import (  # noqa: E402
    block_size_for,
    bootstrap_r2_ci_moving_block,
    bootstrap_r2_ci_pairs,
)

PROJECTS = [
    "DataDog/dd-agent", "bundler/bundler", "getsentry/sentry", "gonum/matrix",
    "mongodb/mongoid", "rg3/youtube-dl", "rspec/rspec-core",
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def fit_and_predict_holdout_rf(mod, X: pd.DataFrame, y: pd.Series) -> Tuple[np.ndarray, np.ndarray]:
    """Random Forest only, same 80/20 split (row order already chronological) + scaling
    as run_pipeline_travistorrent.py's train_and_evaluate()."""
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    rf = mod.build_models()["Random Forest"]
    rf.fit(X_train_s, y_train)
    y_pred = rf.predict(X_test_s)
    return y_test.to_numpy(), y_pred


def run_case(mod, df_all: pd.DataFrame, project: str, n_boot: int, seed: int, verbose: bool) -> dict:
    df = df_all[df_all["gh_project_name"] == project].copy()
    df = mod.engineer(df)
    df = mod.remove_outliers(df)
    X, y = mod.prepare_features(df)

    y_true, y_pred = fit_and_predict_holdout_rf(mod, X, y)
    point_r2 = float(r2_score(y_true, y_pred))
    n = len(y_true)
    bsize = block_size_for(n)

    pairs_lo, pairs_hi, _ = bootstrap_r2_ci_pairs(y_true, y_pred, n_boot, seed)
    block_lo, block_hi, _ = bootstrap_r2_ci_moving_block(y_true, y_pred, n_boot, seed, block_size=bsize)

    if verbose:
        print(
            f"  [{project}] n={n} block_size={bsize} point_r2={point_r2:.4f}  "
            f"pairs CI=[{pairs_lo:.3f},{pairs_hi:.3f}]  block CI=[{block_lo:.3f},{block_hi:.3f}]"
        )

    return dict(
        project=project, n=n, block_size=bsize, point_r2=point_r2,
        pairs_ci=(pairs_lo, pairs_hi), pairs_width=pairs_hi - pairs_lo,
        block_ci=(block_lo, block_hi), block_width=block_hi - block_lo,
        pairs_excludes_zero=bool(pairs_lo > 0 or pairs_hi < 0),
        block_excludes_zero=bool(block_lo > 0 or block_hi < 0),
    )


def render_report(results: list[dict], n_boot: int, seed: int) -> str:
    lines = ["# TravisTorrent — Moving-Block Bootstrap for Temporally-Ordered Holdouts", ""]
    lines.append(
        f"**Method:** moving-block bootstrap, {n_boot} resamples per project, seed {seed}. "
        "Identical procedure to `code/synthetic_data_generator/m11_block_bootstrap.py` "
        "(`block_size_for()`, `bootstrap_r2_ci_pairs()`, `bootstrap_r2_ci_moving_block()`, "
        "imported directly, not reimplemented), applied here to TravisTorrent's 7 "
        "within-project temporal holdouts, filling the follow-on scope flagged in "
        "`BLOCK_BOOTSTRAP_EVIDENCE.md`. Block length follows n^(1/3), rounded, floored "
        "at 2, reported per project since holdout size varies substantially (project "
        "sizes range from ~2K to ~144K builds). Ordering variable: `gh_build_started_at` "
        "per project, the same ordering `run_pipeline_travistorrent.py`'s 80/20 split "
        "already uses."
    )
    lines.append("")
    lines.append(
        "**Model:** Random Forest only, matching this evidence family's headline-model "
        "convention (`m11_block_bootstrap.py`, `BLOCK_BOOTSTRAP_EVIDENCE.md`) -- the paper's "
        "*fixed-hyperparameter, secondary/untuned-baseline* protocol, not the primary "
        "nested-CV-selected protocol introduced this revision (Section 3.2.5). Data loading "
        "(`load_all`, `engineer`, `remove_outliers`, `prepare_features`, `build_models`) "
        "reused directly from `run_pipeline_travistorrent.py` via importlib, following "
        "`real-data/bootstrap_real_world_ci.py`'s pattern -- not reimplemented."
    )
    lines.append("")
    lines.append(
        "| Project | n (test) | Block size | Point R² | Pairs-bootstrap 95% CI (width) | "
        "Block-bootstrap 95% CI (width) | Pairs excl. 0? | Block excl. 0? |"
    )
    lines.append("|---|---:|---:|---:|---|---|:---:|:---:|")
    for r in results:
        lines.append(
            f"| {r['project']} | {r['n']} | {r['block_size']} | {r['point_r2']:.3f} | "
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
        f"projects: {mean_widening:+.3f} R² units. {n_flip} of {len(results)} project(s) "
        "change significance status (excludes-zero vs. not) between the two bootstrap "
        "methods."
    )
    lines.append("")
    lines.append(
        "**Interpretation.** None of TravisTorrent's 7 projects are part of this paper's "
        "confirmatory set (Section 4.1, opening note) -- all 7 are already reported as "
        "exploratory/diagnostic, and the per-project point R² values here are the same "
        "fixed-hyperparameter Random Forest results already in the manuscript's TravisTorrent "
        "Results subsection. This table adds the dependence-aware CI a reviewer asking for "
        "temporal-holdout bootstrap coverage would expect; it does not change which results "
        "are labeled confirmatory."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-boot", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260810)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    mod = load_module("travistorrent_pipeline", SCRIPT_DIR / "run_pipeline_travistorrent.py")
    df_all = mod.load_all(verbose=args.verbose)

    results = []
    for project in PROJECTS:
        print(f"=== {project} ===")
        results.append(run_case(mod, df_all, project, args.n_boot, args.seed, args.verbose))

    report = render_report(results, args.n_boot, args.seed)
    out_path = SCRIPT_DIR / "TRAVISTORRENT_BLOCK_BOOTSTRAP_EVIDENCE.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"\nReport saved to: {out_path}")


if __name__ == "__main__":
    main()
