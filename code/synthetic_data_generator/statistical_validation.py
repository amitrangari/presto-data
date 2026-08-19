#!/usr/bin/env python3
"""Recompute the statistical-validation suite (baselines, multi-seed stability, residual
diagnostics, permutation test) against the R2-fixed pipeline and freshly regenerated data.

Mirrors the methodology described in the manuscript's Statistical Validation section, but must be
rerun because: (1) the rolling-window shift bug is now fixed, and (2) the underlying synthetic data
was regenerated under a different numpy/scipy environment than originally produced the submitted
numbers (see R2_LAG_SHIFT_FIX_EVIDENCE.md addendum 2) -- so the old baseline/permutation/stability
figures no longer correspond to any dataset that currently exists.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_pipeline as rp  # noqa: E402

DOMAIN = "abc-cloud-provider"
SEEDS = [42, 123, 456, 789, 2024]


def load_prepared(domain: str):
    domain_dir = rp.OUTPUT_DIR / domain
    df = rp.load_and_merge(domain_dir)
    df_eng = rp.engineer_features(df)
    X, y, leakage_cols = rp.prepare_features(df_eng, exclude_leakage=True)
    return X, y


def split_scale(X, y, test_frac=0.2):
    n = len(X)
    split = int(n * (1 - test_frac))
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    scaler = StandardScaler()
    return scaler.fit_transform(X_train), scaler.transform(X_test), y_train, y_test


def main():
    X, y = load_prepared(DOMAIN)
    X_train_s, X_test_s, y_train, y_test = split_scale(X, y)
    n_train = len(y_train)

    print(f"Domain: {DOMAIN}  n_train={n_train}  n_test={len(y_test)}  p={X.shape[1]}\n")

    # --- Baseline comparison ---
    gb = GradientBoostingRegressor(n_estimators=100, max_depth=6, learning_rate=0.1,
                                    min_samples_split=5, min_samples_leaf=2, random_state=42)
    gb.fit(X_train_s, y_train)
    pred_gb = gb.predict(X_test_s)
    gb_r2 = r2_score(y_test, pred_gb)
    gb_mae = mean_absolute_error(y_test, pred_gb)
    gb_rmse = np.sqrt(mean_squared_error(y_test, pred_gb))

    naive_mean_pred = np.full(len(y_test), y_train.mean())
    naive_mean_r2 = r2_score(y_test, naive_mean_pred)
    naive_mean_mae = mean_absolute_error(y_test, naive_mean_pred)
    naive_mean_rmse = np.sqrt(mean_squared_error(y_test, naive_mean_pred))

    persistence_pred = np.concatenate([[y_train.iloc[-1]], y_test.values[:-1]])
    persistence_r2 = r2_score(y_test, persistence_pred)
    persistence_mae = mean_absolute_error(y_test, persistence_pred)
    persistence_rmse = np.sqrt(mean_squared_error(y_test, persistence_pred))

    dora_cols = [c for c in X.columns if any(k in c for k in
                 ["Deployment Frequency", "Change Failure Rate", "Mean Time to Recovery", "Lead Time"])]
    dora_cols = dora_cols[:4] if dora_cols else list(X.columns[:4])
    scaler_dora = StandardScaler()
    Xd_train = scaler_dora.fit_transform(X[dora_cols].iloc[:n_train])
    Xd_test = scaler_dora.transform(X[dora_cols].iloc[n_train:])
    gb_dora = GradientBoostingRegressor(n_estimators=100, max_depth=6, learning_rate=0.1,
                                         min_samples_split=5, min_samples_leaf=2, random_state=42)
    gb_dora.fit(Xd_train, y_train)
    pred_dora = gb_dora.predict(Xd_test)
    dora_r2 = r2_score(y_test, pred_dora)
    dora_mae = mean_absolute_error(y_test, pred_dora)
    dora_rmse = np.sqrt(mean_squared_error(y_test, pred_dora))

    print("## Baseline comparison (Gradient Boosting, 241 SDLC-only features)")
    print(f"{'Model':30s} {'R2':>8s} {'MAE':>8s} {'RMSE':>8s}")
    print(f"{'Gradient Boosting (241 feat)':30s} {gb_r2:8.3f} {gb_mae:8.3f} {gb_rmse:8.3f}")
    print(f"{'Naive Mean':30s} {naive_mean_r2:8.3f} {naive_mean_mae:8.3f} {naive_mean_rmse:8.3f}")
    print(f"{'Persistence (Last Value)':30s} {persistence_r2:8.3f} {persistence_mae:8.3f} {persistence_rmse:8.3f}")
    print(f"{'DORA-Only GB (4 metrics)':30s} {dora_r2:8.3f} {dora_mae:8.3f} {dora_rmse:8.3f}")

    # --- Multi-seed stability ---
    print("\n## Multi-seed stability")
    for model_name, cls, kwargs in [
        ("Gradient Boosting", GradientBoostingRegressor,
         dict(n_estimators=100, max_depth=6, learning_rate=0.1, min_samples_split=5, min_samples_leaf=2)),
        ("Random Forest", RandomForestRegressor,
         dict(n_estimators=100, max_depth=10, min_samples_split=5, min_samples_leaf=2)),
    ]:
        r2s = []
        for seed in SEEDS:
            m = cls(random_state=seed, **kwargs)
            m.fit(X_train_s, y_train)
            r2s.append(r2_score(y_test, m.predict(X_test_s)))
        print(f"{model_name:20s} seeds={SEEDS} R2s={[round(r, 3) for r in r2s]} "
              f"mean={np.mean(r2s):.3f} std={np.std(r2s):.3f}")

    # --- Residual diagnostics (GB, seed 42) ---
    residuals = y_test.values - pred_gb
    diffs = np.diff(residuals)
    dw = np.sum(diffs ** 2) / np.sum(residuals ** 2)
    shapiro_stat, shapiro_p = stats.shapiro(residuals)

    def acf(x, lag):
        x = x - x.mean()
        return np.sum(x[:-lag] * x[lag:]) / np.sum(x ** 2) if lag > 0 else 1.0

    n = len(residuals)
    bound = 1.96 / np.sqrt(n)
    acf_vals = [round(acf(residuals, lag), 3) for lag in range(1, 6)]
    print(f"\n## Residual diagnostics (GB, seed 42, n_test={n})")
    print(f"Durbin-Watson: {dw:.3f}")
    print(f"Shapiro-Wilk: stat={shapiro_stat:.4f} p={shapiro_p:.6f}")
    print(f"ACF lags 1-5: {acf_vals}  (95% bound +/- {bound:.3f})")

    # --- Permutation test ---
    print("\n## Permutation test (1000 permutations, GB, TimeSeriesSplit n=5)")
    rng = np.random.RandomState(42)
    n_perm = 1000
    tscv = TimeSeriesSplit(n_splits=5)

    def cv_r2_for(y_arr):
        scores = []
        for tr_idx, val_idx in tscv.split(X_train_s):
            m = GradientBoostingRegressor(n_estimators=100, max_depth=6, learning_rate=0.1,
                                           min_samples_split=5, min_samples_leaf=2, random_state=42)
            m.fit(X_train_s[tr_idx], y_arr[tr_idx])
            scores.append(r2_score(y_arr[val_idx], m.predict(X_train_s[val_idx])))
        return np.mean(scores)

    observed = cv_r2_for(y_train.values)
    null_scores = []
    for i in range(n_perm):
        y_perm = rng.permutation(y_train.values)
        null_scores.append(cv_r2_for(y_perm))
        if (i + 1) % 200 == 0:
            print(f"  ... {i+1}/{n_perm}", file=sys.stderr)
    null_scores = np.array(null_scores)
    p_value = (np.sum(null_scores >= observed) + 1) / (n_perm + 1)
    print(f"Observed CV R2: {observed:.4f}")
    print(f"Null distribution: mean={null_scores.mean():.4f} std={null_scores.std():.4f}")
    print(f"Permutation p-value: {p_value:.4f}")


if __name__ == "__main__":
    main()
