"""
Temporal dynamics engine for synthetic SDLC metric generation.

Transforms i.i.d. copula-generated samples into realistic time series by
applying autoregressive correlation, maturity trends, release-type effects,
and stochastic shock events. All transformations preserve Date and Release
Number columns and respect metric bounds.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Metric polarity classification
# ---------------------------------------------------------------------------

# Metrics where higher values mean *better* outcomes (percentages, scores).
_HIGHER_IS_BETTER_KEYWORDS: list[str] = [
    "success rate",
    "coverage",
    "pass rate",
    "uptime",
    "compliance",
    "score",
    "hit rate",
    "effectiveness",
    "stability",
    "availability",
    "consistency",
    "accuracy",
    "resilience",
    "tolerance",
    "integrity",
    "efficiency",
    "adoption rate",
    "acceptance",
    "satisfaction",
    "readiness",
    "engagement",
    "quality",
    "completeness",
    "clarity",
    "testability",
    "traceability",
    "approval",
    "realization",
    "sign-off",
    "training completion",
    "documentation",
    "promotion rate",
    "reproducibility",
    "monitoring correlation",
    "baseline achievement",
    "containment",
    "delivered score",
    "prioritization",
    "automation",
    "ratio",
    "throughput",
    "concurrent users",
    "frequency",
    "automated test ratio",
    "test stability",
    "degradation response",
    "degradation score",
]

# Metrics where lower values mean *better* outcomes (times, costs, errors).
_LOWER_IS_BETTER_KEYWORDS: list[str] = [
    "time",
    "duration",
    "latency",
    "incident count",
    "defect",
    "issue",
    "failure rate",
    "rollback",
    "complexity",
    "code smells",
    "vulnerabilities",
    "technical debt",
    "duplication",
    "dead code",
    "error rate",
    "flakiness",
    "leakage",
    "declined",
    "change rate",
    "cycle time",
    "ambiguity",
    "cost",
    "utilization",
    "deviation",
    "regression issues",
    "budget consumption",
    "queue time",
    "artifact size",
    "response time",
    "recovery time",
    "failover time",
    "reopened",
    "maintenance effort",
]


def _classify_polarity(column_name: str) -> str:
    """Return 'higher_is_better', 'lower_is_better', or 'neutral'.

    Uses keyword matching against the column name (case-insensitive).
    When both polarities match, the longer keyword wins (more specific).
    """
    col_lower = column_name.lower()

    best_higher_len = 0
    for kw in _HIGHER_IS_BETTER_KEYWORDS:
        if kw in col_lower:
            best_higher_len = max(best_higher_len, len(kw))

    best_lower_len = 0
    for kw in _LOWER_IS_BETTER_KEYWORDS:
        if kw in col_lower:
            best_lower_len = max(best_lower_len, len(kw))

    if best_higher_len > best_lower_len:
        return "higher_is_better"
    if best_lower_len > best_higher_len:
        return "lower_is_better"
    # Tie or no match: default to higher_is_better for score-like columns,
    # lower_is_better for count-like columns, else neutral.
    if "score" in col_lower or "rate" in col_lower or "%" in col_lower:
        return "higher_is_better"
    if "count" in col_lower or "number" in col_lower:
        return "lower_is_better"
    return "neutral"


def _select_metric_cols(
    df: pd.DataFrame, metric_cols: Optional[list[str]]
) -> list[str]:
    """Return explicit metric columns or auto-detect numeric ones,
    excluding 'Date' and 'Release Number'."""
    skip = {"Date", "Release Number"}
    if metric_cols is not None:
        return [c for c in metric_cols if c in df.columns and c not in skip]
    return [c for c in df.columns if c not in skip and pd.api.types.is_numeric_dtype(df[c])]


# ---------------------------------------------------------------------------
# Temporal Engine
# ---------------------------------------------------------------------------


class TemporalEngine:
    """Applies temporal dynamics to copula-generated i.i.d. data.

    All public methods return new DataFrames (input is not mutated).
    The ``Date`` and ``Release Number`` columns are never modified.

    Parameters
    ----------
    seed : int
        Random seed for reproducibility.
    """

    def __init__(self, seed: int = 42) -> None:
        self.rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # AR(1) autocorrelation
    # ------------------------------------------------------------------

    def apply_ar1(
        self,
        data: pd.DataFrame,
        rho: float = 0.6,
        metric_cols: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """Apply AR(1) process to introduce temporal autocorrelation.

        For each metric column the transformation is applied in rank space
        to avoid pushing values outside their observed range:

            1. Convert values to ranks (percentiles) in [0, 1].
            2. Apply AR(1): r_t = rho * r_{t-1} + (1 - rho) * r_t + eps
            3. Re-rank the result to obtain new percentiles.
            4. Map back to original value domain via sorted original values.

        Parameters
        ----------
        data : pd.DataFrame
            Input data with Date, Release Number, and metric columns.
        rho : float
            Autocorrelation coefficient in (0, 1). Higher values produce
            smoother, more correlated series. Default 0.6.
        metric_cols : list[str] or None
            Columns to transform. ``None`` auto-detects all numeric columns.

        Returns
        -------
        pd.DataFrame
            Copy of *data* with temporally correlated metric values.
        """
        if not 0.0 < rho < 1.0:
            raise ValueError(f"rho must be in (0, 1), got {rho}")

        result = data.copy()
        cols = _select_metric_cols(result, metric_cols)
        n = len(result)
        if n < 2:
            return result

        for col in cols:
            values = result[col].to_numpy(dtype=np.float64)
            sorted_vals = np.sort(values)

            # Convert to fractional ranks in (0, 1)
            ranks = _fractional_ranks(values)

            # AR(1) in rank space
            eps_scale = 0.02 * (1.0 - rho)
            ar_ranks = np.empty_like(ranks)
            ar_ranks[0] = ranks[0]
            for t in range(1, n):
                noise = self.rng.normal(0.0, eps_scale)
                ar_ranks[t] = rho * ar_ranks[t - 1] + (1.0 - rho) * ranks[t] + noise

            # Clamp to valid rank range
            ar_ranks = np.clip(ar_ranks, 0.0, 1.0)

            # Re-rank: order the AR(1) ranks to get new ordering indices
            new_order = np.argsort(np.argsort(ar_ranks))
            result[col] = sorted_vals[new_order]

        return result

    # ------------------------------------------------------------------
    # Maturity trend
    # ------------------------------------------------------------------

    def inject_trend(
        self,
        data: pd.DataFrame,
        metric_cols: list[str],
        trend_strength: float = 0.1,
    ) -> pd.DataFrame:
        """Add a gradual maturity trend.

        - **higher_is_better** metrics receive an upward trend (multiplicative
          for percentages, additive for scores).
        - **lower_is_better** metrics receive a downward trend (values
          decrease over time, reflecting improvement).

        Parameters
        ----------
        data : pd.DataFrame
            Input data (must have a ``Date`` column for ordering).
        metric_cols : list[str]
            Columns to apply the trend to.
        trend_strength : float
            Fractional magnitude of the trend over the full time span.
            0.1 means a 10 % cumulative change from first to last row.

        Returns
        -------
        pd.DataFrame
            Copy of *data* with trend applied.
        """
        result = data.copy()
        n = len(result)
        if n < 2:
            return result

        # Linear ramp from 0 to trend_strength
        ramp = np.linspace(0.0, trend_strength, n)

        for col in metric_cols:
            if col not in result.columns:
                continue
            polarity = _classify_polarity(col)
            values = result[col].to_numpy(dtype=np.float64)

            is_percentage = "%" in col or "rate" in col.lower()

            if polarity == "higher_is_better":
                if is_percentage:
                    # Multiplicative: x * (1 + ramp_t)
                    result[col] = values * (1.0 + ramp)
                else:
                    # Additive shift scaled by column mean
                    col_mean = np.nanmean(values)
                    result[col] = values + ramp * col_mean
            elif polarity == "lower_is_better":
                if is_percentage:
                    result[col] = values * (1.0 - ramp)
                else:
                    col_mean = np.nanmean(values)
                    result[col] = values - ramp * col_mean
            # neutral: no trend

        return result

    # ------------------------------------------------------------------
    # Release-type effects
    # ------------------------------------------------------------------

    def inject_release_effects(
        self,
        data: pd.DataFrame,
        release_types: list[str],
    ) -> pd.DataFrame:
        """Modulate metrics based on release type.

        - **Major** releases: quality metrics dip slightly (more changes
          introduce more risk). Effect: 3-8 % degradation on quality metrics.
        - **Minor** releases: neutral to slight improvement (1-3 %).
        - **Patch** releases: targeted fixes improve quality (2-5 %).

        Parameters
        ----------
        data : pd.DataFrame
            Input data with metric columns.
        release_types : list[str]
            One of ``'Major'``, ``'Minor'``, ``'Patch'`` per row,
            aligned with *data* row order.

        Returns
        -------
        pd.DataFrame
            Copy of *data* with release-type effects applied.
        """
        if len(release_types) != len(data):
            raise ValueError(
                f"release_types length ({len(release_types)}) must match "
                f"data length ({len(data)})"
            )

        result = data.copy()
        cols = _select_metric_cols(result, None)

        # Upcast integer columns to float64 to avoid dtype warnings when
        # multiplicative factors produce non-integer results.
        for col in cols:
            if pd.api.types.is_integer_dtype(result[col]):
                result[col] = result[col].astype(np.float64)

        for idx, rtype in enumerate(release_types):
            rtype_lower = rtype.strip().lower()
            for col in cols:
                polarity = _classify_polarity(col)
                val = float(result.at[result.index[idx], col])

                # Determine the multiplier direction:
                # For higher_is_better: Major degrades (multiply < 1),
                # Patch improves (multiply > 1).
                # For lower_is_better: Major worsens (multiply > 1, i.e.,
                # incident counts go up), Patch fixes (multiply < 1).
                if rtype_lower == "major":
                    delta = self.rng.uniform(0.03, 0.08)
                    factor = self._release_factor(polarity, -delta)
                elif rtype_lower == "patch":
                    delta = self.rng.uniform(0.02, 0.05)
                    factor = self._release_factor(polarity, delta)
                else:
                    # Minor: slight improvement
                    delta = self.rng.uniform(0.01, 0.03)
                    factor = self._release_factor(polarity, delta)

                result.at[result.index[idx], col] = val * factor

        return result

    # ------------------------------------------------------------------
    # Shock events
    # ------------------------------------------------------------------

    def inject_shock_events(
        self,
        data: pd.DataFrame,
        shock_probability: float = 0.05,
        metric_cols: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """Inject correlated "bad release" shock events.

        With probability *shock_probability* each row is designated a shock.
        Shocked rows have **all** selected metrics shifted 1-2 sigma toward
        worse values. The subsequent 2-3 rows exhibit gradual recovery
        (exponential decay back to baseline).

        Parameters
        ----------
        data : pd.DataFrame
            Input data.
        shock_probability : float
            Per-row probability of a shock event. Default 0.05 (5 %).
        metric_cols : list[str] or None
            Columns affected by shocks. ``None`` selects all numeric columns.

        Returns
        -------
        pd.DataFrame
            Copy of *data* with shock events injected.
        """
        result = data.copy()
        cols = _select_metric_cols(result, metric_cols)
        n = len(result)
        if n < 2 or not cols:
            return result

        # Upcast integer columns to float64 to avoid dtype warnings when
        # additive shock deltas produce non-integer results.
        for col in cols:
            if pd.api.types.is_integer_dtype(result[col]):
                result[col] = result[col].astype(np.float64)

        # Pre-compute column statistics
        col_stats: dict[str, tuple[float, float, str]] = {}
        for col in cols:
            arr = result[col].to_numpy(dtype=np.float64)
            col_stats[col] = (
                float(np.nanmean(arr)),
                float(np.nanstd(arr)),
                _classify_polarity(col),
            )

        # Determine shock locations (avoid last 3 rows to allow recovery)
        shock_mask = self.rng.random(n) < shock_probability
        # Ensure no shocks in recovery windows of prior shocks
        shock_indices: list[int] = []
        cooldown_until = -1
        for i in range(n):
            if shock_mask[i] and i > cooldown_until:
                shock_indices.append(i)
                recovery_len = int(self.rng.integers(2, 4))  # 2 or 3
                cooldown_until = i + recovery_len

        # Apply shocks and recovery
        for shock_idx in shock_indices:
            # Shock magnitude: 1-2 sigma
            sigma_mult = self.rng.uniform(1.0, 2.0)

            for col in cols:
                mean_val, std_val, polarity = col_stats[col]
                if std_val < 1e-12:
                    continue

                shock_delta = sigma_mult * std_val

                # Direction: push toward worse values
                if polarity == "higher_is_better":
                    shock_delta = -shock_delta  # decrease is worse
                # For lower_is_better, positive delta means worse (higher)
                # For neutral, positive delta (arbitrary)

                val = float(result.at[result.index[shock_idx], col])
                result.at[result.index[shock_idx], col] = val + shock_delta

                # Gradual recovery over next 2-3 rows
                recovery_len = int(self.rng.integers(2, 4))
                for r in range(1, recovery_len + 1):
                    rec_idx = shock_idx + r
                    if rec_idx >= n:
                        break
                    # Exponential decay: remaining shock = shock_delta * decay^r
                    decay = 0.4 ** r
                    residual = shock_delta * decay
                    rec_val = float(result.at[result.index[rec_idx], col])
                    result.at[result.index[rec_idx], col] = rec_val + residual

        return result

    # ------------------------------------------------------------------
    # Bounds enforcement
    # ------------------------------------------------------------------

    def enforce_bounds(
        self,
        data: pd.DataFrame,
        bounds: dict[str, tuple[float, float]],
    ) -> pd.DataFrame:
        """Clip metric values to their defined bounds.

        Parameters
        ----------
        data : pd.DataFrame
            Input data.
        bounds : dict[str, tuple[float, float]]
            Mapping of column name to (lower, upper) bounds.

        Returns
        -------
        pd.DataFrame
            Copy of *data* with values clipped to bounds.
        """
        result = data.copy()
        for col, (lo, hi) in bounds.items():
            if col in result.columns:
                result[col] = result[col].clip(lower=lo, upper=hi)
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _release_factor(polarity: str, improvement_delta: float) -> float:
        """Compute a multiplicative factor from a signed improvement delta.

        Parameters
        ----------
        polarity : str
            ``'higher_is_better'``, ``'lower_is_better'``, or ``'neutral'``.
        improvement_delta : float
            Positive means improvement, negative means degradation.

        Returns
        -------
        float
            Multiplicative factor to apply to the raw value.
        """
        if polarity == "higher_is_better":
            # Improvement = increase, so factor > 1 when delta > 0
            return 1.0 + improvement_delta
        if polarity == "lower_is_better":
            # Improvement = decrease, so factor < 1 when delta > 0
            return 1.0 - improvement_delta
        # Neutral: no modification
        return 1.0


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _fractional_ranks(values: np.ndarray) -> np.ndarray:
    """Return fractional ranks in (0, 1) for an array of values.

    Uses the average method for ties, then scales to (0, 1) using
    (rank - 0.5) / n  (Hazen plotting position).
    """
    n = len(values)
    if n == 0:
        return values.copy()
    # scipy-free rank computation
    temp = np.argsort(np.argsort(values))
    ranks = temp.astype(np.float64)

    # Handle ties: average ranks for equal values
    sorted_indices = np.argsort(values)
    sorted_vals = values[sorted_indices]
    i = 0
    while i < n:
        j = i
        while j < n and sorted_vals[j] == sorted_vals[i]:
            j += 1
        if j > i + 1:
            avg_rank = np.mean(np.arange(i, j, dtype=np.float64))
            for k in range(i, j):
                ranks[sorted_indices[k]] = avg_rank
        i = j

    # Scale to (0, 1) using Hazen plotting position
    return (ranks + 0.5) / n
