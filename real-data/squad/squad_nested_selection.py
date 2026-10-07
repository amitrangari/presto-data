#!/usr/bin/env python3
"""SQuaD nested model selection (PRESTO v4 revision, Reviewer 2 round 3, Phase 2b).

Reuses run_pipeline_squad.py (defect-fix rate), run_pipeline_squad_vuln.py (CVE-count), and
run_pipeline_squad_enriched.py (static-analysis-enriched defect-fix rate) data loading/feature
prep, plus nested_cv_harness.py's nested_select() (imported directly), to replace the paper's
existing fixed-hyperparameter "best of 5, selected by holdout R2" protocol for all three SQuaD
variants (Section 4.2.4 and its sub-sections). All three are small (~408 projects), so the
harness's default (unshrunk) grids are used throughout.

Usage: python squad_nested_selection.py [--verbose]
"""
from __future__ import annotations

import importlib.util
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
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.preprocessing import StandardScaler

from nested_cv_harness import nested_select  # noqa: E402


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


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


CLS_MAP = {"Linear Regression": LinearRegression, "Ridge Regression": Ridge,
           "Lasso Regression": Lasso, "Random Forest": RandomForestRegressor,
           "Gradient Boosting": GradientBoostingRegressor}


def refit_selected_and_ci(X, y, result, n_boot=2000, seed=20260919):
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    cls = CLS_MAP[result["selected_model"]]
    model = cls(**result["selected_params"])
    model.fit(X_train_s, y_train)
    y_pred = model.predict(X_test_s)
    lo, hi = bootstrap_r2_ci(y_test.to_numpy(), y_pred, n_boot=n_boot, seed=seed)
    return lo, hi


def run_case(label, X, y, verbose=False):
    t0 = time.time()
    result = nested_select(X, y, verbose=verbose)
    ci_lo, ci_hi = refit_selected_and_ci(X, y, result)
    elapsed = time.time() - t0
    result.update(label=label, ci_lo=ci_lo, ci_hi=ci_hi,
                   ci_excludes_zero=bool(ci_lo > 0 or ci_hi < 0), elapsed_sec=elapsed)
    print(f"  [{label}] nested={result['selected_model']} holdout R2={result['selected_holdout_r2']:.4f} "
          f"CI=[{ci_lo:.4f},{ci_hi:.4f}] old-protocol={result['old_protocol_selected_model']} "
          f"holdout R2={result['old_protocol_holdout_r2']:.4f} ({elapsed:.1f}s)")
    return result


def render_row(name, r, pub_model, pub_r2):
    sig = "yes" if r["ci_excludes_zero"] else "no"
    return (f"| {name} | {r['selected_model']} | {r['selected_inner_cv_r2']:.4f} | "
            f"{r['selected_holdout_r2']:.4f} | [{r['ci_lo']:.4f}, {r['ci_hi']:.4f}] | {sig} | "
            f"{r['old_protocol_selected_model']} | {r['old_protocol_holdout_r2']:.4f} | "
            f"{pub_model} ({pub_r2:.4f}) |")


def main():
    verbose = "--verbose" in sys.argv
    lines = ["# SQuaD Nested Model Selection (PRESTO v4 revision, Phase 2b)", ""]
    lines.append(
        "Replaces the paper's existing fixed-hyperparameter \"best of 5, selected by holdout R2\" "
        "protocol (Section 4.2.4) with nested_cv_harness.py's nested_select() for all three SQuaD "
        "variants: defect-fix rate, CVE-count, and the static-analysis-enriched defect-fix rate. "
        "A 95% pairs/case bootstrap CI (2000 resamples, seed 20260919) is added for each "
        "nested-selected model. All three (~408 projects) use the harness's default grids.\n"
    )
    rows = ["| Variant | Nested Model | Inner CV R2 | Nested Holdout R2 | 95% CI | Sig? | "
            "Old-Protocol Model | Old-Protocol Holdout R2 | Published (main_mdpi_v3) |",
            "|---|---|---:|---:|---|:---:|---|---:|---|"]

    print("=== SQuaD defect-fix rate ===")
    squad = load_module("run_pipeline_squad", _THIS_DIR / "run_pipeline_squad.py")
    agg = squad.load_and_aggregate(verbose=verbose)
    X, y = squad.prepare_features(agg)
    print(f"  n={len(X)}, features={X.shape[1]}")
    r_defect = run_case("defect_fix", X, y, verbose)
    rows.append(render_row("Defect-fix rate", r_defect, "Random Forest", 0.402))

    print("\n=== SQuaD CVE-count ===")
    squad_vuln = load_module("run_pipeline_squad_vuln", _THIS_DIR / "run_pipeline_squad_vuln.py")
    agg_vuln = squad_vuln.load_and_aggregate(verbose=verbose)
    X_vuln, y_vuln = squad_vuln.prepare_features(agg_vuln)
    print(f"  n={len(X_vuln)}, features={X_vuln.shape[1]}")
    r_cve = run_case("cve_count", X_vuln, y_vuln, verbose)
    rows.append(render_row("CVE-count (log1p)", r_cve, "Random Forest", 0.245))

    print("\n=== SQuaD enriched (static-analysis) defect-fix rate ===")
    squad_enr = load_module("run_pipeline_squad_enriched", _THIS_DIR / "run_pipeline_squad_enriched.py")
    base_agg = squad.load_and_aggregate(verbose=False)
    sq_df = squad_enr.load_sonarqube_project()
    pmd_df = squad_enr.load_pmd_project()
    ck_df = squad_enr.load_ck_project()
    merged = base_agg.merge(sq_df, on="project_name", how="left") \
                      .merge(pmd_df, on="project_name", how="left") \
                      .merge(ck_df, on="project_name", how="left")
    X_enr, y_enr = squad.prepare_features(merged)
    print(f"  n={len(X_enr)}, features={X_enr.shape[1]}")
    r_enriched = run_case("enriched_defect_fix", X_enr, y_enr, verbose)
    rows.append(render_row("Enriched defect-fix rate", r_enriched, "Random Forest", 0.483))

    lines.append("\n".join(rows))

    all_rows = [r_defect, r_cve, r_enriched]
    n_sig = sum(1 for r in all_rows if r["ci_excludes_zero"])
    n_swap = sum(1 for r in all_rows if r["selected_model"] != r["old_protocol_selected_model"])
    lines.append(f"\n## Summary\n\n- {n_sig}/3 nested-selected variants have a bootstrap CI "
                  f"excluding zero.\n- Nested selection picks a different model than the old "
                  f"holdout-selection protocol in {n_swap}/3 variants.\n")

    out_path = _THIS_DIR / "SQUAD_NESTED_SELECTION_EVIDENCE.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nEvidence file written to: {out_path}")


if __name__ == "__main__":
    main()
