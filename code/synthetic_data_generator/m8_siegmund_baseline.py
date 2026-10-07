#!/usr/bin/env python3
"""M8 (consensus review, Phase 2): reimplement a genuine prior-method baseline.

The paper's existing baseline table (Section 4.4) compares the full 241-feature
SDLC model against naive mean, last-value persistence, and a 4-metric DORA-only
model -- none of which is a method from the literature the paper itself cites.
M8 asks for at least one reimplemented prior method as a real competitive
baseline.

We reimplement the core *methodology* of Siegmund et al. 2015 ("Performance-
Influence Models for Highly Configurable Systems", ESEC/FSE), adapted from their
domain (configuration options -> runtime performance) to ours (SDLC process
metrics -> production uptime): a **performance-influence model** built by forward
stepwise OLS regression, adding one main-effect term at a time by the largest
F-test/p-value improvement, stopping when no candidate term is significant at
p<0.05, then testing pairwise interactions among the selected main effects and
adding any that are themselves significant at p<0.05. This is Siegmund et al.'s
own procedure (Section 3.2-3.3 of their paper): start from an empty model, grow
by significance, allow limited-order interaction terms -- not a generic stepwise
regression borrowed from elsewhere.

Run on the primary domain (ABC Cloud Provider), without-AR features, same 80/20
temporal split and StandardScaler-on-train-only protocol as every other model in
this paper, so the result is directly comparable to Table `baselines`.

Usage: python m8_siegmund_baseline.py [--verbose] [--all-domains]
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

import run_pipeline as rp  # noqa: E402

DATA_ROOT = Path("/Volumes/4TB/research-data-and-code/zenado/presto-data/synthetic-data-projects")
SIG_LEVEL = 0.05
MAX_MAIN_EFFECTS = 15  # guard against unbounded growth given n=136 training rows


def _ols_pvalue_of_new_term(y: np.ndarray, X_cols: list[np.ndarray], candidate: np.ndarray) -> tuple[float, float]:
    """Fit OLS with X_cols + candidate, return (p-value of candidate, model R2)."""
    X = np.column_stack(X_cols + [candidate]) if X_cols else candidate.reshape(-1, 1)
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()
    return float(model.pvalues[-1]), float(model.rsquared)


def forward_stepwise_main_effects(X: pd.DataFrame, y: pd.Series, verbose: bool = False) -> list[str]:
    """Siegmund-style forward selection: add the most significant remaining term
    each round, stop when no candidate is significant at SIG_LEVEL."""
    selected: list[str] = []
    selected_arrays: list[np.ndarray] = []
    remaining = list(X.columns)
    y_arr = y.to_numpy()

    while remaining and len(selected) < MAX_MAIN_EFFECTS:
        best_p, best_col, best_r2 = 1.1, None, -np.inf
        for col in remaining:
            candidate = X[col].to_numpy()
            try:
                p, r2 = _ols_pvalue_of_new_term(y_arr, selected_arrays, candidate)
            except Exception:
                continue
            if p < best_p:
                best_p, best_col, best_r2 = p, col, r2
        if best_col is None or best_p >= SIG_LEVEL:
            break
        selected.append(best_col)
        selected_arrays.append(X[best_col].to_numpy())
        remaining.remove(best_col)
        if verbose:
            print(f"      + {best_col} (p={best_p:.4f}, model R2={best_r2:.4f})")

    return selected


def add_significant_interactions(X: pd.DataFrame, y: pd.Series, main_effects: list[str],
                                   verbose: bool = False) -> list[tuple[str, str]]:
    """Test all pairwise interactions among selected main effects; keep those
    significant at SIG_LEVEL when added to the full main-effects model."""
    y_arr = y.to_numpy()
    base_cols = [X[c].to_numpy() for c in main_effects]
    interactions: list[tuple[str, str]] = []

    for i in range(len(main_effects)):
        for j in range(i + 1, len(main_effects)):
            a, b = main_effects[i], main_effects[j]
            term = X[a].to_numpy() * X[b].to_numpy()
            try:
                p, _ = _ols_pvalue_of_new_term(y_arr, base_cols, term)
            except Exception:
                continue
            if p < SIG_LEVEL:
                interactions.append((a, b))
                if verbose:
                    print(f"      interaction {a} x {b} significant (p={p:.4f})")

    return interactions


def fit_and_evaluate(domain: str, verbose: bool = False) -> dict:
    domain_dir = DATA_ROOT / domain
    df = rp.load_and_merge(domain_dir, verbose=False)
    df_eng = rp.engineer_features(df, verbose=False)
    X_all, y, _ = rp.prepare_features(df_eng, exclude_leakage=True)  # without-AR, matches Table `baselines`

    split_idx = int(len(X_all) * 0.8)
    X_train, X_test = X_all.iloc[:split_idx], X_all.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    scaler = StandardScaler()
    X_train_s = pd.DataFrame(scaler.fit_transform(X_train), columns=X_train.columns, index=X_train.index)
    X_test_s = pd.DataFrame(scaler.transform(X_test), columns=X_test.columns, index=X_test.index)

    if verbose:
        print(f"  [{domain}] forward stepwise main-effect selection ({X_train_s.shape[1]} candidates) ...")
    main_effects = forward_stepwise_main_effects(X_train_s, y_train, verbose=verbose)

    if verbose:
        print(f"  [{domain}] testing pairwise interactions among {len(main_effects)} selected main effects ...")
    interactions = add_significant_interactions(X_train_s, y_train, main_effects, verbose=verbose)

    # Build final design matrix: selected main effects + significant interaction terms.
    def build_design(X: pd.DataFrame) -> np.ndarray:
        cols = [X[c].to_numpy() for c in main_effects]
        cols += [X[a].to_numpy() * X[b].to_numpy() for a, b in interactions]
        if not cols:
            return np.ones((len(X), 1))
        return sm.add_constant(np.column_stack(cols))

    X_train_design = build_design(X_train_s)
    X_test_design = build_design(X_test_s)

    final_model = sm.OLS(y_train.to_numpy(), X_train_design).fit()
    y_pred = final_model.predict(X_test_design)

    holdout_r2 = float(r2_score(y_test, y_pred))
    holdout_mae = float(mean_absolute_error(y_test, y_pred))
    holdout_rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))

    return {
        "domain": domain,
        "n_main_effects": len(main_effects),
        "main_effects": main_effects,
        "n_interactions": len(interactions),
        "interactions": interactions,
        "train_r2": float(final_model.rsquared),
        "train_adj_r2": float(final_model.rsquared_adj),
        "holdout_r2": holdout_r2,
        "holdout_mae": holdout_mae,
        "holdout_rmse": holdout_rmse,
    }


def format_report(all_results: list[dict]) -> str:
    lines = ["# M8 — Siegmund-Style Performance-Influence Model Baseline", ""]
    lines.append(
        "Reimplements the core methodology of Siegmund et al. 2015 (ESEC/FSE) -- forward "
        "stepwise OLS with significance-gated term addition (p<0.05), followed by "
        "significance-gated pairwise interaction terms among the selected main effects -- "
        "adapted from their domain (configuration options) to ours (SDLC process metrics), "
        "without-AR features, same 80/20 temporal split and StandardScaler-on-train-only "
        "protocol as every other result in this paper."
    )
    lines.append("")
    lines.append("| Domain | Main effects | Interactions | Train R² | Train adj. R² | Holdout R² | Holdout MAE | Holdout RMSE |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for r in all_results:
        lines.append(
            f"| {r['domain']} | {r['n_main_effects']} | {r['n_interactions']} | "
            f"{r['train_r2']:.4f} | {r['train_adj_r2']:.4f} | {r['holdout_r2']:.4f} | "
            f"{r['holdout_mae']:.4f} | {r['holdout_rmse']:.4f} |"
        )
    lines.append("")
    for r in all_results:
        lines.append(f"## {r['domain']}")
        lines.append("")
        lines.append(f"Selected main effects ({r['n_main_effects']}): " + ", ".join(r["main_effects"]))
        lines.append("")
        if r["interactions"]:
            lines.append("Significant interactions: " + ", ".join(f"{a} x {b}" for a, b in r["interactions"]))
        else:
            lines.append("No pairwise interaction terms reached significance.")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    verbose = "--verbose" in sys.argv
    all_domains = "--all-domains" in sys.argv
    domains = rp.ALL_DOMAINS if all_domains else ["abc-cloud-provider"]

    all_results = []
    for domain in domains:
        print(f"\n=== {domain} ===")
        all_results.append(fit_and_evaluate(domain, verbose=verbose))

    report = format_report(all_results)
    out_path = _SCRIPT_DIR / "M8_SIEGMUND_BASELINE_RESULTS.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"\nReport saved to: {out_path}")
    print(report)


if __name__ == "__main__":
    main()
