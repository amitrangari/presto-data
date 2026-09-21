#!/usr/bin/env python3
"""M9 (consensus review, Phase 2): ablate the near-tautological "System Availability
(%)" feature.

Section 4.5 currently only *flags* System Availability (%) as a caveat (14.9% RF
feature importance, semantically adjacent to the target System Uptime (%), copula
correlation 0.68) rather than actually testing what happens if it's removed. M9 asks
for the real ablation: rerun with the feature dropped and report the R² and
feature-importance-rank consequences, honestly, on all 3 domains and both the
with-AR and without-AR conditions.

Usage: python m9_system_availability_ablation.py [--verbose]
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

import run_pipeline as rp  # noqa: E402

DATA_ROOT = Path("/Volumes/4TB/research-data-and-code/zenado/presto-data/synthetic-data-projects")
ABLATED_FEATURE = "System Availability (%)"


def run_domain(domain: str, verbose: bool = False) -> dict:
    domain_dir = DATA_ROOT / domain
    df = rp.load_and_merge(domain_dir, verbose=False)
    df_eng = rp.engineer_features(df, verbose=False)

    out = {"domain": domain}
    for cond_name, exclude_leakage in (("with_AR", False), ("without_AR", True)):
        X, y, _ = rp.prepare_features(df_eng, exclude_leakage=exclude_leakage)

        # Also drop every engineered feature derived FROM System Availability
        # (rolling/lag/cross-phase composites), not just the raw column, so the
        # ablation is complete rather than leaving a derivative proxy behind.
        derived_cols = [c for c in X.columns if c.startswith(ABLATED_FEATURE)]
        cols_to_drop = list({ABLATED_FEATURE, *derived_cols} & set(X.columns))
        if verbose:
            print(f"  [{domain}/{cond_name}] dropping {len(cols_to_drop)} column(s): {cols_to_drop}")

        X_full = X
        X_ablated = X.drop(columns=cols_to_drop)

        results_full, fi_full = rp.train_and_evaluate(X_full, y, verbose=False)
        results_ablated, fi_ablated = rp.train_and_evaluate(X_ablated, y, verbose=False)

        rf_full = next(r for r in results_full if r.name == "Random Forest")
        rf_ablated = next(r for r in results_ablated if r.name == "Random Forest")

        # Rank of System Availability (%) itself in the full-feature RF importances
        # (fi_full is computed on whichever condition's X -- here without_AR's
        # fi is the "clean" one used elsewhere in the paper).
        rank = None
        importance_pct = None
        if fi_full is not None and ABLATED_FEATURE in fi_full["feature"].values:
            fi_sorted = fi_full.sort_values("importance", ascending=False).reset_index(drop=True)
            rank = int(fi_sorted.index[fi_sorted["feature"] == ABLATED_FEATURE][0]) + 1
            importance_pct = float(
                fi_sorted.loc[fi_sorted["feature"] == ABLATED_FEATURE, "importance"].iloc[0]
            ) * 100

        # New top feature after ablation, for context.
        new_top_feature = None
        new_top_importance = None
        if fi_ablated is not None and len(fi_ablated) > 0:
            top_row = fi_ablated.sort_values("importance", ascending=False).iloc[0]
            new_top_feature = top_row["feature"]
            new_top_importance = float(top_row["importance"]) * 100

        out[cond_name] = {
            "n_features_full": X_full.shape[1],
            "n_features_ablated": X_ablated.shape[1],
            "cols_dropped": cols_to_drop,
            "rf_holdout_r2_full": rf_full.holdout_r2,
            "rf_holdout_r2_ablated": rf_ablated.holdout_r2,
            "sysavail_rank_in_full": rank,
            "sysavail_importance_pct_in_full": importance_pct,
            "new_top_feature_after_ablation": new_top_feature,
            "new_top_importance_pct": new_top_importance,
        }
        if verbose:
            print(
                f"    RF holdout R2: full={rf_full.holdout_r2:.4f}  "
                f"ablated={rf_ablated.holdout_r2:.4f}  "
                f"(Δ={rf_ablated.holdout_r2 - rf_full.holdout_r2:+.4f})"
            )
            print(
                f"    System Availability (%) was rank {rank} "
                f"({importance_pct:.1f}%) in full feature set" if rank else
                "    System Availability (%) not in feature set for this condition"
            )
            print(
                f"    New top feature after ablation: {new_top_feature} "
                f"({new_top_importance:.1f}%)" if new_top_feature else ""
            )

    return out


def format_report(all_results: list[dict]) -> str:
    lines = ["# M9 — System Availability (%) Ablation", ""]
    lines.append(
        f"Protocol: for each domain and each of the with-AR / without-AR feature "
        f"conditions, remove `{ABLATED_FEATURE}` and every engineered feature derived "
        f"from it (rolling/lag/cross-phase composites), retrain and re-evaluate Random "
        f"Forest (the model whose feature importances flagged this feature in Section "
        f"4.5) with unchanged fixed hyperparameters, and compare holdout R² and the "
        f"new top feature to the full-feature-set baseline."
    )
    lines.append("")
    for res in all_results:
        domain = res["domain"]
        lines.append(f"## {domain}")
        lines.append("")
        lines.append(
            "| Condition | Features (full → ablated) | RF Holdout R² (full) | "
            "RF Holdout R² (ablated) | Δ | Sys. Avail. rank (full) | New top feature (ablated) |"
        )
        lines.append("|---|---|---:|---:|---:|---|---|")
        for cond_name in ("with_AR", "without_AR"):
            r = res[cond_name]
            delta = r["rf_holdout_r2_ablated"] - r["rf_holdout_r2_full"]
            rank_str = (
                f"#{r['sysavail_rank_in_full']} ({r['sysavail_importance_pct_in_full']:.1f}%)"
                if r["sysavail_rank_in_full"] else "n/a"
            )
            top_str = (
                f"{r['new_top_feature_after_ablation']} ({r['new_top_importance_pct']:.1f}%)"
                if r["new_top_feature_after_ablation"] else "n/a"
            )
            lines.append(
                f"| {cond_name} | {r['n_features_full']} → {r['n_features_ablated']} | "
                f"{r['rf_holdout_r2_full']:.4f} | {r['rf_holdout_r2_ablated']:.4f} | "
                f"{delta:+.4f} | {rank_str} | {top_str} |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    verbose = "--verbose" in sys.argv
    all_results = []
    for domain in rp.ALL_DOMAINS:
        print(f"\n=== {domain} ===")
        all_results.append(run_domain(domain, verbose=verbose))

    report = format_report(all_results)
    out_path = _SCRIPT_DIR / "M9_SYSTEM_AVAILABILITY_ABLATION_EVIDENCE.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"\nReport saved to: {out_path}")
    print(report)


if __name__ == "__main__":
    main()
