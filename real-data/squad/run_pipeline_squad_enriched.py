#!/usr/bin/env python3
"""SQuaD defect-fix-rate prediction, enriched with real static-analysis code-quality features.

The paper's existing SQuaD validation (run_pipeline_squad.py) uses only process_metrics.csv
(LOC, churn, commit-author count, release age) -- it has no Code-quality-phase features at all,
unlike PRESTO's synthetic domains. The 2026-08-14 full SQuaD data extraction makes three raw
per-file/per-issue static-analysis dumps available (SonarQube, PMD, CK), aggregated to
project-release granularity via DuckDB (RAW_DATA/aggregated/*.csv, see
aggregate_raw_static_analysis.py). This script rolls those up to project level (mean across
releases, matching the existing >=5-releases aggregation unit) and joins them onto the existing
feature set, to test whether genuine code-quality signal changes the paper's finding that SQuaD's
defect-fix-rate R^2=0.402 (Random Forest) is not statistically significant (95% CI [-0.245, 0.748]).

Usage: python run_pipeline_squad_enriched.py --verbose
"""
from __future__ import annotations

import importlib.util
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

SCRIPT_DIR = Path(__file__).resolve().parent
RAW = SCRIPT_DIR / "RAW_DATA"
AGG = RAW / "aggregated"

spec = importlib.util.spec_from_file_location("run_pipeline_squad", SCRIPT_DIR / "run_pipeline_squad.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

boot_spec = importlib.util.spec_from_file_location(
    "bootstrap_real_world_ci", SCRIPT_DIR.parent / "bootstrap_real_world_ci.py"
)
boot = importlib.util.module_from_spec(boot_spec)
boot_spec.loader.exec_module(boot)


def load_sonarqube_project() -> pd.DataFrame:
    df = pd.read_csv(AGG / "sonarqube_project_release_measures.csv")
    measure_cols = [c for c in df.columns if c.startswith("measures_")]
    for c in measure_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    agg = df.groupby("project_name")[measure_cols].mean().add_prefix("sq_mean_")
    return agg.reset_index()


def load_pmd_project() -> pd.DataFrame:
    df = pd.read_csv(AGG / "pmd_project_release_counts.csv")
    count_cols = ["n_violations", "n_priority1", "n_priority2", "n_priority3",
                  "n_files_with_violations", "n_distinct_rules"]
    for c in count_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    agg = df.groupby("project_name")[count_cols].mean().add_prefix("pmd_mean_")
    return agg.reset_index()


def load_ck_project() -> pd.DataFrame:
    df = pd.read_csv(AGG / "ck_project_release_avg.csv")
    metric_cols = ["avg_wmc", "avg_cbo", "avg_dit", "avg_class_loc", "avg_lcom", "avg_rfc", "avg_noc"]
    for c in metric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    agg = df.groupby("project_name")[metric_cols].mean().add_prefix("ck_mean_")
    return agg.reset_index()


def main() -> None:
    verbose = "--verbose" in sys.argv

    base_agg = base.load_and_aggregate(verbose=verbose)
    print(f"Base process-metrics aggregation: {len(base_agg)} projects")

    sq = load_sonarqube_project()
    pmd = load_pmd_project()
    ck = load_ck_project()
    print(f"SonarQube project rollup: {len(sq)} projects")
    print(f"PMD project rollup: {len(pmd)} projects")
    print(f"CK project rollup: {len(ck)} projects")

    merged = base_agg.merge(sq, on="project_name", how="left") \
                      .merge(pmd, on="project_name", how="left") \
                      .merge(ck, on="project_name", how="left")

    n_with_sq = merged["sq_mean_measures_bugs"].notna().sum() if "sq_mean_measures_bugs" in merged else 0
    n_with_pmd = merged["pmd_mean_n_violations"].notna().sum() if "pmd_mean_n_violations" in merged else 0
    n_with_ck = merged["ck_mean_avg_wmc"].notna().sum() if "ck_mean_avg_wmc" in merged else 0
    print(f"Of {len(merged)} base projects: {n_with_sq} have SonarQube coverage, "
          f"{n_with_pmd} have PMD coverage, {n_with_ck} have CK coverage")

    X, y = base.prepare_features(merged)
    print(f"Enriched feature set: {X.shape[1]} features (base was {base.prepare_features(base_agg)[0].shape[1]})")

    results, feature_names = base.train_and_evaluate(X, y)
    print("\n--- Enriched Model Performance ---")
    for r in sorted(results, key=lambda r: -r["holdout_r2"]):
        print(f"  {r['name']:20s} CV R2={r['cv_r2_mean']:.4f}+/-{r['cv_r2_std']:.4f}  "
              f"Holdout R2={r['holdout_r2']:.4f}  MAE={r['holdout_mae']:.2f}  RMSE={r['holdout_rmse']:.2f}")

    best = max(results, key=lambda r: r["holdout_r2"])
    print(f"\nBest model: {best['name']} (Holdout R2={best['holdout_r2']:.4f})")

    # Bootstrap CI on the best model's holdout predictions, same procedure as the rest of the paper.
    n = len(X)
    split = int(n * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    models = base.build_models()
    fitted = {}
    for name, model in models.items():
        model.fit(X_train_s, y_train)
        fitted[name] = model

    boot_rows = []
    for name, model in fitted.items():
        pred = model.predict(X_test_s)
        r2 = float(r2_score(y_test, pred))
        ci_lo, ci_hi, _median = boot.bootstrap_r2_ci(y_test.values, pred, n_boot=2000, seed=20260810)
        excl = not (ci_lo <= 0 <= ci_hi)
        boot_rows.append({"model": name, "holdout_r2": r2, "ci_lo": ci_lo, "ci_hi": ci_hi, "excludes_zero": excl})
        print(f"  {name:20s} R2={r2:.4f}  95% CI=[{ci_lo:.4f}, {ci_hi:.4f}]  excludes_zero={excl}")

    importances = sorted(zip(feature_names, fitted["Random Forest"].feature_importances_), key=lambda t: -t[1])

    report_path = SCRIPT_DIR / "SQUAD_ENRICHED_STATIC_ANALYSIS_RESULTS.md"
    with open(report_path, "w") as f:
        f.write("# SQuaD Defect-Fix Rate, Enriched with Real Static-Analysis Features\n\n")
        f.write(
            "Extends the paper's SQuaD defect-fix-rate validation (Section 4.2.4) with real "
            "code-quality features from SonarQube, PMD, and CK -- aggregated from the "
            "2026-08-14 full SQuaD data extraction's raw per-file/per-issue dumps (up to 678GB "
            "each) via DuckDB streaming aggregation, then rolled up to project level (mean "
            "across releases) and joined onto the existing process-metrics feature set. Tests "
            "whether genuine Code-phase static-analysis signal changes the paper's finding that "
            "the existing (process-metrics-only) result, Random Forest R2=0.402, "
            "95% CI [-0.245, 0.748], is not statistically significant.\n\n"
        )
        f.write("## Coverage\n\n| Source | Projects covered (of {}) |\n|---|---|\n".format(len(merged)))
        f.write(f"| SonarQube | {n_with_sq} |\n")
        f.write(f"| PMD | {n_with_pmd} |\n")
        f.write(f"| CK | {n_with_ck} |\n\n")
        f.write(f"Enriched feature count: {X.shape[1]} (base process-metrics-only: "
                f"{base.prepare_features(base_agg)[0].shape[1]})\n\n")
        f.write("## Model Performance (80/20 split, same order as base pipeline)\n\n")
        f.write("| Model | CV R2 (mean +/- std) | Holdout R2 | MAE | RMSE |\n|---|---|---|---|---|\n")
        for r in sorted(results, key=lambda r: -r["holdout_r2"]):
            f.write(f"| {r['name']} | {r['cv_r2_mean']:.4f} +/- {r['cv_r2_std']:.4f} | "
                    f"{r['holdout_r2']:.4f} | {r['holdout_mae']:.2f} | {r['holdout_rmse']:.2f} |\n")
        f.write("\n## Bootstrap 95% CI (2000-resample pairs/case bootstrap, seed 20260810)\n\n")
        f.write("| Model | Holdout R2 | 95% CI | Excludes zero |\n|---|---|---|---|\n")
        for row in sorted(boot_rows, key=lambda r: -r["holdout_r2"]):
            f.write(f"| {row['model']} | {row['holdout_r2']:.4f} | "
                    f"[{row['ci_lo']:.4f}, {row['ci_hi']:.4f}] | {row['excludes_zero']} |\n")
        f.write("\n## Feature Importances (Random Forest, top 20)\n\n| Rank | Feature | Importance |\n|---|---|---|\n")
        for i, (name, imp) in enumerate(importances[:20], 1):
            f.write(f"| {i} | {name} | {imp:.4f} |\n")
        f.write("\n## Comparison to Paper's Existing Result\n\n")
        f.write("| | Existing (process-metrics only) | Enriched (+ SonarQube/PMD/CK) |\n|---|---|---|\n")
        f.write(f"| Best model | Random Forest | {best['name']} |\n")
        f.write(f"| Holdout R2 | 0.4023 | {best['holdout_r2']:.4f} |\n")
        rf_boot = next((r for r in boot_rows if r["model"] == "Random Forest"), None)
        if rf_boot:
            f.write(f"| RF 95% CI | [-0.2453, 0.7478] | [{rf_boot['ci_lo']:.4f}, {rf_boot['ci_hi']:.4f}] |\n")
            f.write(f"| RF excludes zero (significant) | No | {rf_boot['excludes_zero']} |\n")
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
