#!/usr/bin/env python3
"""Paired-difference bootstrap CIs (PRESTO v5 revision, Item 4 / Task B).

Reviewer 2's round-2 review objects to reporting two separate confidence intervals for
"with feature X" and "without feature X" and then eyeballing whether they look different --
that comparison should instead be a single paired-difference bootstrap CI on the R^2
DIFFERENCE itself, computed by resampling the SAME bootstrap indices jointly across both
conditions per resample (not two independent bootstraps).

This script implements that once (`bootstrap_r2_diff_ci()`) and applies it to four
comparisons, each reusing the relevant dataset's own existing pipeline module for data
loading / feature engineering / model fitting -- nothing is refit with different
hyperparameters than what is already reported elsewhere in this repo:

  B1. With-AR vs. without-AR      -- 3 synthetic domains (all cases where both conditions
                                      exist, i.e. all 3 after this revision's block-bootstrap
                                      cell fill) + Mozilla Perfherder (3 signatures,
                                      with-AR vs. alert-history-only/without-AR).
  B2. GHALogs full-feature vs. `mean_n_steps`-ablated (the paper's central real-world
      downgrade, previously argued via two separate CIs -- exactly what Reviewer 2 objects
      to).
  B3. TravisTorrent full vs. circular-feature-excluded (`tr_log_testduration`-derived
      features dropped), per project (7 projects).
  B4. SQuaD plain (process-metrics-only) vs. static-analysis-enriched (SonarQube/PMD/CK)
      defect-fix rate.

Method: `bootstrap_r2_diff_ci()` resamples the same bootstrap indices for both conditions'
(y_true, y_pred) pairs on each of `n_boot` resamples (default 2000, seed 20260810 -- the
same convention as `m11_block_bootstrap.py` and `bootstrap_real_world_ci.py`), computes
R^2_conditionA(resample) - R^2_conditionB(resample) each time, and reports the 2.5/97.5
percentile CI on that difference. Model: Random Forest throughout, matching the headline
model already used in `m11_block_bootstrap.py`, `bootstrap_real_world_ci.py`, and the
travistorrent/perfherder block-bootstrap adapters this revision -- so a single model choice
is held constant across the whole with/without-AR and full/ablated comparison family.

**Correctness check performed before every comparison in this script:** y_true is verified
identical (same values, same order) between the two conditions being paired before any
difference is computed -- see each `run_*` function's `assert` on shared y_true / row keys.
Where two conditions do not share row order/count positionally (checked, not assumed), rows
are aligned on their natural key (project_name for SQuaD) before pairing.

Usage: python paired_difference_bootstrap.py [--n-boot 2000] [--seed 20260810] [--verbose]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler

REAL_DATA_DIR = Path(__file__).resolve().parent
REPO_ROOT = REAL_DATA_DIR.parent
SYNTH_DIR = REPO_ROOT / "code" / "synthetic_data_generator"

# The single Random Forest hyperparameter set used throughout this evidence family
# (m11_block_bootstrap.py, bootstrap_real_world_ci.py's build_models(),
# run_pipeline_travistorrent.py's / run_pipeline_squad.py's build_models(),
# run_pipeline_ghalogs_ablation.py). Held fixed across every comparison below so a
# difference reflects the feature-set change alone, not a different model fit.
RF_KWARGS = dict(n_estimators=100, max_depth=10, min_samples_split=5, min_samples_leaf=2, random_state=42)
# n_jobs is a parallelization setting, not a hyperparameter -- it does not affect fitted
# tree structure, predictions, or randomness (random_state is still fixed), only wall-clock
# time. Added here (not in the hyperparameter dict comment above) to speed up TravisTorrent's
# large per-project fits (up to ~117K training rows x 241 features) on this machine's 10 cores.
RF_FIT_KWARGS = dict(RF_KWARGS, n_jobs=-1)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def bootstrap_r2_diff_ci(
    y_true: np.ndarray,
    y_pred_a: np.ndarray,
    y_pred_b: np.ndarray,
    n_boot: int,
    seed: int,
    alpha: float = 0.05,
) -> dict:
    """Paired-difference bootstrap: resamples the SAME indices for both conditions on each
    resample, computes R2_a(resample) - R2_b(resample), returns the percentile CI on the
    difference. `y_true` must be identical between conditions (verified by the caller)."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred_a = np.asarray(y_pred_a, dtype=float)
    y_pred_b = np.asarray(y_pred_b, dtype=float)
    n = len(y_true)
    assert len(y_pred_a) == n and len(y_pred_b) == n, "condition length mismatch"

    point_r2_a = float(r2_score(y_true, y_pred_a))
    point_r2_b = float(r2_score(y_true, y_pred_b))
    point_diff = point_r2_a - point_r2_b

    rng = np.random.default_rng(seed)
    diffs = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        yt = y_true[idx]
        ss_tot = np.sum((yt - yt.mean()) ** 2)
        if ss_tot <= 0:
            diffs[b] = np.nan
            continue
        r2_a = 1.0 - np.sum((yt - y_pred_a[idx]) ** 2) / ss_tot
        r2_b = 1.0 - np.sum((yt - y_pred_b[idx]) ** 2) / ss_tot
        diffs[b] = r2_a - r2_b
    diffs = diffs[~np.isnan(diffs)]
    lo, hi = np.percentile(diffs, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return dict(
        r2_a=point_r2_a, r2_b=point_r2_b, point_diff=point_diff,
        ci_lo=float(lo), ci_hi=float(hi), n=n,
        excludes_zero=bool(lo > 0 or hi < 0),
    )


def fit_rf_holdout(X: pd.DataFrame, y: pd.Series) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """80/20 split (row order as given), StandardScaler fit on train, Random Forest
    (RF_KWARGS). Returns (y_test, y_pred, test_index) -- test_index lets callers verify
    two conditions share the same held-out rows before pairing."""
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    rf = RandomForestRegressor(**RF_FIT_KWARGS)
    rf.fit(X_train_s, y_train)
    y_pred = rf.predict(X_test_s)
    return y_test.to_numpy(), y_pred, X_test.index.to_numpy()


# ---------------------------------------------------------------------------
# B1a. Synthetic domains: with-AR vs. without-AR
# ---------------------------------------------------------------------------
def run_synthetic_with_without(n_boot: int, seed: int, verbose: bool) -> List[dict]:
    pipe = load_module("synthetic_pipeline", SYNTH_DIR / "run_pipeline.py")
    data_root = Path("/Volumes/4TB/research-data-and-code/zenado/presto-data/synthetic-data-projects")
    rows = []
    for domain in ["abc-cloud-provider", "card-payment-processor", "xyz-sales-force"]:
        df = pipe.load_and_merge(data_root / domain)
        df_eng = pipe.engineer_features(df)
        X_with, y_with, _ = pipe.prepare_features(df_eng, exclude_leakage=False)
        X_without, y_without, _ = pipe.prepare_features(df_eng, exclude_leakage=True)
        # Correctness check: y is derived from the same df_eng regardless of exclude_leakage
        # (only column selection on X differs) -- verify, don't assume.
        assert len(y_with) == len(y_without) and np.allclose(y_with.to_numpy(), y_without.to_numpy()), \
            f"{domain}: y_true mismatch between with-AR/without-AR conditions"

        y_true_a, pred_with, idx_with = fit_rf_holdout(X_with, y_with)
        y_true_b, pred_without, idx_without = fit_rf_holdout(X_without, y_without)
        assert np.array_equal(idx_with, idx_without), f"{domain}: holdout row index mismatch"
        assert np.allclose(y_true_a, y_true_b), f"{domain}: holdout y_true mismatch"

        res = bootstrap_r2_diff_ci(y_true_a, pred_with, pred_without, n_boot, seed)
        res.update(comparison="with-AR minus without-AR", dataset="synthetic", case=domain)
        rows.append(res)
        if verbose:
            print(f"  [{domain}] with-AR R2={res['r2_a']:.4f} without-AR R2={res['r2_b']:.4f} "
                  f"diff={res['point_diff']:+.4f} CI=[{res['ci_lo']:+.4f},{res['ci_hi']:+.4f}]")
    return rows


# ---------------------------------------------------------------------------
# B1b. Perfherder: with-AR vs. without-AR (alert-history-only)
# ---------------------------------------------------------------------------
def run_perfherder_with_without(n_boot: int, seed: int, verbose: bool) -> List[dict]:
    pf_dir = REAL_DATA_DIR / "mozilla-perfherder"
    mod = load_module("perfherder_pipeline", pf_dir / "run_pipeline_perfherder.py")
    alerts_lookup = mod.load_alerts_lookup(pf_dir / "alerts_data.csv")
    rows = []
    for name, spec in mod.SIGNATURES.items():
        path = pf_dir / spec["path"]
        if not path.exists():
            found = mod.find_signature_file(spec["id"])
            path = found
        df = mod.load_signature_series(path, spec["id"], alerts_lookup, verbose=False)
        df_eng = mod.engineer_features(df, verbose=False)
        X_with, y_with, _ = mod.prepare_features(df_eng, exclude_target_derived=False)
        X_without, y_without, _ = mod.prepare_features(df_eng, exclude_target_derived=True)
        assert np.allclose(y_with.to_numpy(), y_without.to_numpy()), \
            f"{name}: y_true mismatch between with-AR/without-AR conditions"

        y_true_a, pred_with, idx_with = fit_rf_holdout(X_with, y_with)
        y_true_b, pred_without, idx_without = fit_rf_holdout(X_without, y_without)
        assert np.array_equal(idx_with, idx_without), f"{name}: holdout row index mismatch"

        res = bootstrap_r2_diff_ci(y_true_a, pred_with, pred_without, n_boot, seed)
        res.update(comparison="with-AR minus without-AR", dataset="perfherder", case=name)
        rows.append(res)
        if verbose:
            print(f"  [{name}] with-AR R2={res['r2_a']:.4f} without-AR R2={res['r2_b']:.4f} "
                  f"diff={res['point_diff']:+.4f} CI=[{res['ci_lo']:+.4f},{res['ci_hi']:+.4f}]")
    return rows


# ---------------------------------------------------------------------------
# B2. GHALogs: full-feature vs. mean_n_steps-ablated
# ---------------------------------------------------------------------------
def run_ghalogs_ablation(n_boot: int, seed: int, verbose: bool) -> List[dict]:
    gh_dir = REAL_DATA_DIR / "ghalogs"
    mod = load_module("ghalogs_pipeline", gh_dir / "run_pipeline_ghalogs.py")
    run_agg = mod.load_repo_aggregates(verbose=False)
    repo_meta = mod.load_repo_metadata(verbose=False)
    merged = run_agg.merge(repo_meta, on="repository_name", how="inner")
    merged = mod.engineer(merged)
    merged = merged.dropna(subset=["mean_total_time"])
    merged = merged.sort_values("pushedAt")  # chronological, matching run_pipeline_ghalogs.py's main()

    X_full, y = mod.prepare_features(merged)
    dropped = [c for c in ["mean_n_steps"] if c in X_full.columns]
    X_ablated = X_full.drop(columns=dropped)
    if verbose:
        print(f"  GHALogs: full={X_full.shape[1]} features, ablated={X_ablated.shape[1]} "
              f"(dropped {dropped}), n={len(X_full)}")

    y_true_a, pred_full, idx_full = fit_rf_holdout(X_full, y)
    y_true_b, pred_ablated, idx_ablated = fit_rf_holdout(X_ablated, y)
    assert np.array_equal(idx_full, idx_ablated), "GHALogs: holdout row index mismatch"

    res = bootstrap_r2_diff_ci(y_true_a, pred_full, pred_ablated, n_boot, seed)
    res.update(comparison="full-feature minus mean_n_steps-ablated", dataset="ghalogs", case="all repos")
    if verbose:
        print(f"  [GHALogs] full R2={res['r2_a']:.4f} ablated R2={res['r2_b']:.4f} "
              f"diff={res['point_diff']:+.4f} CI=[{res['ci_lo']:+.4f},{res['ci_hi']:+.4f}]")
    return [res]


# ---------------------------------------------------------------------------
# B3. TravisTorrent: full vs. circular-feature-excluded (per project)
# ---------------------------------------------------------------------------
def run_travistorrent_circular(n_boot: int, seed: int, verbose: bool) -> List[dict]:
    tt_dir = REAL_DATA_DIR / "travistorrent"
    mod = load_module("travistorrent_pipeline", tt_dir / "run_pipeline_travistorrent.py")
    df_all = mod.load_all(verbose=False)
    rows = []
    for project in ["DataDog/dd-agent", "bundler/bundler", "getsentry/sentry", "gonum/matrix",
                     "mongodb/mongoid", "rg3/youtube-dl", "rspec/rspec-core"]:
        df = df_all[df_all["gh_project_name"] == project].copy()
        df = mod.engineer(df)
        df = mod.remove_outliers(df)
        X_full, y = mod.prepare_features(df)
        excluded = [c for c in X_full.columns if "testduration" in c]
        X_ablated = X_full.drop(columns=excluded)

        y_true_a, pred_full, idx_full = fit_rf_holdout(X_full, y)
        y_true_b, pred_ablated, idx_ablated = fit_rf_holdout(X_ablated, y)
        assert np.array_equal(idx_full, idx_ablated), f"{project}: holdout row index mismatch"

        res = bootstrap_r2_diff_ci(y_true_a, pred_full, pred_ablated, n_boot, seed)
        res.update(comparison="full minus circular-excluded", dataset="travistorrent", case=project)
        rows.append(res)
        if verbose:
            print(f"  [{project}] full R2={res['r2_a']:.4f} excl R2={res['r2_b']:.4f} "
                  f"diff={res['point_diff']:+.4f} CI=[{res['ci_lo']:+.4f},{res['ci_hi']:+.4f}] "
                  f"({len(excluded)} testduration-derived features excluded)")
    return rows


# ---------------------------------------------------------------------------
# B4. SQuaD: plain vs. static-analysis-enriched defect-fix rate
# ---------------------------------------------------------------------------
def run_squad_enrichment(n_boot: int, seed: int, verbose: bool) -> List[dict]:
    sq_dir = REAL_DATA_DIR / "squad"
    base = load_module("squad_base_pipeline", sq_dir / "run_pipeline_squad.py")

    base_agg = base.load_and_aggregate(verbose=False)
    X_plain, y_plain = base.prepare_features(base_agg)

    # Reimplement run_pipeline_squad_enriched.py's join logic directly (rather than importing
    # that module, which also imports bootstrap_real_world_ci.py at module scope) -- same
    # load_sonarqube_project/load_pmd_project/load_ck_project + left-join logic.
    enriched_mod = load_module("squad_enriched_pipeline", sq_dir / "run_pipeline_squad_enriched.py")
    sq = enriched_mod.load_sonarqube_project()
    pmd = enriched_mod.load_pmd_project()
    ck = enriched_mod.load_ck_project()
    merged = base_agg.merge(sq, on="project_name", how="left") \
                      .merge(pmd, on="project_name", how="left") \
                      .merge(ck, on="project_name", how="left")

    # Correctness check per the task spec: verify row alignment before pairing rather than
    # assuming positional alignment holds. The left join can only change row count/order if
    # sq/pmd/ck have duplicate project_name keys (they are built via groupby, so should not).
    if len(merged) != len(base_agg) or not (merged["project_name"].to_numpy() == base_agg["project_name"].to_numpy()).all():
        if verbose:
            print("  SQuaD: base/enriched row order or count diverged -- aligning on project_name (inner join)")
        merged = base_agg[["project_name"]].merge(merged, on="project_name", how="inner")
        base_agg = base_agg[base_agg["project_name"].isin(merged["project_name"])].reset_index(drop=True)
        merged = merged.set_index("project_name").loc[base_agg["project_name"]].reset_index()
        X_plain, y_plain = base.prepare_features(base_agg)
        aligned_note = "required inner-join alignment on project_name"
    else:
        aligned_note = "naturally aligned (left join preserved base row order/count)"

    X_enriched, y_enriched = base.prepare_features(merged)
    assert len(y_plain) == len(y_enriched), "SQuaD: plain/enriched row count mismatch after alignment"
    assert np.allclose(y_plain.to_numpy(), y_enriched.to_numpy()), \
        "SQuaD: plain/enriched y_true (mean_n_fix) mismatch after alignment"

    if verbose:
        print(f"  SQuaD: plain={X_plain.shape[1]} features, enriched={X_enriched.shape[1]} "
              f"features, n={len(X_plain)} projects ({aligned_note})")

    y_true_a, pred_enriched, idx_enriched = fit_rf_holdout(X_enriched, y_enriched)
    y_true_b, pred_plain, idx_plain = fit_rf_holdout(X_plain, y_plain)
    assert np.array_equal(idx_enriched, idx_plain), "SQuaD: holdout row index mismatch"

    res = bootstrap_r2_diff_ci(y_true_a, pred_enriched, pred_plain, n_boot, seed)
    res.update(comparison="enriched minus plain", dataset="squad", case="defect-fix rate (all projects)",
               alignment=aligned_note)
    if verbose:
        print(f"  [SQuaD] enriched R2={res['r2_a']:.4f} plain R2={res['r2_b']:.4f} "
              f"diff={res['point_diff']:+.4f} CI=[{res['ci_lo']:+.4f},{res['ci_hi']:+.4f}]")
    return [res]


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------
def render_family(title: str, rows: List[dict], col_a: str, col_b: str) -> List[str]:
    lines = [f"## {title}", ""]
    lines.append(f"| Case | n | {col_a} R² | {col_b} R² | Diff (A − B) | 95% CI on diff | Excludes 0? | Interpretation |")
    lines.append("|---|---:|---:|---:|---:|---|:---:|---|")
    for r in rows:
        sig = "yes" if r["excludes_zero"] else "no"
        interp = "significant gap" if r["excludes_zero"] else "noise-level (CI includes 0)"
        lines.append(
            f"| {r['case']} | {r['n']} | {r['r2_a']:.4f} | {r['r2_b']:.4f} | "
            f"{r['point_diff']:+.4f} | [{r['ci_lo']:+.4f}, {r['ci_hi']:+.4f}] | {sig} | {interp} |"
        )
    lines.append("")
    return lines


CACHE_DIR = REAL_DATA_DIR / ".pd_cache"


def save_cache(name: str, rows: List[dict]) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    (CACHE_DIR / f"{name}.json").write_text(json.dumps(rows, indent=2))


def load_cache(name: str) -> List[dict] | None:
    path = CACHE_DIR / f"{name}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-boot", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260810)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--only", choices=["b1", "b2", "b3", "b4", "all"], default="all")
    args = parser.parse_args()

    lines = [
        "# Paired-Difference Bootstrap Confidence Intervals",
        "",
        "Reviewer 2's round-2 comment: reporting two separate confidence intervals for "
        "\"with feature X\" and \"without feature X\" and eyeballing whether they look "
        "different is not the same as testing whether the DIFFERENCE is significant. This "
        "report computes a paired-difference bootstrap CI directly on R²(condition A) − "
        "R²(condition B): the same bootstrap indices are resampled jointly across both "
        f"conditions on each of {args.n_boot} resamples (seed {args.seed}), and the "
        "2.5/97.5 percentile CI is taken on the resulting distribution of differences. "
        "Random Forest throughout (same hyperparameters as `m11_block_bootstrap.py` / "
        "`bootstrap_real_world_ci.py`'s build_models()), held fixed across both conditions "
        "in every comparison so the difference reflects the feature-set change alone.",
        "",
        "**Row-alignment correctness check:** for every comparison below, y_true was "
        "verified identical (same values, same order) between the two conditions before "
        "pairing (see script asserts). SQuaD's plain-vs-enriched comparison is the only one "
        "where this required an explicit check beyond simple column-set difference on a "
        "shared dataframe -- see its row in the table and the accompanying alignment note.",
        "",
    ]

    # Each family's rows are cached to disk (.pd_cache/<name>.json) after computing, and any
    # family NOT recomputed in this invocation (because --only restricted this run to a
    # subset, e.g. for running slow families like B3 in parallel with fast ones) is loaded
    # from its cache instead, so the final report always merges every family that has ever
    # been computed rather than the clobber-on-partial-run bug an earlier version of this
    # script had (a --only run used to overwrite the report with just that family).
    results = {}
    if args.only in ("b1", "all"):
        print("Running B1a: synthetic with-AR vs without-AR...")
        results["b1a"] = run_synthetic_with_without(args.n_boot, args.seed, args.verbose)
        save_cache("b1a", results["b1a"])
        print("Running B1b: Perfherder with-AR vs without-AR...")
        results["b1b"] = run_perfherder_with_without(args.n_boot, args.seed, args.verbose)
        save_cache("b1b", results["b1b"])
    if args.only in ("b2", "all"):
        print("Running B2: GHALogs full vs mean_n_steps-ablated...")
        results["b2"] = run_ghalogs_ablation(args.n_boot, args.seed, args.verbose)
        save_cache("b2", results["b2"])
    if args.only in ("b3", "all"):
        print("Running B3: TravisTorrent full vs circular-excluded...")
        results["b3"] = run_travistorrent_circular(args.n_boot, args.seed, args.verbose)
        save_cache("b3", results["b3"])
    if args.only in ("b4", "all"):
        print("Running B4: SQuaD plain vs enriched...")
        results["b4"] = run_squad_enrichment(args.n_boot, args.seed, args.verbose)
        save_cache("b4", results["b4"])

    for name in ("b1a", "b1b", "b2", "b3", "b4"):
        if name not in results:
            cached = load_cache(name)
            if cached is not None:
                results[name] = cached

    if "b1a" in results:
        lines += render_family("B1a. Synthetic domains: with-AR vs. without-AR", results["b1a"], "With-AR", "Without-AR")
    if "b1b" in results:
        lines += render_family("B1b. Mozilla Perfherder: with-AR vs. without-AR (alert-history-only)", results["b1b"], "With-AR", "Without-AR")
    if "b2" in results:
        lines += render_family("B2. GHALogs: full-feature vs. mean_n_steps-ablated", results["b2"], "Full", "Ablated")
    if "b3" in results:
        lines += render_family("B3. TravisTorrent: full vs. circular-feature-excluded (tr_log_testduration-derived)", results["b3"], "Full", "Excluded")
        small_effect = [r for r in results["b3"] if r["excludes_zero"] and abs(r["point_diff"]) < 0.02]
        if small_effect:
            names = ", ".join(f"{r['case']} ({r['point_diff']:+.4f})" for r in small_effect)
            lines.append(
                f"*Statistical vs. practical significance note:* {names} exclude zero (statistically "
                "significant, given large holdout n) but the point difference itself is negligible or "
                "even in the opposite direction from the other 5 projects (full-feature R² typically "
                "exceeding excluded-feature R² by a large margin). With n in the thousands, a "
                "paired-difference bootstrap CI can exclude zero for a difference too small to be "
                "practically meaningful -- read the point-difference magnitude alongside "
                "significance, not significance alone, for these rows."
            )
            lines.append("")
    if "b4" in results:
        lines += render_family("B4. SQuaD: static-analysis-enriched vs. plain defect-fix rate", results["b4"], "Enriched", "Plain")
        if results["b4"][0].get("alignment"):
            lines.append(f"*Row alignment: {results['b4'][0]['alignment']}.*")
            lines.append("")

    out_path = REAL_DATA_DIR / "PAIRED_DIFFERENCE_BOOTSTRAP_EVIDENCE.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport saved to: {out_path}")


if __name__ == "__main__":
    main()
