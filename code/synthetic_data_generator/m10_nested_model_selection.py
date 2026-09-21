#!/usr/bin/env python3
"""M10 (v4 revision, Reviewer 2 round 3): nested model selection, all synthetic domains.

Replaces the paper's current fixed-holdout "best of 5 models" selection (Section 3.2.4's
Model-Selection Rule, currently: pick whichever model scores highest ON the holdout, then
report that same holdout score) with the nested-CV harness in `nested_cv_harness.py`: model
and hyperparameter selection happens entirely within the outer 80% training partition via
TimeSeriesSplit(5); the untouched 20% outer holdout is scored exactly once, by the
already-selected configuration.

Runs all 3 synthetic domains x 2 AR-conditions (6 total nested selections), and reports the
new nested-selected numbers side by side with the paper's existing published fixed-holdout-
selection numbers so the change is auditable rather than a silent swap.

Usage: python m10_nested_model_selection.py [--verbose]
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

import run_pipeline as rp  # noqa: E402
from nested_cv_harness import nested_select  # noqa: E402

DATA_ROOT = Path("/Volumes/4TB/research-data-and-code/zenado/presto-data/synthetic-data-projects")

# Paper's existing published fixed-holdout-selection numbers (main_mdpi_v3), for direct
# old-vs-new comparison. Source: Table `model_perf_with`/`model_perf_without` (Section 4.1.2)
# and Table `cross_domain` (Section 4.1.10).
OLD_PUBLISHED = {
    ("abc-cloud-provider", "with_AR"): {"model": "Random Forest", "holdout_r2": 0.914},
    ("abc-cloud-provider", "without_AR"): {"model": "Random Forest", "holdout_r2": 0.107},
    ("card-payment-processor", "without_AR"): {"model": "Random Forest", "holdout_r2": 0.475},
    ("xyz-sales-force", "without_AR"): {"model": "Gradient Boosting", "holdout_r2": 0.490},
}


def run_domain(domain: str, verbose: bool = False) -> dict:
    domain_dir = DATA_ROOT / domain
    df = rp.load_and_merge(domain_dir, verbose=False)
    df_eng = rp.engineer_features(df, verbose=False)

    X_with, y, _ = rp.prepare_features(df_eng, exclude_leakage=False)
    X_without, _, _ = rp.prepare_features(df_eng, exclude_leakage=True)

    out = {"domain": domain}
    for cond_name, X in (("with_AR", X_with), ("without_AR", X_without)):
        if verbose:
            print(f"  [{domain}] {cond_name} ...")
        t0 = time.time()
        result = nested_select(X, y, verbose=verbose)
        elapsed = time.time() - t0
        result["elapsed_sec"] = elapsed
        out[cond_name] = result
        if verbose:
            print(
                f"    -> nested-selected: {result['selected_model']} "
                f"(inner CV R2={result['selected_inner_cv_r2']:.4f}, "
                f"holdout R2={result['selected_holdout_r2']:.4f})  "
                f"[old-protocol would pick: {result['old_protocol_selected_model']} "
                f"holdout R2={result['old_protocol_holdout_r2']:.4f}]  "
                f"({elapsed:.1f}s)"
            )
    return out


def format_report(all_results: list[dict]) -> str:
    lines = ["# M10 — Nested Model Selection, All Synthetic Domains", ""]
    lines.append(
        "Full-algorithm nested cross-validation (see `nested_cv_harness.py` for the protocol "
        "and hyperparameter grids), replacing the paper's fixed-holdout \"best of 5 models\" "
        "selection with a genuinely nested one: model and hyperparameter choice happens entirely "
        "within the outer 80% training partition via `TimeSeriesSplit(5)`; the outer 20% holdout "
        "is scored exactly once, by the already-selected configuration. This supersedes the "
        "selection *mechanism* in Section 3.2.4's Model-Selection Rule; it does not change the "
        "underlying data or feature engineering."
    )
    lines.append("")
    lines.append(
        "**Old-vs-new comparison** is against `main_mdpi_v3`'s already-published fixed-holdout-"
        "selection numbers (Tables `model_perf_with`/`model_perf_without`, `cross_domain`)."
    )
    lines.append("")

    for res in all_results:
        domain = res["domain"]
        lines.append(f"## {domain}")
        lines.append("")
        for cond_name in ("with_AR", "without_AR"):
            if cond_name not in res:
                continue
            r = res[cond_name]
            lines.append(f"### {cond_name}")
            lines.append("")
            lines.append(
                "| Model | Inner CV R² | Best hyperparameters | Holdout R² (all candidates, "
                "for reference only — not used for selection) | Holdout MAE | Holdout RMSE |"
            )
            lines.append("|---|---:|---|---:|---:|---:|")
            for name, c in sorted(
                r["per_candidate"].items(), key=lambda kv: kv[1]["inner_cv_r2"], reverse=True
            ):
                marker = " **(nested-selected)**" if name == r["selected_model"] else ""
                params_str = ", ".join(f"{k}={v}" for k, v in c["best_params"].items())
                lines.append(
                    f"| {name}{marker} | {c['inner_cv_r2']:.4f} | {params_str} | "
                    f"{c['holdout_r2']:.4f} | {c['holdout_mae']:.4f} | {c['holdout_rmse']:.4f} |"
                )
            lines.append("")
            old = OLD_PUBLISHED.get((domain, cond_name))
            lines.append(
                f"**Nested-selected:** {r['selected_model']}, holdout R² = "
                f"{r['selected_holdout_r2']:.4f} (selected by inner CV R² = "
                f"{r['selected_inner_cv_r2']:.4f}, never by holdout score)."
            )
            lines.append(
                f"**Old fixed-holdout-selection protocol on this same split** would pick: "
                f"{r['old_protocol_selected_model']}, holdout R² = "
                f"{r['old_protocol_holdout_r2']:.4f}."
            )
            if old is not None:
                lines.append(
                    f"**Paper's already-published number** (main_mdpi_v3): {old['model']}, "
                    f"holdout R² = {old['holdout_r2']:.3f}."
                )
                same_model = r["selected_model"] == old["model"]
                delta = r["selected_holdout_r2"] - old["holdout_r2"]
                lines.append(
                    f"**Verdict:** nested selection picks {'the same' if same_model else 'a DIFFERENT'} "
                    f"model as the published result"
                    + (f" ({r['selected_model']} vs. {old['model']})" if not same_model else "")
                    + f"; nested holdout R² differs from the published figure by {delta:+.4f}."
                )
            lines.append(f"(n_train={r['n_train']}, n_test={r['n_test']}, n_features={r['n_features']}, "
                          f"wall time {r['elapsed_sec']:.1f}s)")
            lines.append("")
    return "\n".join(lines)


def main() -> None:
    verbose = "--verbose" in sys.argv
    all_results = []
    for domain in rp.ALL_DOMAINS:
        print(f"\n=== {domain} ===")
        all_results.append(run_domain(domain, verbose=verbose))

    report = format_report(all_results)
    out_path = _SCRIPT_DIR / "NESTED_MODEL_SELECTION_EVIDENCE.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"\nReport saved to: {out_path}")


if __name__ == "__main__":
    main()
