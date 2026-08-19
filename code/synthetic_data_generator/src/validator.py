"""Statistical validation of synthetic SDLC datasets.

Validates generated data against distributional, correlational, temporal,
and boundary expectations. The paper claims:

    "Kolmogorov-Smirnov tests confirmed distributional similarity
     (p > 0.05) for 92% of metrics."

This module provides the machinery to verify and reproduce that claim.

Validation categories:
    1. Distribution validation (KS tests against theoretical CDFs)
    2. Correlation validation (empirical vs target Pearson correlations)
    3. Temporal validation (lag-1 autocorrelation structure)
    4. Bound validation (hard limits from metric definitions)

Dependencies: numpy, scipy, pandas only.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import scipy.stats as stats


# ---------------------------------------------------------------------------
# Import project types
# ---------------------------------------------------------------------------

from .metric_registry import (
    DistributionType,
    MetricDefinition,
    MetricRegistry,
    Phase,
)


# ---------------------------------------------------------------------------
# Distribution builders (mirror copula_engine.py, keyed by DistributionType)
# ---------------------------------------------------------------------------

def _build_reference_distribution(
    metric: MetricDefinition,
) -> stats.rv_continuous | stats.rv_frozen:
    """Build a scipy distribution object from a MetricDefinition.

    Handles the parameter-naming differences between MetricDefinition
    and scipy. Returns a frozen distribution suitable for KS testing.

    Args:
        metric: The metric definition containing distribution type and params.

    Returns:
        A frozen scipy distribution matching the metric specification.

    Raises:
        ValueError: If the distribution type is not supported.
    """
    dist_type = metric.distribution_type
    params = metric.params

    if dist_type == DistributionType.BETA:
        return stats.beta(a=params["a"], b=params["b"])

    if dist_type == DistributionType.TRUNCATED_NORMAL:
        mu = params["mu"]
        sigma = params["sigma"]
        low = params["low"]
        high = params["high"]
        a_std = (low - mu) / sigma
        b_std = (high - mu) / sigma
        return stats.truncnorm(a=a_std, b=b_std, loc=mu, scale=sigma)

    if dist_type == DistributionType.LOGNORMAL:
        return stats.lognorm(s=params["sigma"], scale=np.exp(params["mu"]))

    if dist_type == DistributionType.POISSON:
        return stats.poisson(mu=params["lam"])

    if dist_type == DistributionType.GAMMA:
        return stats.gamma(a=params["shape"], scale=params["scale"])

    if dist_type == DistributionType.NEGATIVE_BINOMIAL:
        return stats.nbinom(n=params["n"], p=params["p"])

    raise ValueError(
        f"Unsupported distribution type: {dist_type.value}. "
        f"Supported: {[dt.value for dt in DistributionType]}"
    )


def _normalize_to_unit_interval(
    values: np.ndarray, metric: MetricDefinition,
) -> np.ndarray:
    """Normalize bounded data to [0, 1] for KS testing against base Beta.

    For Beta-distributed metrics the registry defines bounds (e.g. 60-100%)
    that scale the base Beta(a, b) from [0, 1] to [low, high]. Before
    running a KS test against the unscaled Beta CDF, the empirical data
    must be mapped back to [0, 1].

    Args:
        values: Raw metric values.
        metric: The metric definition with bounds.

    Returns:
        Values normalized to [0, 1], clipped to avoid edge artifacts.
    """
    lo, hi = metric.bounds
    span = hi - lo
    if span <= 0:
        return values
    normalized = (values - lo) / span
    return np.clip(normalized, 1e-10, 1.0 - 1e-10)


# ---------------------------------------------------------------------------
# DataValidator
# ---------------------------------------------------------------------------

class DataValidator:
    """Validates synthetic SDLC datasets for statistical quality.

    Runs four categories of validation against the MetricRegistry:
        - Distribution: KS tests for each metric
        - Correlation: Empirical vs target Pearson correlations
        - Temporal: Lag-1 autocorrelation structure
        - Bounds: Hard limit enforcement

    Attributes:
        registry: MetricRegistry instance with metric definitions.
        ks_alpha: Significance level for KS tests (default 0.05).
        corr_tolerance: Absolute correlation error tolerance (default 0.15).
        autocorr_tolerance: Autocorrelation deviation tolerance (default 0.2).
    """

    KS_ALPHA: float = 0.05
    CORR_TOLERANCE: float = 0.15
    AUTOCORR_TOLERANCE: float = 0.2

    def __init__(self, metric_registry: MetricRegistry) -> None:
        """Initialize the validator.

        Args:
            metric_registry: MetricRegistry instance with metric definitions.
        """
        self.registry = metric_registry

    # ------------------------------------------------------------------
    # Phase-to-key mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _phase_key(phase: Phase) -> str:
        """Convert a Phase enum to the string key used in data dicts.

        The data dict uses short lowercase keys like 'production', 'build',
        etc. The Phase enum values match these directly.
        """
        return phase.value

    # ------------------------------------------------------------------
    # Distribution validation
    # ------------------------------------------------------------------

    def validate_distributions(
        self, data: dict[str, pd.DataFrame],
    ) -> dict:
        """Run KS tests comparing each metric against its theoretical CDF.

        For each metric defined in the registry:
            1. Locate the metric's data in the corresponding phase DataFrame.
            2. Build the theoretical distribution from the registry definition.
            3. For Beta distributions, normalize data to [0, 1] before testing.
            4. Run scipy.stats.kstest and record the result.

        Args:
            data: Mapping of phase name to DataFrame. Keys are phase values
                like 'production', 'build', 'code', etc.

        Returns:
            Dictionary with 'summary' and 'results' keys. Summary contains
            total count, passed count, and pass rate. Results is a list of
            per-metric test outcomes.
        """
        results: list[dict] = []

        for phase in Phase:
            phase_key = self._phase_key(phase)
            df = data.get(phase_key)
            if df is None or df.empty:
                continue

            metrics = self.registry.get_phase_metrics(phase)

            for metric in metrics:
                if metric.name not in df.columns:
                    continue

                values = df[metric.name].dropna().values
                if len(values) < 10:
                    continue

                ref_dist = _build_reference_distribution(metric)

                # For Beta distributions with bounds, normalize to [0,1]
                if metric.distribution_type == DistributionType.BETA:
                    test_values = _normalize_to_unit_interval(values, metric)
                else:
                    test_values = values

                ks_stat, p_value = stats.kstest(test_values, ref_dist.cdf)

                results.append({
                    "metric": metric.name,
                    "phase": phase.value,
                    "ks_stat": float(ks_stat),
                    "p_value": float(p_value),
                    "passed": bool(p_value > self.KS_ALPHA),
                })

        total = len(results)
        passed = sum(1 for r in results if r["passed"])
        pass_rate = passed / total if total > 0 else 0.0

        return {
            "summary": {
                "total": total,
                "passed": passed,
                "pass_rate": pass_rate,
            },
            "results": results,
        }

    # ------------------------------------------------------------------
    # Correlation validation
    # ------------------------------------------------------------------

    def validate_correlations(
        self,
        data: dict[str, pd.DataFrame],
        target_correlations: list[tuple[str, str, float]],
    ) -> dict:
        """Compare empirical correlations against target correlations.

        Merges all phase DataFrames into a single wide DataFrame (joined
        on row index for temporal alignment), then computes pairwise
        Pearson correlations between the specified metric pairs.

        For each (metric_a, metric_b, target_rho):
            1. Compute empirical Pearson correlation.
            2. Compute absolute error |empirical - target|.
            3. Pass if error < CORR_TOLERANCE (0.15).

        Also computes the Frobenius norm between target and empirical
        correlation matrices for the specified metrics.

        Args:
            data: Mapping of phase name to DataFrame.
            target_correlations: List of (metric_a, metric_b, target_rho)
                tuples specifying expected pairwise correlations.

        Returns:
            Dictionary with 'summary' and 'results' keys. Summary includes
            total, passed, pass_rate, and frobenius_norm. Results is a list
            of per-pair validation outcomes.
        """
        # Merge all phase DataFrames into one wide DataFrame
        merged = self._merge_phases(data)

        results: list[dict] = []
        metric_names_seen: list[str] = []

        for metric_a, metric_b, target_rho in target_correlations:
            if metric_a not in merged.columns or metric_b not in merged.columns:
                continue

            col_a = merged[metric_a].dropna()
            col_b = merged[metric_b].dropna()
            common_idx = col_a.index.intersection(col_b.index)

            if len(common_idx) < 10:
                continue

            empirical_rho = float(
                np.corrcoef(
                    col_a.loc[common_idx].values,
                    col_b.loc[common_idx].values,
                )[0, 1]
            )
            error = abs(empirical_rho - target_rho)

            results.append({
                "metric_a": metric_a,
                "metric_b": metric_b,
                "target_rho": target_rho,
                "empirical_rho": empirical_rho,
                "error": float(error),
                "passed": bool(error < self.CORR_TOLERANCE),
            })

            for name in (metric_a, metric_b):
                if name not in metric_names_seen:
                    metric_names_seen.append(name)

        # Frobenius norm between target and empirical correlation matrices
        frobenius_norm = self._compute_frobenius_norm(
            merged, target_correlations, metric_names_seen,
        )

        total = len(results)
        passed = sum(1 for r in results if r["passed"])
        pass_rate = passed / total if total > 0 else 0.0

        return {
            "summary": {
                "total": total,
                "passed": passed,
                "pass_rate": pass_rate,
                "frobenius_norm": frobenius_norm,
            },
            "results": results,
        }

    @staticmethod
    def _merge_phases(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Merge all phase DataFrames into a single wide DataFrame.

        Joins on row index (integer position) since all phases share
        the same temporal alignment (same number of releases/time steps).
        Duplicate column names across phases are kept as-is since the
        first occurrence wins with pd.concat.

        Args:
            data: Mapping of phase name to DataFrame.

        Returns:
            A single DataFrame with all metrics as columns.
        """
        frames: list[pd.DataFrame] = []
        for phase_key in sorted(data.keys()):
            df = data[phase_key]
            if df is not None and not df.empty:
                frames.append(df.reset_index(drop=True))

        if not frames:
            return pd.DataFrame()

        # Concatenate along columns, keeping first occurrence of duplicates
        merged = pd.concat(frames, axis=1)
        # Remove duplicate columns (keep first)
        merged = merged.loc[:, ~merged.columns.duplicated()]
        return merged

    @staticmethod
    def _compute_frobenius_norm(
        merged: pd.DataFrame,
        target_correlations: list[tuple[str, str, float]],
        metric_names: list[str],
    ) -> float:
        """Compute Frobenius norm between target and empirical matrices.

        Builds square correlation matrices for the subset of metrics
        that appear in target_correlations, then computes
        ||C_target - C_empirical||_F.

        Args:
            merged: Wide DataFrame with all metrics.
            target_correlations: Target pairwise correlations.
            metric_names: Ordered list of metric names to include.

        Returns:
            Frobenius norm as a float, or 0.0 if computation is not possible.
        """
        if not metric_names:
            return 0.0

        available = [m for m in metric_names if m in merged.columns]
        if len(available) < 2:
            return 0.0

        n = len(available)
        name_to_idx = {name: i for i, name in enumerate(available)}

        # Build target correlation matrix
        target_matrix = np.eye(n, dtype=np.float64)
        for metric_a, metric_b, rho in target_correlations:
            if metric_a in name_to_idx and metric_b in name_to_idx:
                i = name_to_idx[metric_a]
                j = name_to_idx[metric_b]
                target_matrix[i, j] = rho
                target_matrix[j, i] = rho

        # Build empirical correlation matrix
        subset = merged[available].dropna()
        if len(subset) < 10:
            return 0.0

        empirical_matrix = np.array(subset.corr().values, dtype=np.float64)

        # Frobenius norm of the difference
        diff = target_matrix - empirical_matrix
        return float(np.linalg.norm(diff, ord="fro"))

    # ------------------------------------------------------------------
    # Temporal validation
    # ------------------------------------------------------------------

    def validate_temporal(
        self,
        data: dict[str, pd.DataFrame],
        target_autocorr: float = 0.6,
    ) -> dict:
        """Validate temporal autocorrelation structure.

        For each numeric metric, computes the lag-1 autocorrelation and
        checks whether it falls within [target - tolerance, target + tolerance].

        Args:
            data: Mapping of phase name to DataFrame.
            target_autocorr: Expected lag-1 autocorrelation (default 0.6).

        Returns:
            Dictionary with 'summary' and 'results' keys.
        """
        results: list[dict] = []
        lower_bound = target_autocorr - self.AUTOCORR_TOLERANCE
        upper_bound = target_autocorr + self.AUTOCORR_TOLERANCE

        for phase in Phase:
            phase_key = self._phase_key(phase)
            df = data.get(phase_key)
            if df is None or df.empty:
                continue

            metrics = self.registry.get_phase_metrics(phase)

            for metric in metrics:
                if metric.name not in df.columns:
                    continue

                series = df[metric.name].dropna()
                if len(series) < 20:
                    continue

                lag1_autocorr = self._compute_lag1_autocorrelation(
                    series.values,
                )

                if np.isnan(lag1_autocorr):
                    continue

                results.append({
                    "metric": metric.name,
                    "phase": phase.value,
                    "lag1_autocorr": float(lag1_autocorr),
                    "target": target_autocorr,
                    "passed": bool(lower_bound <= lag1_autocorr <= upper_bound),
                })

        total = len(results)
        passed = sum(1 for r in results if r["passed"])
        pass_rate = passed / total if total > 0 else 0.0

        return {
            "summary": {
                "total": total,
                "passed": passed,
                "pass_rate": pass_rate,
            },
            "results": results,
        }

    @staticmethod
    def _compute_lag1_autocorrelation(values: np.ndarray) -> float:
        """Compute lag-1 Pearson autocorrelation for a time series.

        Uses numpy corrcoef on the series shifted by one position.

        Args:
            values: 1D array of numeric values.

        Returns:
            Lag-1 autocorrelation as a float. Returns NaN if the series
            has zero variance.
        """
        if len(values) < 3:
            return float("nan")

        x = values[:-1]
        y = values[1:]

        # Guard against constant series
        if np.std(x) == 0.0 or np.std(y) == 0.0:
            return float("nan")

        return float(np.corrcoef(x, y)[0, 1])

    # ------------------------------------------------------------------
    # Bound validation
    # ------------------------------------------------------------------

    def validate_bounds(
        self, data: dict[str, pd.DataFrame],
    ) -> dict:
        """Check that all values fall within defined bounds.

        Uses bounds from the MetricDefinition for each metric. Reports
        any values that fall outside [bound_min, bound_max].

        Args:
            data: Mapping of phase name to DataFrame.

        Returns:
            Dictionary with 'summary' (total metrics checked, violation
            count) and 'violations' (list of per-metric violation details).
        """
        total_checked = 0
        violations: list[dict] = []

        for phase in Phase:
            phase_key = self._phase_key(phase)
            df = data.get(phase_key)
            if df is None or df.empty:
                continue

            metrics = self.registry.get_phase_metrics(phase)

            for metric in metrics:
                if metric.name not in df.columns:
                    continue

                values = df[metric.name].dropna().values
                if len(values) == 0:
                    continue

                total_checked += 1
                bound_min, bound_max = metric.bounds
                min_val = float(np.min(values))
                max_val = float(np.max(values))

                out_of_bounds = int(
                    np.sum((values < bound_min) | (values > bound_max))
                )

                if out_of_bounds > 0:
                    violations.append({
                        "metric": metric.name,
                        "phase": phase.value,
                        "min_val": min_val,
                        "max_val": max_val,
                        "bound_min": bound_min,
                        "bound_max": bound_max,
                        "count": out_of_bounds,
                    })

        return {
            "summary": {
                "total": total_checked,
                "violations": len(violations),
            },
            "violations": violations,
        }

    # ------------------------------------------------------------------
    # Combined validation
    # ------------------------------------------------------------------

    def validate_all(
        self,
        data: dict[str, pd.DataFrame],
        target_correlations: Optional[list[tuple[str, str, float]]] = None,
        target_autocorr: float = 0.6,
    ) -> dict:
        """Run all validations and return a combined report.

        Args:
            data: Mapping of phase name to DataFrame.
            target_correlations: Optional list of (metric_a, metric_b,
                target_rho) tuples. If None, correlation validation is
                skipped.
            target_autocorr: Expected lag-1 autocorrelation (default 0.6).

        Returns:
            Dictionary with keys 'distributions', 'correlations',
            'temporal', 'bounds', and 'overall_passed'.
        """
        dist_results = self.validate_distributions(data)
        temporal_results = self.validate_temporal(data, target_autocorr)
        bounds_results = self.validate_bounds(data)

        corr_results: Optional[dict] = None
        if target_correlations is not None and len(target_correlations) > 0:
            corr_results = self.validate_correlations(
                data, target_correlations,
            )

        # Overall pass: distribution pass rate >= 0.90,
        # no bound violations, and (if tested) correlation pass rate >= 0.80
        overall = True

        if dist_results["summary"]["pass_rate"] < 0.90:
            overall = False
        if bounds_results["summary"]["violations"] > 0:
            overall = False
        if corr_results is not None:
            if corr_results["summary"]["pass_rate"] < 0.80:
                overall = False

        return {
            "distributions": dist_results,
            "correlations": corr_results,
            "temporal": temporal_results,
            "bounds": bounds_results,
            "overall_passed": overall,
        }

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def print_report(self, results: dict) -> None:
        """Print a formatted validation report to stdout.

        Displays a summary block for each validation category,
        followed by an overall PASS/FAIL verdict.

        Args:
            results: Output from validate_all().
        """
        print("=" * 72)
        print("  PRESTO Synthetic Data Validation Report")
        print("=" * 72)

        # Distribution validation
        dist = results["distributions"]
        ds = dist["summary"]
        print(
            f"\n[Distribution] {ds['passed']}/{ds['total']} metrics passed "
            f"KS test ({ds['pass_rate']:.1%} pass rate)"
        )
        failed_dist = [r for r in dist["results"] if not r["passed"]]
        if failed_dist:
            print("  Failed metrics:")
            for r in failed_dist[:10]:
                print(
                    f"    - {r['metric']} ({r['phase']}): "
                    f"KS={r['ks_stat']:.4f}, p={r['p_value']:.4f}"
                )
            if len(failed_dist) > 10:
                print(f"    ... and {len(failed_dist) - 10} more")

        # Correlation validation
        corr = results.get("correlations")
        if corr is not None:
            cs = corr["summary"]
            print(
                f"\n[Correlation] {cs['passed']}/{cs['total']} pairs within "
                f"tolerance ({cs['pass_rate']:.1%} preserved)"
            )
            print(f"  Frobenius norm: {cs['frobenius_norm']:.4f}")
            failed_corr = [r for r in corr["results"] if not r["passed"]]
            if failed_corr:
                print("  Failed pairs:")
                for r in failed_corr[:10]:
                    print(
                        f"    - {r['metric_a']} <-> {r['metric_b']}: "
                        f"target={r['target_rho']:.3f}, "
                        f"empirical={r['empirical_rho']:.3f}, "
                        f"error={r['error']:.3f}"
                    )
                if len(failed_corr) > 10:
                    print(f"    ... and {len(failed_corr) - 10} more")
        else:
            print("\n[Correlation] Skipped (no target correlations provided)")

        # Temporal validation
        temp = results["temporal"]
        ts = temp["summary"]
        print(
            f"\n[Temporal] {ts['passed']}/{ts['total']} metrics have correct "
            f"autocorrelation ({ts['pass_rate']:.1%} pass rate)"
        )
        failed_temp = [r for r in temp["results"] if not r["passed"]]
        if failed_temp:
            print("  Failed metrics:")
            for r in failed_temp[:10]:
                print(
                    f"    - {r['metric']} ({r['phase']}): "
                    f"lag1={r['lag1_autocorr']:.3f}, "
                    f"target={r['target']:.3f}"
                )
            if len(failed_temp) > 10:
                print(f"    ... and {len(failed_temp) - 10} more")

        # Bound validation
        bounds = results["bounds"]
        bs = bounds["summary"]
        n_violations = bs["violations"]
        print(
            f"\n[Bounds] {bs['total']} metrics checked, "
            f"{n_violations} violation(s) found"
        )
        if bounds["violations"]:
            for v in bounds["violations"][:10]:
                print(
                    f"    - {v['metric']} ({v['phase']}): "
                    f"range [{v['min_val']:.2f}, {v['max_val']:.2f}] "
                    f"outside [{v['bound_min']:.1f}, {v['bound_max']:.1f}] "
                    f"({v['count']} values)"
                )
            if len(bounds["violations"]) > 10:
                remaining = len(bounds["violations"]) - 10
                print(f"    ... and {remaining} more")

        # Overall verdict
        overall = results["overall_passed"]
        verdict = "PASS" if overall else "FAIL"
        print(f"\n{'=' * 72}")
        print(f"  Overall: {verdict}")
        print(f"{'=' * 72}")

    def save_report(self, results: dict, filepath: str) -> None:
        """Save a validation report as a Markdown file.

        Generates a clean, structured document suitable for including
        as supplementary material in the PRESTO paper.

        Args:
            results: Output from validate_all().
            filepath: Destination path for the .md file.
        """
        lines: list[str] = []

        lines.append("# PRESTO Synthetic Data Validation Report")
        lines.append("")
        lines.append(
            "Statistical validation of synthetic SDLC metrics against "
            "theoretical distributions, target correlations, temporal "
            "structure, and defined bounds."
        )
        lines.append("")

        # Overall verdict
        overall = results["overall_passed"]
        verdict = "PASS" if overall else "FAIL"
        lines.append(f"**Overall Verdict: {verdict}**")
        lines.append("")

        # --- Distribution section ---
        lines.append("## 1. Distribution Validation (Kolmogorov-Smirnov)")
        lines.append("")

        dist = results["distributions"]
        ds = dist["summary"]
        lines.append(
            f"- **Result:** {ds['passed']}/{ds['total']} metrics passed "
            f"({ds['pass_rate']:.1%})"
        )
        lines.append(f"- **Significance level:** alpha = {self.KS_ALPHA}")
        lines.append(
            "- **Criterion:** p-value > alpha (fail to reject H0: "
            "data follows specified distribution)"
        )
        lines.append("")

        if dist["results"]:
            lines.append("| Metric | Phase | KS Statistic | p-value | Result |")
            lines.append("|--------|-------|-------------|---------|--------|")
            for r in dist["results"]:
                status = "Pass" if r["passed"] else "**FAIL**"
                lines.append(
                    f"| {r['metric']} | {r['phase']} | "
                    f"{r['ks_stat']:.4f} | {r['p_value']:.4f} | {status} |"
                )
            lines.append("")

        # --- Correlation section ---
        lines.append("## 2. Correlation Validation")
        lines.append("")

        corr = results.get("correlations")
        if corr is not None:
            cs = corr["summary"]
            lines.append(
                f"- **Result:** {cs['passed']}/{cs['total']} pairs within "
                f"tolerance ({cs['pass_rate']:.1%})"
            )
            lines.append(
                f"- **Tolerance:** |empirical - target| < "
                f"{self.CORR_TOLERANCE}"
            )
            lines.append(
                f"- **Frobenius norm:** {cs['frobenius_norm']:.4f}"
            )
            lines.append("")

            if corr["results"]:
                lines.append(
                    "| Metric A | Metric B | Target rho | "
                    "Empirical rho | Error | Result |"
                )
                lines.append(
                    "|----------|----------|-----------|"
                    "--------------|-------|--------|"
                )
                for r in corr["results"]:
                    status = "Pass" if r["passed"] else "**FAIL**"
                    lines.append(
                        f"| {r['metric_a']} | {r['metric_b']} | "
                        f"{r['target_rho']:.3f} | "
                        f"{r['empirical_rho']:.3f} | "
                        f"{r['error']:.3f} | {status} |"
                    )
                lines.append("")
        else:
            lines.append("*Skipped (no target correlations provided).*")
            lines.append("")

        # --- Temporal section ---
        lines.append("## 3. Temporal Autocorrelation Validation")
        lines.append("")

        temp = results["temporal"]
        ts = temp["summary"]
        lines.append(
            f"- **Result:** {ts['passed']}/{ts['total']} metrics within "
            f"tolerance ({ts['pass_rate']:.1%})"
        )
        lines.append(
            f"- **Tolerance:** target +/- {self.AUTOCORR_TOLERANCE}"
        )
        lines.append("")

        if temp["results"]:
            lines.append(
                "| Metric | Phase | Lag-1 Autocorr | Target | Result |"
            )
            lines.append(
                "|--------|-------|---------------|--------|--------|"
            )
            for r in temp["results"]:
                status = "Pass" if r["passed"] else "**FAIL**"
                lines.append(
                    f"| {r['metric']} | {r['phase']} | "
                    f"{r['lag1_autocorr']:.3f} | "
                    f"{r['target']:.3f} | {status} |"
                )
            lines.append("")

        # --- Bounds section ---
        lines.append("## 4. Bound Validation")
        lines.append("")

        bounds = results["bounds"]
        bs = bounds["summary"]
        lines.append(
            f"- **Metrics checked:** {bs['total']}"
        )
        lines.append(
            f"- **Violations:** {bs['violations']}"
        )
        lines.append("")

        if bounds["violations"]:
            lines.append(
                "| Metric | Phase | Data Range | Defined Bounds | "
                "Violation Count |"
            )
            lines.append(
                "|--------|-------|-----------|---------------|"
                "----------------|"
            )
            for v in bounds["violations"]:
                lines.append(
                    f"| {v['metric']} | {v['phase']} | "
                    f"[{v['min_val']:.2f}, {v['max_val']:.2f}] | "
                    f"[{v['bound_min']:.1f}, {v['bound_max']:.1f}] | "
                    f"{v['count']} |"
                )
            lines.append("")

        # Write file
        content = "\n".join(lines)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
