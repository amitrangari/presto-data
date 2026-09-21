#!/usr/bin/env python3
"""M11 (v4 revision, Reviewer 2 round 3): moving-block bootstrap for temporally-ordered holdouts.

Reviewer 2's round-3 review flags that `r1_analysis.py`'s existing pairs/case bootstrap
(resample (y_true, y_pred) pairs independently with replacement, 2000x) assumes exchangeability,
which is questionable for temporally-ordered holdout observations -- consecutive releases in the
holdout share autocorrelated errors (the same AR(1)-style persistence the paper documents for the
target itself), so treating each holdout row as an independent, freely-shuffleable draw understates
the true sampling uncertainty.

This script adds a MOVING BLOCK bootstrap as an alternative resampling scheme, applied only to
TEMPORALLY-ORDERED datasets (the 3 synthetic domains here; TravisTorrent and Perfherder are
handled in the real-world adapter scripts). GHALogs and SQuaD are cross-sectional (no temporal
ordering within their holdouts), so the existing pairs bootstrap remains the statistically correct
choice there and is not touched by this script.

Method: resample contiguous BLOCKS of (y_true, y_pred) pairs (not individual pairs) with
replacement, concatenate blocks until reaching the original holdout length (truncating the final
block if needed), and recompute R^2 per resample -- exactly analogous to a moving-block
bootstrap for a dependent time series, applied here to the (error) sequence implicit in
(y_true - y_pred). Block length follows the common n^(1/3) rule of thumb for holdouts this size
(30-40 rows), rounded to the nearest integer >= 2, and is reported explicitly per case since it's
data-size-dependent, not a fixed constant.

Usage: python m11_block_bootstrap.py [--n-boot 2000] [--seed 20260810] [--verbose]
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import run_pipeline as pipe  # noqa: E402

DATA_ROOT = Path("/Volumes/4TB/research-data-and-code/zenado/presto-data/synthetic-data-projects")
ALL_DOMAINS = ["abc-cloud-provider", "card-payment-processor", "xyz-sales-force"]

# The paper's existing pairs-bootstrap headline figures (Section 4.1.5, Table under "Bootstrap
# Confidence Intervals"), for direct old-vs-new comparison.
EXISTING_PAIRS_CI = {
    ("abc-cloud-provider", "with_AR", "Random Forest"): {"r2": 0.914, "ci": (0.280, 0.964)},
    ("abc-cloud-provider", "without_AR", "Random Forest"): {"r2": 0.107, "ci": (-6.533, 0.463)},
    ("card-payment-processor", "without_AR", "Random Forest"): {"r2": 0.475, "ci": (-0.179, 0.892)},
    ("xyz-sales-force", "without_AR", "Random Forest"): {"r2": 0.487, "ci": (0.222, 0.658)},
}


def block_size_for(n: int) -> int:
    """n^(1/3) rule of thumb, rounded, floored at 2."""
    return max(2, round(n ** (1.0 / 3.0)))


def bootstrap_r2_ci_pairs(
    y_true: np.ndarray, y_pred: np.ndarray, n_boot: int, seed: int, alpha: float = 0.05
) -> Tuple[float, float, float]:
    """Identical to r1_analysis.py's bootstrap_r2_ci -- reimplemented here (not imported) so
    this script has no import-order dependency on r1_analysis.py's module-level side effects."""
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


def bootstrap_r2_ci_moving_block(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_boot: int,
    seed: int,
    block_size: int,
    alpha: float = 0.05,
) -> Tuple[float, float, float]:
    """Moving-block bootstrap 95% CI for holdout R^2.

    Resamples overlapping contiguous blocks of length `block_size` from the (y_true, y_pred)
    sequence with replacement, concatenates blocks (truncating the final one) to reconstruct a
    resampled sequence of the original length n, and recomputes R^2 per resample. Preserves
    local temporal dependence within each block, unlike the pairs bootstrap which shuffles every
    row independently.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    n = len(y_true)
    n_blocks_needed = int(np.ceil(n / block_size))
    n_possible_starts = n - block_size + 1
    if n_possible_starts < 1:
        raise ValueError(f"block_size={block_size} exceeds holdout length n={n}")

    rng = np.random.default_rng(seed)
    boot_r2 = np.empty(n_boot)
    for b in range(n_boot):
        starts = rng.integers(0, n_possible_starts, size=n_blocks_needed)
        yt_parts, yp_parts = [], []
        for s in starts:
            yt_parts.append(y_true[s : s + block_size])
            yp_parts.append(y_pred[s : s + block_size])
        yt = np.concatenate(yt_parts)[:n]
        yp = np.concatenate(yp_parts)[:n]
        ss_res = np.sum((yt - yp) ** 2)
        ss_tot = np.sum((yt - yt.mean()) ** 2)
        boot_r2[b] = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan
    boot_r2 = boot_r2[~np.isnan(boot_r2)]
    lo, hi = np.percentile(boot_r2, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi), float(np.median(boot_r2))


def fit_and_predict_holdout_rf(X: pd.DataFrame, y: pd.Series) -> Tuple[np.ndarray, np.ndarray]:
    """Random Forest only (the paper's headline model), same split/scaling as run_pipeline."""
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    rf = pipe.build_models()["Random Forest"]
    rf.fit(X_train_s, y_train)
    y_pred = rf.predict(X_test_s)
    return y_test.to_numpy(), y_pred


def run_case(domain: str, condition: str, n_boot: int, seed: int, verbose: bool) -> dict:
    domain_dir = DATA_ROOT / domain
    df = pipe.load_and_merge(domain_dir)
    df_eng = pipe.engineer_features(df)
    exclude_leakage = condition == "without_AR"
    X, y, _ = pipe.prepare_features(df_eng, exclude_leakage=exclude_leakage)
    y_true, y_pred = fit_and_predict_holdout_rf(X, y)

    point_r2 = float(r2_score(y_true, y_pred))
    n = len(y_true)
    bsize = block_size_for(n)

    pairs_lo, pairs_hi, pairs_med = bootstrap_r2_ci_pairs(y_true, y_pred, n_boot, seed)
    block_lo, block_hi, block_med = bootstrap_r2_ci_moving_block(
        y_true, y_pred, n_boot, seed, block_size=bsize
    )

    if verbose:
        print(
            f"  [{domain}/{condition}] n={n} block_size={bsize} point_r2={point_r2:.4f}  "
            f"pairs CI=[{pairs_lo:.3f},{pairs_hi:.3f}]  block CI=[{block_lo:.3f},{block_hi:.3f}]"
        )

    return dict(
        domain=domain,
        condition=condition,
        n=n,
        block_size=bsize,
        point_r2=point_r2,
        pairs_ci=(pairs_lo, pairs_hi),
        pairs_width=pairs_hi - pairs_lo,
        block_ci=(block_lo, block_hi),
        block_width=block_hi - block_lo,
        pairs_excludes_zero=bool(pairs_lo > 0 or pairs_hi < 0),
        block_excludes_zero=bool(block_lo > 0 or block_hi < 0),
    )


def render_report(results: list[dict], n_boot: int, seed: int) -> str:
    lines = ["# M11 — Moving-Block Bootstrap for Temporally-Ordered Holdouts", ""]
    lines.append(
        f"**Method:** moving-block bootstrap, {n_boot} resamples per case, seed {seed}. Block "
        "length follows n^(1/3), rounded, floored at 2 (reported per case since holdout size "
        "varies). Resamples overlapping contiguous blocks of (y_true, y_pred) with replacement, "
        "concatenates to the original holdout length, recomputes R^2 per resample. Compared "
        "directly against the existing pairs/case bootstrap (`r1_analysis.py`'s method, 2000 "
        "resamples, identical seed) on the *same* fitted-model predictions, so any CI-width "
        "difference reflects the resampling scheme alone, not a different model fit."
    )
    lines.append("")
    lines.append(
        "**Scope:** the 3 synthetic domains only (temporally-ordered by construction). "
        "TravisTorrent and Mozilla Perfherder (also temporally ordered) would need this same "
        "treatment in their own adapter scripts -- not done here, flagged as follow-on scope. "
        "GHALogs and SQuaD are cross-sectional (no temporal ordering within their holdouts), so "
        "the existing pairs bootstrap remains the statistically appropriate choice there and "
        "should NOT be replaced with a block bootstrap."
    )
    lines.append("")
    lines.append("Random Forest only (the paper's headline model for every case below).")
    lines.append("")
    lines.append(
        "| Domain | Condition | n | Block size | Point R² | Pairs-bootstrap 95% CI "
        "(width) | Block-bootstrap 95% CI (width) | Pairs excl. 0? | Block excl. 0? |"
    )
    lines.append("|---|---|---:|---:|---:|---|---|:---:|:---:|")
    for r in results:
        lines.append(
            f"| {r['domain']} | {r['condition']} | {r['n']} | {r['block_size']} | "
            f"{r['point_r2']:.3f} | [{r['pairs_ci'][0]:.3f}, {r['pairs_ci'][1]:.3f}] "
            f"({r['pairs_width']:.3f}) | [{r['block_ci'][0]:.3f}, {r['block_ci'][1]:.3f}] "
            f"({r['block_width']:.3f}) | {'yes' if r['pairs_excludes_zero'] else 'no'} | "
            f"{'yes' if r['block_excludes_zero'] else 'no'} |"
        )
    lines.append("")

    mean_widening = np.mean([r["block_width"] - r["pairs_width"] for r in results])
    n_flip = sum(1 for r in results if r["pairs_excludes_zero"] != r["block_excludes_zero"])
    lines.append(
        f"**Summary:** mean CI width change (block − pairs) across these {len(results)} cases: "
        f"{mean_widening:+.3f} R² units. {n_flip} of {len(results)} case(s) change significance "
        "status (excludes-zero vs. not) between the two bootstrap methods."
    )
    lines.append("")
    lines.append(
        "**Interpretation.** A moving-block bootstrap that preserves local temporal dependence "
        "in the (error) sequence is expected to produce wider (or equal) CIs than a pairs "
        "bootstrap when residuals are positively autocorrelated, since blocks limit how much "
        "resampled variability the procedure can generate relative to treating every row as an "
        "independent draw. Whether that pattern holds here, and how large the practical effect "
        "is on any headline significance claim, should be read directly from the table above "
        "rather than assumed."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-boot", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260810)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    cases = [
        ("abc-cloud-provider", "with_AR"),
        ("abc-cloud-provider", "without_AR"),
        ("card-payment-processor", "without_AR"),
        ("xyz-sales-force", "without_AR"),
    ]
    results = []
    for domain, condition in cases:
        print(f"=== {domain} / {condition} ===")
        results.append(run_case(domain, condition, args.n_boot, args.seed, args.verbose))

    report = render_report(results, args.n_boot, args.seed)
    out_path = SCRIPT_DIR / "BLOCK_BOOTSTRAP_EVIDENCE.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"\nReport saved to: {out_path}")


if __name__ == "__main__":
    main()
