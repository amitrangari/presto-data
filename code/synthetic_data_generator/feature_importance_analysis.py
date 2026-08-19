#!/usr/bin/env python3
"""Permutation importance (matching the manuscript's stated methodology, unlike the Gini-based
feature_importances_ that run_pipeline.py's ml_results.md actually reports) + phase-level
aggregation, for the ABC Cloud Provider domain without AR features.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
import run_pipeline as rp  # noqa: E402
from metric_registry import get_registry  # noqa: E402

DOMAIN = "abc-cloud-provider"


def phase_for_feature(feat_name: str, name_to_phase: dict) -> str:
    if feat_name in name_to_phase:
        return name_to_phase[feat_name]
    # derived features: strip suffixes to find the parent metric name
    for suffix_marker in ["_rolling_", "_lag_", "_pct_change_", "_diff_"]:
        if suffix_marker in feat_name:
            base = feat_name.split(suffix_marker)[0]
            if base in name_to_phase:
                return name_to_phase[base]
    if feat_name in ("stability_score", "quality_score"):
        return "Cross-Phase"
    return "Unknown"


def main():
    registry = get_registry()
    name_to_phase = {m.name: m.phase.value for m in registry.get_all_metrics()}

    domain_dir = rp.OUTPUT_DIR / DOMAIN
    df = rp.load_and_merge(domain_dir)
    df_eng = rp.engineer_features(df)
    X, y, _ = rp.prepare_features(df_eng, exclude_leakage=True)

    n = len(X)
    split = int(n * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    rf = RandomForestRegressor(n_estimators=100, max_depth=10, min_samples_split=5,
                                min_samples_leaf=2, random_state=42)
    rf.fit(X_train_s, y_train)

    result = permutation_importance(rf, X_test_s, y_test, n_repeats=10, random_state=42, n_jobs=-1)
    importances = result.importances_mean
    # normalize to sum to 1 (like the original manuscript's percentage framing), clip negatives to 0
    imp_clipped = np.clip(importances, 0, None)
    imp_norm = imp_clipped / imp_clipped.sum()

    order = np.argsort(-imp_norm)
    feat_names = X.columns.tolist()

    print("## Top 20 features (permutation importance, normalized)")
    phase_totals: dict = {}
    for rank, idx in enumerate(order[:20], 1):
        fname = feat_names[idx]
        phase = phase_for_feature(fname, name_to_phase)
        print(f"{rank:3d}  {fname:50s} {imp_norm[idx]*100:6.2f}%  [{phase}]")

    print("\n## Phase-level aggregation (all features)")
    for idx in order:
        fname = feat_names[idx]
        phase = phase_for_feature(fname, name_to_phase)
        phase_totals[phase] = phase_totals.get(phase, 0.0) + imp_norm[idx]
    for phase, total in sorted(phase_totals.items(), key=lambda t: -t[1]):
        print(f"{phase:20s} {total*100:6.2f}%")
    print(f"\nSum check: {sum(phase_totals.values())*100:.2f}% (should be ~100%)")

    unknown_feats = [feat_names[idx] for idx in order if phase_for_feature(feat_names[idx], name_to_phase) == "Unknown"]
    print(f"\nFeatures with unresolved phase mapping ({len(unknown_feats)}): {unknown_feats[:10]}")


if __name__ == "__main__":
    main()
