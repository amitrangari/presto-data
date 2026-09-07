#!/usr/bin/env python3
"""Calibration diagnostics + sensitivity sweep for the ABC Cloud Provider domain.

Addresses two reviewer-driven gaps for the PRESTO MDPI resubmission:

  Gap A (roadmap #10, partial): calibration diagnostics beyond the existing
      correlation-preservation-tolerance check -- specifically AR(1) recovery,
      correlation-matrix distance (Frobenius norm), and marginal
      goodness-of-fit (KS test) on representative metrics.

  Gap B (roadmap #31): sensitivity of the ABC Cloud domain's headline
      without-AR Random Forest holdout R^2 (0.268, from
      R1_BOOTSTRAP_AND_ABLATION_EVIDENCE.md) to (a) specified correlation
      strength, (b) AR(1) rank-space noise level, (c) AR(1) rho.

This script does NOT modify generate.py, run_pipeline.py, or any file under
src/. It imports them read-only and, for the noise-level sweep only,
monkeypatches TemporalEngine.apply_ar1 in-process (the noise coefficient is
not exposed via config) -- the patch is undone immediately after use and the
file on disk is never touched.

Usage:
    python3.12 calibration_sensitivity_analysis.py

Writes:
    output/calibration_sensitivity/<tag>/abc-cloud-provider/*.csv  (regenerated data)
    output/calibration_sensitivity_results.json                    (raw numbers)
    CALIBRATION_AND_SENSITIVITY_EVIDENCE.md                        (report, this dir)
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import scipy.stats as stats
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import generate as gen  # noqa: E402
import run_pipeline as pipe  # noqa: E402
from src.validator import DataValidator  # noqa: E402
from src.metric_registry import Phase, DistributionType, get_registry  # noqa: E402
from src.temporal_engine import TemporalEngine, _fractional_ranks  # noqa: E402
from src.exporter import PHASE_FILE_MAP  # noqa: E402

PRIMARY_DOMAIN = "abc-cloud-provider"
OUT_ROOT = SCRIPT_DIR / "output" / "calibration_sensitivity"
CONFIG_DIR = SCRIPT_DIR / "config"

# Reverse of generate.py's _PHASE_TO_EXPORTER_KEY
_EXPORTER_TO_PHASE_VALUE = {
    "production": "production",
    "build": "build",
    "code": "code",
    "test": "test",
    "performance": "performance_test",
    "chaos": "chaos",
    "requirements": "requirements",
    "uat": "uat",
}


# ---------------------------------------------------------------------------
# Generation + loading helpers
# ---------------------------------------------------------------------------
def regenerate(domain_config: dict, correlation_config: dict, registry, tag: str) -> Path:
    out_dir = OUT_ROOT / tag
    gen.generate_domain(
        domain_name=PRIMARY_DOMAIN,
        domain_config=domain_config,
        registry=registry,
        correlation_config=correlation_config,
        output_dir=str(out_dir),
        validate=False,
        verbose=False,
    )
    return out_dir / PRIMARY_DOMAIN


def load_phase_data(domain_dir: Path) -> Dict[str, pd.DataFrame]:
    """Load exported per-phase CSVs into a dict keyed by Phase.value."""
    data: Dict[str, pd.DataFrame] = {}
    for exporter_key, fname in PHASE_FILE_MAP.items():
        path = domain_dir / fname
        if not path.exists():
            continue
        df = pd.read_csv(path)
        phase_value = _EXPORTER_TO_PHASE_VALUE[exporter_key]
        data[phase_value] = df
    return data


def flatten_correlation_config(cfg: dict) -> Tuple[List[Tuple[str, str, float]], List[Tuple[str, str, float]]]:
    """Return (applied_pairs, all_specified_pairs).

    applied_pairs: target_correlations + cross_phase_correlations -- the
        pairs that generate.py's _collect_correlation_pairs() actually
        turns into copula input (verified: intra_phase_correlations is a
        dict keyed by SDLC phase, but _collect_correlation_pairs() iterates
        `correlation_config.get(section, [])` for section in
        ["target_correlations", "intra_phase_correlations",
        "cross_phase_correlations"] and does
        `isinstance(item, (list, tuple))` on each element of that iterable.
        For a dict, iterating yields its string keys, which fail the
        isinstance check and are silently skipped. So none of the 8
        intra_phase_correlations blocks are ever applied to the copula's
        correlation matrix -- confirmed by direct count below.)
    all_specified_pairs: applied_pairs + every intra_phase_correlations
        entry, i.e. everything a reader of correlation_templates.yaml would
        believe is enforced.
    """
    target = [tuple(p) for p in cfg.get("target_correlations", [])]
    cross = [tuple(p) for p in cfg.get("cross_phase_correlations", [])]
    intra_flat: List[Tuple[str, str, float]] = []
    for _phase_key, pairs in cfg.get("intra_phase_correlations", {}).items():
        intra_flat.extend(tuple(p) for p in pairs)
    applied = target + cross
    all_specified = applied + intra_flat
    return applied, all_specified


def scale_correlation_config(cfg: dict, factor: float) -> dict:
    """Return a deep copy of cfg with every rho multiplied by *factor*,
    clamped to [-0.95, 0.95] (same clamp generate.py's own
    _precompensate_correlations uses)."""
    out = copy.deepcopy(cfg)

    def _scale_list(pairs):
        scaled = []
        for a, b, rho in pairs:
            new_rho = float(np.clip(rho * factor, -0.95, 0.95))
            scaled.append([a, b, new_rho])
        return scaled

    out["target_correlations"] = _scale_list(out.get("target_correlations", []))
    out["cross_phase_correlations"] = _scale_list(out.get("cross_phase_correlations", []))
    intra = out.get("intra_phase_correlations", {})
    for phase_key in list(intra.keys()):
        intra[phase_key] = _scale_list(intra[phase_key])
    return out


# ---------------------------------------------------------------------------
# RF holdout R^2 (mirrors r1_analysis.py's fit_and_predict_holdout, RF only)
# ---------------------------------------------------------------------------
def rf_holdout_r2(domain_dir: Path, exclude_leakage: bool) -> Dict[str, Any]:
    merged = pipe.load_and_merge(domain_dir)
    engineered = pipe.engineer_features(merged)
    X, y, _leak = pipe.prepare_features(engineered, exclude_leakage=exclude_leakage)

    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    model = pipe.build_models()["Random Forest"]
    model.fit(X_train_s, y_train)
    y_pred = model.predict(X_test_s)
    r2 = float(r2_score(y_test, y_pred))
    return {"r2": r2, "n_features": int(X.shape[1]), "n_holdout": int(len(y_test))}


# ---------------------------------------------------------------------------
# Noise-level monkeypatch for TemporalEngine.apply_ar1
# (in-process only; src/temporal_engine.py is never written to)
# ---------------------------------------------------------------------------
_ORIGINAL_APPLY_AR1 = TemporalEngine.apply_ar1


def _make_noise_scaled_apply_ar1(noise_mult: float):
    """Return a drop-in replacement for TemporalEngine.apply_ar1 whose
    rank-space innovation std is `0.02 * noise_mult * (1 - rho)` instead of
    the hardcoded `0.02 * (1 - rho)` in src/temporal_engine.py. Everything
    else (rank transform, AR(1) recursion, re-ranking) is copied verbatim
    from the original method."""

    def patched(self, data, rho: float = 0.6, metric_cols=None):
        if not 0.0 < rho < 1.0:
            raise ValueError(f"rho must be in (0, 1), got {rho}")
        result = data.copy()
        skip = {"Date", "Release Number"}
        if metric_cols is not None:
            cols = [c for c in metric_cols if c in result.columns and c not in skip]
        else:
            cols = [c for c in result.columns if c not in skip and pd.api.types.is_numeric_dtype(result[c])]
        n = len(result)
        if n < 2:
            return result
        for col in cols:
            values = result[col].to_numpy(dtype=np.float64)
            sorted_vals = np.sort(values)
            ranks = _fractional_ranks(values)
            eps_scale = 0.02 * noise_mult * (1.0 - rho)
            ar_ranks = np.empty_like(ranks)
            ar_ranks[0] = ranks[0]
            for t in range(1, n):
                noise = self.rng.normal(0.0, eps_scale)
                ar_ranks[t] = rho * ar_ranks[t - 1] + (1.0 - rho) * ranks[t] + noise
            ar_ranks = np.clip(ar_ranks, 0.0, 1.0)
            new_order = np.argsort(np.argsort(ar_ranks))
            result[col] = sorted_vals[new_order]
        return result

    return patched


# ---------------------------------------------------------------------------
# Marginal KS spot-check with domain-override-aware reference distributions
# ---------------------------------------------------------------------------
def build_ref_dist(dist_name: str, params: dict):
    if dist_name == "beta":
        return stats.beta(a=params["a"], b=params.get("b"))
    if dist_name == "lognormal":
        return stats.lognorm(s=params["sigma"], scale=np.exp(params["mu"]))
    if dist_name == "poisson":
        return stats.poisson(mu=params["lam"])
    if dist_name == "gamma":
        return stats.gamma(a=params["shape"], scale=params["scale"])
    if dist_name == "negative_binomial":
        return stats.nbinom(n=params["n"], p=params["p"])
    raise ValueError(dist_name)


def normalize_beta(values: np.ndarray, lo: float, hi: float) -> np.ndarray:
    span = hi - lo
    normalized = (values - lo) / span
    return np.clip(normalized, 1e-10, 1.0 - 1e-10)


def ks_spot_check(data: Dict[str, pd.DataFrame], registry, domain_config: dict) -> List[dict]:
    """4 representative metrics spanning distribution families, using the
    domain_profiles.yaml target_overrides where the config file specifies
    one for this domain (even though -- see Part 1 finding -- generate.py
    does not actually apply target_overrides when sampling; this function
    checks generated data against BOTH what the YAML claims and what the
    base registry actually used, to make that gap visible for System
    Uptime specifically)."""
    overrides = domain_config.get("target_overrides", {})
    checks = []

    # 1. System Uptime (%) -- Beta, target metric, ABC Cloud override exists
    target = registry.get_target_metric()
    vals = data["production"]["System Uptime (%)"].dropna().to_numpy(dtype=float)
    base_lo, base_hi = target.bounds
    base_ref = build_ref_dist("beta", target.params)
    ks_base, p_base = stats.kstest(normalize_beta(vals, base_lo, base_hi), base_ref.cdf)
    entry = {
        "metric": "System Uptime (%)", "family": "beta",
        "checked_against": "metric_registry.py base params",
        "params": target.params, "bounds": [base_lo, base_hi],
        "ks_stat": float(ks_base), "p_value": float(p_base), "n": len(vals),
    }
    checks.append(entry)
    if "System Uptime (%)" in overrides:
        ov = overrides["System Uptime (%)"]
        ov_lo, ov_hi = ov["bounds"]
        ov_ref = build_ref_dist(ov["distribution"], ov["params"])
        ks_ov, p_ov = stats.kstest(normalize_beta(vals, ov_lo, ov_hi), ov_ref.cdf)
        checks.append({
            "metric": "System Uptime (%)", "family": "beta",
            "checked_against": "domain_profiles.yaml target_overrides (documented but NOT applied by generate.py)",
            "params": ov["params"], "bounds": [ov_lo, ov_hi],
            "ks_stat": float(ks_ov), "p_value": float(p_ov), "n": len(vals),
        })

    # 2. Mean Time to Recovery (MTTR) (Minutes) -- Lognormal, domain override
    mttr = registry.get_phase_metric("Mean Time to Recovery (MTTR) (Minutes)", Phase.PRODUCTION)
    vals = data["production"]["Mean Time to Recovery (MTTR) (Minutes)"].dropna().to_numpy(dtype=float)
    ref = build_ref_dist("lognormal", mttr.params)
    ks, p = stats.kstest(vals, ref.cdf)
    checks.append({
        "metric": "Mean Time to Recovery (MTTR) (Minutes)", "family": "lognormal",
        "checked_against": "metric_registry.py base params (matches domain override closely: mu 2.8 vs 2.9)",
        "params": mttr.params, "bounds": list(mttr.bounds),
        "ks_stat": float(ks), "p_value": float(p), "n": len(vals),
    })

    # 3. Production Incident Count -- Poisson, domain override lam 12 vs base 8
    vals = data["production"]["Production Incident Count"].dropna().to_numpy(dtype=float)
    base_pic = registry.get_phase_metric("Production Incident Count", Phase.PRODUCTION)
    ref_base = build_ref_dist("poisson", base_pic.params)
    ks_base, p_base = stats.kstest(vals, ref_base.cdf)
    checks.append({
        "metric": "Production Incident Count", "family": "poisson",
        "checked_against": "metric_registry.py base params (lam=8)",
        "params": base_pic.params, "bounds": list(base_pic.bounds),
        "ks_stat": float(ks_base), "p_value": float(p_base), "n": len(vals),
    })
    if "Production Incident Count" in overrides:
        ov = overrides["Production Incident Count"]
        ref_ov = build_ref_dist(ov["distribution"], ov["params"])
        ks_ov, p_ov = stats.kstest(vals, ref_ov.cdf)
        checks.append({
            "metric": "Production Incident Count", "family": "poisson",
            "checked_against": "domain_profiles.yaml target_overrides (documented but NOT applied by generate.py; lam=12)",
            "params": ov["params"], "bounds": ov["bounds"],
            "ks_stat": float(ks_ov), "p_value": float(p_ov), "n": len(vals),
        })

    # 4. Code Smells -- Negative Binomial in the registry, but copula_engine
    # has no negative_binomial builder; generate.py's
    # _translate_distribution_params() silently substitutes a moment-matched
    # Gamma instead (mean/variance matched, not shape). Check against BOTH.
    cs = registry.get_phase_metric("Code Smells", Phase.CODE)
    vals = data["code"]["Code Smells"].dropna().to_numpy(dtype=float)
    ref_nb = build_ref_dist("negative_binomial", cs.params)
    ks_nb, p_nb = stats.kstest(vals, ref_nb.cdf)
    checks.append({
        "metric": "Code Smells", "family": "negative_binomial (as documented in metric_registry.py)",
        "checked_against": "metric_registry.py's stated negative_binomial(n=3.0, p=0.03)",
        "params": cs.params, "bounds": list(cs.bounds),
        "ks_stat": float(ks_nb), "p_value": float(p_nb), "n": len(vals),
        "note": "fraction of non-integer generated values: " + f"{float(np.mean(np.abs(vals - np.round(vals)) > 1e-9)):.3f}",
    })
    n_mean = cs.params["n"] * (1 - cs.params["p"]) / cs.params["p"]
    n_var = cs.params["n"] * (1 - cs.params["p"]) / (cs.params["p"] ** 2)
    gamma_shape = (n_mean ** 2) / n_var
    gamma_scale = n_var / n_mean
    ref_gamma = build_ref_dist("gamma", {"shape": gamma_shape, "scale": gamma_scale})
    ks_g, p_g = stats.kstest(vals, ref_gamma.cdf)
    checks.append({
        "metric": "Code Smells", "family": "gamma (actual copula-engine substitute)",
        "checked_against": f"moment-matched Gamma(shape={gamma_shape:.3f}, scale={gamma_scale:.3f}) "
                            f"used internally by generate.py._translate_distribution_params()",
        "params": {"shape": gamma_shape, "scale": gamma_scale}, "bounds": list(cs.bounds),
        "ks_stat": float(ks_g), "p_value": float(p_g), "n": len(vals),
    })

    return checks


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    registry = get_registry()
    domain_configs = gen.load_domain_configs(CONFIG_DIR)
    domain_config = domain_configs[PRIMARY_DOMAIN]
    correlation_config = gen.load_correlation_config(CONFIG_DIR)
    base_ar1_rho = domain_config["temporal"]["ar1_rho"]

    results: Dict[str, Any] = {}

    # ===== Part 1: calibration diagnostics on the baseline (unmodified) run =====
    print("=== Part 1: calibration diagnostics (baseline, seed=42, unmodified config) ===")
    baseline_dir = regenerate(domain_config, correlation_config, registry, tag="baseline")
    data = load_phase_data(baseline_dir)
    validator = DataValidator(registry)

    # (a) AR(1) recovery
    temporal_results = validator.validate_temporal(data, target_autocorr=base_ar1_rho)
    sys_uptime_vals = data["production"]["System Uptime (%)"].to_numpy(dtype=float)
    sys_uptime_lag1 = DataValidator._compute_lag1_autocorrelation(sys_uptime_vals)
    results["ar1_recovery"] = {
        "target_ar1_rho": base_ar1_rho,
        "system_uptime_lag1_autocorr": float(sys_uptime_lag1),
        "within_paper_stated_range_0.55_0.65": bool(0.55 <= sys_uptime_lag1 <= 0.65),
        "all_metrics_pass_rate": temporal_results["summary"]["pass_rate"],
        "all_metrics_total": temporal_results["summary"]["total"],
        "all_metrics_passed": temporal_results["summary"]["passed"],
        "autocorr_tolerance": DataValidator.AUTOCORR_TOLERANCE,
    }
    print(f"  System Uptime lag-1 autocorr: {sys_uptime_lag1:.4f} (target {base_ar1_rho})")
    print(f"  All-metric AR1 pass rate: {temporal_results['summary']['pass_rate']:.1%} "
          f"({temporal_results['summary']['passed']}/{temporal_results['summary']['total']})")

    # (b) Correlation-matrix distance
    applied_pairs, all_specified_pairs = flatten_correlation_config(correlation_config)
    n_intra_total = sum(len(v) for v in correlation_config.get("intra_phase_correlations", {}).values())
    results["correlation_pair_counts"] = {
        "target_correlations": len(correlation_config.get("target_correlations", [])),
        "cross_phase_correlations": len(correlation_config.get("cross_phase_correlations", [])),
        "intra_phase_correlations_in_yaml": n_intra_total,
        "applied_to_copula": len(applied_pairs),
        "all_specified_in_yaml": len(all_specified_pairs),
    }
    corr_applied = validator.validate_correlations(data, applied_pairs)
    corr_full = validator.validate_correlations(data, all_specified_pairs)
    results["correlation_distance"] = {
        "applied_pairs_only": {
            "n_pairs": corr_applied["summary"]["total"],
            "pass_rate": corr_applied["summary"]["pass_rate"],
            "frobenius_norm": corr_applied["summary"]["frobenius_norm"],
        },
        "all_yaml_specified_pairs": {
            "n_pairs": corr_full["summary"]["total"],
            "pass_rate": corr_full["summary"]["pass_rate"],
            "frobenius_norm": corr_full["summary"]["frobenius_norm"],
        },
    }
    print(f"  Applied-pairs Frobenius norm: {corr_applied['summary']['frobenius_norm']:.4f} "
          f"({corr_applied['summary']['passed']}/{corr_applied['summary']['total']} within tolerance)")
    print(f"  All-YAML-specified-pairs Frobenius norm: {corr_full['summary']['frobenius_norm']:.4f} "
          f"({corr_full['summary']['passed']}/{corr_full['summary']['total']} within tolerance)")

    # (c) Marginal goodness-of-fit: full 164-metric aggregate (base registry, no
    # domain-override awareness -- documented caveat) + 4-metric spot check
    dist_full = validator.validate_distributions(data)
    results["ks_full_registry_aggregate"] = dist_full["summary"]
    print(f"  Full-registry KS pass rate (base params, no domain-override awareness): "
          f"{dist_full['summary']['pass_rate']:.1%} ({dist_full['summary']['passed']}/{dist_full['summary']['total']})")

    spot_checks = ks_spot_check(data, registry, domain_config)
    results["ks_spot_checks"] = spot_checks
    for c in spot_checks:
        print(f"  KS spot-check: {c['metric']} vs {c['checked_against'][:60]}: "
              f"KS={c['ks_stat']:.4f}, p={c['p_value']:.4g}")

    # (d) target_overrides dead-config check (bounds violation test)
    target_ov = domain_config.get("target_overrides", {})
    override_check = []
    for metric_name, ov in target_ov.items():
        if metric_name not in data.get("production", pd.DataFrame()).columns:
            continue
        vals = data["production"][metric_name].dropna().to_numpy(dtype=float)
        ov_lo, ov_hi = ov["bounds"]
        violates_override_bounds = bool(vals.min() < ov_lo - 1e-6 or vals.max() > ov_hi + 1e-6)
        override_check.append({
            "metric": metric_name,
            "override_bounds": [ov_lo, ov_hi],
            "realized_range": [float(vals.min()), float(vals.max())],
            "violates_override_bounds": violates_override_bounds,
        })
    results["target_overrides_applied_check"] = override_check
    print("  target_overrides dead-config check:")
    for c in override_check:
        status = "NOT APPLIED (violates override bounds)" if c["violates_override_bounds"] else "consistent with override"
        print(f"    {c['metric']}: override bounds {c['override_bounds']}, "
              f"realized {c['realized_range']} -> {status}")

    # ===== Part 2: sensitivity sweep =====
    print("\n=== Part 2: sensitivity sweep (RF holdout R^2, without-AR features) ===")
    sweep_rows: List[dict] = []

    # Baseline point (reuse Part 1's regeneration)
    base_metrics = rf_holdout_r2(baseline_dir, exclude_leakage=True)
    base_metrics_withar = rf_holdout_r2(baseline_dir, exclude_leakage=False)
    sweep_rows.append({
        "sweep": "baseline", "param": "ar1_rho=0.60, corr_factor=1.0x, noise_mult=1.0x",
        "value": "baseline",
        "r2_without_ar": base_metrics["r2"], "n_features_without_ar": base_metrics["n_features"],
        "r2_with_ar": base_metrics_withar["r2"],
        "n_holdout": base_metrics["n_holdout"],
        "frobenius_norm_applied_pairs": corr_applied["summary"]["frobenius_norm"],
        "system_uptime_lag1": float(sys_uptime_lag1),
    })
    print(f"  baseline: RF without-AR R^2={base_metrics['r2']:.4f}, with-AR R^2={base_metrics_withar['r2']:.4f}")

    # Sweep A: AR(1) rho
    for rho in [0.50, 0.70]:
        cfg_a = copy.deepcopy(domain_config)
        cfg_a["temporal"]["ar1_rho"] = rho
        tag = f"ar1_rho_{rho}"
        d = regenerate(cfg_a, correlation_config, registry, tag=tag)
        m = rf_holdout_r2(d, exclude_leakage=True)
        data_a = load_phase_data(d)
        lag1 = DataValidator._compute_lag1_autocorrelation(
            data_a["production"]["System Uptime (%)"].to_numpy(dtype=float)
        )
        corr_a = validator.validate_correlations(data_a, applied_pairs)
        sweep_rows.append({
            "sweep": "ar1_rho", "param": "ar1_rho", "value": rho,
            "r2_without_ar": m["r2"], "n_features_without_ar": m["n_features"],
            "r2_with_ar": None, "n_holdout": m["n_holdout"],
            "frobenius_norm_applied_pairs": corr_a["summary"]["frobenius_norm"],
            "system_uptime_lag1": float(lag1),
        })
        print(f"  ar1_rho={rho}: RF without-AR R^2={m['r2']:.4f}, System Uptime lag1={lag1:.4f}")

    # Sweep B: correlation strength multiplier
    for factor in [0.7, 1.3]:
        cfg_b = scale_correlation_config(correlation_config, factor)
        tag = f"corr_factor_{factor}"
        d = regenerate(domain_config, cfg_b, registry, tag=tag)
        m = rf_holdout_r2(d, exclude_leakage=True)
        data_b = load_phase_data(d)
        applied_pairs_b, _ = flatten_correlation_config(cfg_b)
        corr_b_vs_scaled = validator.validate_correlations(data_b, applied_pairs_b)
        corr_b_vs_original = validator.validate_correlations(data_b, applied_pairs)
        lag1_b = DataValidator._compute_lag1_autocorrelation(
            data_b["production"]["System Uptime (%)"].to_numpy(dtype=float)
        )
        sweep_rows.append({
            "sweep": "corr_factor", "param": "correlation_strength_multiplier", "value": factor,
            "r2_without_ar": m["r2"], "n_features_without_ar": m["n_features"],
            "r2_with_ar": None, "n_holdout": m["n_holdout"],
            "frobenius_norm_applied_pairs": corr_b_vs_scaled["summary"]["frobenius_norm"],
            "frobenius_norm_vs_original_target": corr_b_vs_original["summary"]["frobenius_norm"],
            "system_uptime_lag1": float(lag1_b),
        })
        print(f"  corr_factor={factor}x: RF without-AR R^2={m['r2']:.4f}, "
              f"Frobenius(vs scaled target)={corr_b_vs_scaled['summary']['frobenius_norm']:.4f}, "
              f"Frobenius(vs original target)={corr_b_vs_original['summary']['frobenius_norm']:.4f}")

    # Sweep C: AR(1) rank-space noise multiplier (monkeypatch)
    for noise_mult in [0.5, 2.0]:
        TemporalEngine.apply_ar1 = _make_noise_scaled_apply_ar1(noise_mult)
        try:
            tag = f"noise_mult_{noise_mult}"
            d = regenerate(domain_config, correlation_config, registry, tag=tag)
        finally:
            TemporalEngine.apply_ar1 = _ORIGINAL_APPLY_AR1
        m = rf_holdout_r2(d, exclude_leakage=True)
        data_c = load_phase_data(d)
        lag1_c = DataValidator._compute_lag1_autocorrelation(
            data_c["production"]["System Uptime (%)"].to_numpy(dtype=float)
        )
        corr_c = validator.validate_correlations(data_c, applied_pairs)
        sweep_rows.append({
            "sweep": "noise_mult", "param": "ar1_rank_noise_multiplier", "value": noise_mult,
            "r2_without_ar": m["r2"], "n_features_without_ar": m["n_features"],
            "r2_with_ar": None, "n_holdout": m["n_holdout"],
            "frobenius_norm_applied_pairs": corr_c["summary"]["frobenius_norm"],
            "system_uptime_lag1": float(lag1_c),
        })
        print(f"  noise_mult={noise_mult}x: RF without-AR R^2={m['r2']:.4f}, "
              f"System Uptime lag1={lag1_c:.4f}")

    results["sensitivity_sweep"] = sweep_rows

    # ===== Save raw results =====
    out_json = SCRIPT_DIR / "output" / "calibration_sensitivity_results.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nRaw results written to {out_json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
