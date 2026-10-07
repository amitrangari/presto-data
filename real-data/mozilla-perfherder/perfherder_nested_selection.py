#!/usr/bin/env python3
"""Mozilla Perfherder nested model selection (PRESTO v4 revision, Reviewer 2 round 3, Phase 2b).

Reuses run_pipeline_perfherder.py's and run_pipeline_perfherder_bugs.py's data loading/feature
engineering functions and nested_cv_harness.py's nested_select() (imported directly) to replace
the paper's existing fixed-hyperparameter "best of 5, selected by holdout R2" protocol for:
  - 3 main signatures (ESPN, Instagram, NYTimes) x 2 conditions (with-AR / alert-history-only)
  - 2 bug-enriched signatures (osx-cross installer size, osx-aarch64 build metric) x 2 conditions
    (alert-flag-only / bug-metadata-enriched)

All 5 datasets here are small (thousands of pushes) so the harness's default grids are used
unmodified -- no shrink needed, unlike TravisTorrent's larger projects.

Usage: python perfherder_nested_selection.py [--verbose]
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
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.preprocessing import StandardScaler

import run_pipeline_perfherder as ph  # noqa: E402
import run_pipeline_perfherder_bugs as phb  # noqa: E402
from nested_cv_harness import nested_select  # noqa: E402


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


# OLD published numbers, main_mdpi_v3 Section 4.2.2
OLD_MAIN = {
    "espn-loadtime": {"with_AR": ("Ridge Regression", 0.574), "without_AR": (None, -3.191)},
    "instagram-speedindex": {"with_AR": ("Ridge Regression", 0.913), "without_AR": (None, -0.367)},
    "nytimes-speedindex": {"with_AR": ("Ridge Regression", 0.167), "without_AR": (None, -3.563)},
}
OLD_BUGS = {
    "installer-size-osx-cross": {"alert_only": (None, -56.06), "bug_enriched": ("Lasso Regression", -2.56)},
    "build-metric-osx-aarch64": {"alert_only": (None, -41.31), "bug_enriched": ("Lasso Regression", -1.57)},
}


def render_table(rows, old_map, cond_a_key, cond_b_key, cond_a_label, cond_b_label):
    out = ["| Signature | Condition | Nested Model | Inner CV R2 | Nested Holdout R2 | 95% CI | "
           "Sig? | Old-Protocol Model | Old-Protocol Holdout R2 | Published (main_mdpi_v3) |",
           "|---|---|---|---:|---:|---|:---:|---|---:|---:|"]
    for name, results in rows.items():
        for cond_key, cond_label in [(cond_a_key, cond_a_label), (cond_b_key, cond_b_label)]:
            r = results[cond_key]
            sig = "yes" if r["ci_excludes_zero"] else "no"
            pub_model, pub_r2 = old_map.get(name, {}).get(cond_key, (None, float("nan")))
            out.append(
                f"| {name} | {cond_label} | {r['selected_model']} | {r['selected_inner_cv_r2']:.4f} | "
                f"{r['selected_holdout_r2']:.4f} | [{r['ci_lo']:.4f}, {r['ci_hi']:.4f}] | {sig} | "
                f"{r['old_protocol_selected_model']} | {r['old_protocol_holdout_r2']:.4f} | {pub_r2:.4f} |"
            )
    return "\n".join(out)


def main():
    verbose = "--verbose" in sys.argv
    lines = ["# Mozilla Perfherder Nested Model Selection (PRESTO v4 revision, Phase 2b)", ""]
    lines.append(
        "Replaces the paper's existing fixed-hyperparameter \"best of 5, selected by holdout R2\" "
        "protocol (Section 4.2.2) with nested_cv_harness.py's nested_select() for the 3 main "
        "signatures (with-AR / alert-history-only) and the 2 bug-enriched signatures "
        "(alert-flag-only / bug-metadata-enriched). A 95% pairs/case bootstrap CI (2000 resamples, "
        "seed 20260919) is added for each nested-selected model. All 5 datasets are small enough "
        "(thousands of pushes) to use the harness's default (unshrunk) grids.\n"
    )

    print("=== Main signatures (ESPN, Instagram, NYTimes) ===")
    alerts_lookup = ph.load_alerts_lookup(ph.SCRIPT_DIR / "alerts_data.csv")
    main_results = {}
    for name, spec in ph.SIGNATURES.items():
        print(f"\n--- {name} ---")
        path = ph.TIMESERIES_DIR / spec["path"]
        if not path.exists():
            found = ph.find_signature_file(spec["id"])
            if found is None:
                print(f"  ERROR: file not found for {spec['id']}, skipping")
                continue
            path = found
        df = ph.load_signature_series(path, spec["id"], alerts_lookup, verbose=verbose)
        df_eng = ph.engineer_features(df, verbose=verbose)
        X_with, y, target_derived = ph.prepare_features(df_eng, exclude_target_derived=False)
        X_without, _, _ = ph.prepare_features(df_eng, exclude_target_derived=True)
        print(f"  n={len(df_eng)}, with-AR features={X_with.shape[1]}, without-AR features={X_without.shape[1]}")
        main_results[name] = {
            "with_AR": run_case("with_AR", X_with, y, verbose),
            "without_AR": run_case("without_AR", X_without, y, verbose),
        }

    print("\n=== Bug-enriched signatures (osx-cross, osx-aarch64) ===")
    bug_meta = phb.load_bug_metadata()
    bug_results = {}
    for name, spec in phb.SIGNATURES.items():
        print(f"\n--- {name} ---")
        path = phb.SCRIPT_DIR / spec["path"]
        if not path.exists():
            print(f"  ERROR: file not found at {path}, skipping")
            continue
        df = phb.load_signature_series(path, bug_meta, verbose=verbose)
        df_eng = phb.add_lag_and_history_features(df, verbose=verbose)
        y, X_alert_only, X_bug_enriched = phb.prepare_feature_sets(df_eng)
        print(f"  n={len(df_eng)}, alert-only features={X_alert_only.shape[1]}, "
              f"bug-enriched features={X_bug_enriched.shape[1]}")
        bug_results[name] = {
            "alert_only": run_case("alert_only", X_alert_only, y, verbose),
            "bug_enriched": run_case("bug_enriched", X_bug_enriched, y, verbose),
        }

    lines.append("## Main signatures\n")
    lines.append(render_table(main_results, OLD_MAIN, "with_AR", "without_AR", "with-AR", "without-AR (alert-history only)"))
    lines.append("\n## Bug-enriched signatures\n")
    lines.append(render_table(bug_results, OLD_BUGS, "alert_only", "bug_enriched", "alert-flag-only", "bug-metadata-enriched"))

    all_rows = [r for res in main_results.values() for r in res.values()] + \
               [r for res in bug_results.values() for r in res.values()]
    n_sig = sum(1 for r in all_rows if r["ci_excludes_zero"])
    n_swap = sum(1 for r in all_rows if r["selected_model"] != r["old_protocol_selected_model"])
    lines.append(f"\n## Summary\n\n- {n_sig}/{len(all_rows)} nested-selected cases have a bootstrap "
                  f"CI excluding zero.\n- Nested selection picks a different model than the old "
                  f"holdout-selection protocol in {n_swap}/{len(all_rows)} cases.\n")

    out_path = _THIS_DIR / "PERFHERDER_NESTED_SELECTION_EVIDENCE.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nEvidence file written to: {out_path}")


if __name__ == "__main__":
    main()
