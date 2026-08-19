#!/usr/bin/env python3
"""PRESTO pipeline applied to real Mozilla Perfherder performance-benchmark data.

Scope note (read before trusting these numbers): unlike the synthetic domains, Perfherder's
per-signature time series has exactly one substantive numeric column (`value`, a real runtime
performance measurement per push) plus mostly-constant metadata (platform, suite, test name are
fixed per signature). There is no analog of PRESTO's 241 SDLC process features here -- no
requirements/code/build/test-quality metrics joined to these pushes. So this script validates only
the *temporal/autoregressive* half of PRESTO's methodology (same feature engineering, same 5-model
comparison, same corrected shift logic as run_pipeline.py) against a genuine real-world runtime
target. It does NOT validate the "SDLC process metrics predict performance" half of the paper's
claim -- that gap is what TravisTorrent (build-duration) and GHALogs (CI timing) partially address,
and what a real 8-phase dataset (named as future work) would fully address.

Usage:
    python run_pipeline_perfherder.py --all
    python run_pipeline_perfherder.py --signature 3777843 --verbose
"""
from __future__ import annotations

import argparse
import csv
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

SCRIPT_DIR = Path(__file__).resolve().parent
TIMESERIES_DIR = SCRIPT_DIR / "timeseries-data"
OUTPUT_DIR = SCRIPT_DIR / "output"

# Diverse, well-populated, genuine runtime-performance signatures (curated: all appear in
# alerts_data.csv, i.e. Mozilla's own performance sheriffs flagged real regressions on them).
SIGNATURES = {
    "espn-loadtime": {
        "id": "3777843",
        "path": "autoland2/autoland2/3777843_timeseries_data.csv",
        "description": "ESPN.com page load time (ms), opt/fission/warm/webrender",
    },
    "instagram-speedindex": {
        "id": "3870280",
        "path": "autoland2/autoland2/3870280_timeseries_data.csv",
        "description": "Instagram Perceptual Speed Index (ms), opt/fission/warm/webrender",
    },
    "nytimes-speedindex": {
        "id": "3778095",
        "path": "autoland2/autoland2/3778095_timeseries_data.csv",
        "description": "NYTimes Perceptual Speed Index (ms), opt/fission/warm/webrender",
    },
}

ROLLING_WINDOWS = [3, 5, 7, 10]
LAG_STEPS = [1, 2, 3, 5]


@dataclass
class ModelResult:
    name: str
    cv_r2_mean: float
    cv_r2_std: float
    holdout_r2: float
    holdout_mae: float
    holdout_rmse: float


def find_signature_file(sig_id: str) -> Optional[Path]:
    matches = list(TIMESERIES_DIR.glob(f"*/*/{sig_id}_timeseries_data.csv"))
    return matches[0] if matches else None


def load_alerts_lookup(alerts_csv: Path) -> dict:
    """Map (signature_id, push_timestamp) -> is_regression flag, for lagged alert-history features."""
    lookup: dict = {}
    with open(alerts_csv, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row.get("signature_id")
            ts = row.get("push_timestamp")
            if sid and ts:
                lookup.setdefault(sid, set()).add(ts[:19])
    return lookup


def load_signature_series(path: Path, sig_id: str, alerts_lookup: dict, verbose: bool = False) -> pd.DataFrame:
    df = pd.read_csv(path, usecols=["push_timestamp", "value", "revision"])
    df["push_timestamp"] = pd.to_datetime(df["push_timestamp"])
    df = df.sort_values("push_timestamp").reset_index(drop=True)
    # collapse duplicate timestamps (multiple retries of the same push) by mean
    df = df.groupby("push_timestamp", as_index=False).agg({"value": "mean", "revision": "first"})
    alert_ts = alerts_lookup.get(sig_id, set())
    df["had_alert"] = df["push_timestamp"].astype(str).str[:19].isin(alert_ts).astype(int)
    if verbose:
        print(f"  Loaded {len(df)} pushes, {df['had_alert'].sum()} flagged as regression alerts")
    return df


def add_rolling_features(df: pd.DataFrame, verbose: bool = False) -> pd.DataFrame:
    """Same fixed logic as the synthetic pipeline: shift by 1 before computing rolling stats
    so no row's rolling feature includes its own value (see R2_LAG_SHIFT_FIX_EVIDENCE.md)."""
    df_out = df.copy()
    shifted = df_out["value"].shift(1)
    added = 0
    for window in ROLLING_WINDOWS:
        roll = shifted.rolling(window=window, min_periods=1)
        df_out[f"value_rolling_mean_{window}"] = roll.mean()
        df_out[f"value_rolling_std_{window}"] = roll.std()
        df_out[f"value_rolling_min_{window}"] = roll.min()
        df_out[f"value_rolling_max_{window}"] = roll.max()
        rolling_mean = df_out[f"value_rolling_mean_{window}"]
        rolling_std = df_out[f"value_rolling_std_{window}"]
        df_out[f"value_rolling_cv_{window}"] = rolling_std / (rolling_mean + 1e-8)
        added += 5
    if verbose:
        print(f"  Rolling features added: {added} columns")
    return df_out


def add_lag_features(df: pd.DataFrame, verbose: bool = False) -> pd.DataFrame:
    """Lag features only -- deliberately excludes diff_k and pct_change_k.

    value_diff_k = value - value_lag_k is an exact algebraic identity: including both
    value_lag_k and value_diff_k as separate features lets any linear model perfectly
    reconstruct value (coef=1 on each) whenever n > p, which is trivially true here
    (thousands of pushes, 32 features) unlike the synthetic pipeline's n<p regime where
    the same redundancy is masked by rank deficiency. This is a distinct, more fundamental
    leakage mode from the R2 rolling-window bug -- see R2_LAG_SHIFT_FIX_EVIDENCE.md addendum.
    """
    df_out = df.copy()
    added = 0
    for lag in LAG_STEPS:
        df_out[f"value_lag_{lag}"] = df_out["value"].shift(lag)
        df_out[f"had_alert_lag_{lag}"] = df_out["had_alert"].shift(lag)
        added += 2
    if verbose:
        print(f"  Lag features added: {added} columns")
    return df_out


def engineer_features(df: pd.DataFrame, verbose: bool = False) -> pd.DataFrame:
    df_out = add_rolling_features(df, verbose=verbose)
    df_out = add_lag_features(df_out, verbose=verbose)
    df_out["push_gap_hours"] = df_out["push_timestamp"].diff().dt.total_seconds() / 3600.0
    df_out = df_out.ffill().bfill()
    for col in df_out.select_dtypes(include=[np.number]).columns:
        if df_out[col].isna().any():
            df_out[col] = df_out[col].fillna(df_out[col].mean())
    df_out = df_out.replace([np.inf, -np.inf], np.nan)
    for col in df_out.select_dtypes(include=[np.number]).columns:
        if df_out[col].isna().any():
            df_out[col] = df_out[col].fillna(df_out[col].mean())
    return df_out


def prepare_features(df: pd.DataFrame, exclude_target_derived: bool):
    y = df["value"].copy()
    exclude = {"push_timestamp", "revision", "value", "had_alert"}
    feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in exclude]
    target_derived = [c for c in feature_cols if c.startswith("value_")]
    if exclude_target_derived:
        feature_cols = [c for c in feature_cols if c not in target_derived]
    X = df[feature_cols].copy()
    return X, y, target_derived


def train_and_evaluate(X: pd.DataFrame, y: pd.Series) -> List[ModelResult]:
    n = len(X)
    split_idx = int(n * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    models = {
        "Linear Regression": LinearRegression(),
        "Ridge Regression": Ridge(alpha=1.0),
        "Lasso Regression": Lasso(alpha=1.0),
        "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(random_state=42),
    }

    n_splits = min(5, max(2, split_idx // 20))
    tscv = TimeSeriesSplit(n_splits=n_splits)
    results = []
    for name, model in models.items():
        cv_scores = []
        for tr_idx, val_idx in tscv.split(X_train_s):
            model.fit(X_train_s[tr_idx], y_train.iloc[tr_idx])
            pred = model.predict(X_train_s[val_idx])
            cv_scores.append(r2_score(y_train.iloc[val_idx], pred))
        model.fit(X_train_s, y_train)
        pred_test = model.predict(X_test_s)
        results.append(ModelResult(
            name=name,
            cv_r2_mean=float(np.mean(cv_scores)),
            cv_r2_std=float(np.std(cv_scores)),
            holdout_r2=float(r2_score(y_test, pred_test)),
            holdout_mae=float(mean_absolute_error(y_test, pred_test)),
            holdout_rmse=float(np.sqrt(mean_squared_error(y_test, pred_test))),
        ))
    return results


def run_signature_pipeline(name: str, spec: dict, alerts_lookup: dict, verbose: bool = False):
    print(f"\n{'='*70}\n  Signature: {name} ({spec['description']})\n{'='*70}")
    path = TIMESERIES_DIR / spec["path"]
    if not path.exists():
        found = find_signature_file(spec["id"])
        if found is None:
            print(f"  ERROR: file not found for signature {spec['id']}")
            return None
        path = found

    df = load_signature_series(path, spec["id"], alerts_lookup, verbose=verbose)
    df_eng = engineer_features(df, verbose=verbose)

    X_with, y, target_derived = prepare_features(df_eng, exclude_target_derived=False)
    X_without, _, _ = prepare_features(df_eng, exclude_target_derived=True)

    print(f"  Samples: {len(df_eng)}, target-derived (AR) features: {len(target_derived)}, "
          f"process-side features (had_alert + push_gap only): {X_without.shape[1]}")

    print("\n  --- WITH target-derived (AR) features ---")
    results_with = train_and_evaluate(X_with, y)
    for r in results_with:
        print(f"    {r.name:25s} CV R2={r.cv_r2_mean:.4f}+/-{r.cv_r2_std:.4f}  "
              f"Holdout R2={r.holdout_r2:.4f}  MAE={r.holdout_mae:.4f}  RMSE={r.holdout_rmse:.4f}")

    print("\n  --- WITHOUT target-derived features (alert-history + push-gap only) ---")
    results_without = train_and_evaluate(X_without, y)
    for r in results_without:
        print(f"    {r.name:25s} CV R2={r.cv_r2_mean:.4f}+/-{r.cv_r2_std:.4f}  "
              f"Holdout R2={r.holdout_r2:.4f}  MAE={r.holdout_mae:.4f}  RMSE={r.holdout_rmse:.4f}")

    OUTPUT_DIR.mkdir(exist_ok=True)
    report_path = OUTPUT_DIR / f"{name}_ml_results.md"
    with open(report_path, "w") as f:
        f.write(f"# ML Pipeline Results: {name} (Mozilla Perfherder, real data)\n\n")
        f.write(f"**Signature:** {spec['description']} (signature_id={spec['id']})\n\n")
        f.write("## Dataset Characteristics\n\n| Property | Value |\n|---|---|\n")
        f.write(f"| Samples (pushes) | {len(df_eng)} |\n")
        f.write(f"| Target-derived (AR) features | {len(target_derived)} |\n")
        f.write(f"| Process-side features (non-AR) | {X_without.shape[1]} |\n")
        f.write(f"| Target mean | {y.mean():.4f} |\n| Target std | {y.std():.4f} |\n\n")
        f.write("## Model Performance (WITH target-derived AR features)\n\n")
        f.write("| Model | CV R2 (mean +/- std) | Holdout R2 | Holdout MAE | Holdout RMSE |\n|---|---|---|---|---|\n")
        for r in sorted(results_with, key=lambda r: -r.holdout_r2):
            f.write(f"| {r.name} | {r.cv_r2_mean:.4f} +/- {r.cv_r2_std:.4f} | {r.holdout_r2:.4f} | {r.holdout_mae:.4f} | {r.holdout_rmse:.4f} |\n")
        f.write("\n## Model Performance (WITHOUT target-derived features -- alert-history + push-gap only)\n\n")
        f.write("| Model | CV R2 (mean +/- std) | Holdout R2 | Holdout MAE | Holdout RMSE |\n|---|---|---|---|---|\n")
        for r in sorted(results_without, key=lambda r: -r.holdout_r2):
            f.write(f"| {r.name} | {r.cv_r2_mean:.4f} +/- {r.cv_r2_std:.4f} | {r.holdout_r2:.4f} | {r.holdout_mae:.4f} | {r.holdout_rmse:.4f} |\n")
        f.write("\n## Notes\n\n")
        f.write("- Real Mozilla Perfherder data (CC-BY-4.0), not synthetic.\n")
        f.write("- Rolling/lag features use the corrected shift (see ../../code/synthetic_data_generator/R2_LAG_SHIFT_FIX_EVIDENCE.md) -- no same-row leakage.\n")
        f.write("- 'WITHOUT target-derived' features are alert-history + inter-push time gap only -- Perfherder has no SDLC process-metric analog to PRESTO's 241 synthetic features, so this is a much weaker non-AR feature set than the synthetic domains have.\n")
        f.write("- 80/20 temporal split, 5-fold (or fewer, data permitting) TimeSeriesSplit CV, StandardScaler fit on train only.\n")
    print(f"\n  Report saved to: {report_path}")
    return results_with, results_without


def main():
    parser = argparse.ArgumentParser(description="Run PRESTO pipeline on real Perfherder signatures.")
    parser.add_argument("--signature", choices=list(SIGNATURES.keys()), help="Run a single signature.")
    parser.add_argument("--all", action="store_true", help="Run all signatures.")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    alerts_lookup = load_alerts_lookup(SCRIPT_DIR / "alerts_data.csv")

    targets = SIGNATURES.keys() if (args.all or not args.signature) else [args.signature]
    summary = []
    for name in targets:
        res = run_signature_pipeline(name, SIGNATURES[name], alerts_lookup, verbose=args.verbose)
        if res:
            results_with, _ = res
            best = max(results_with, key=lambda r: r.holdout_r2)
            summary.append((name, best.name, best.holdout_r2))

    print(f"\n{'='*70}\n  CROSS-SIGNATURE SUMMARY (best model, WITH AR features)\n{'='*70}")
    for name, model, r2 in summary:
        print(f"  {name:25s} Best: {model:20s} R2={r2:.4f}")


if __name__ == "__main__":
    main()
