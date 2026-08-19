"""Gaussian Copula engine for generating correlated synthetic SDLC metrics.

Mathematical background:
    A Gaussian copula generates correlated random variables with arbitrary
    marginal distributions via the following procedure:

    1. Define a correlation matrix Sigma (d x d, positive semi-definite).
    2. Sample Z ~ N(0, Sigma) using Cholesky decomposition:
       Z = L @ epsilon, where L = cholesky(Sigma) and epsilon ~ N(0, I).
    3. Transform to uniform: U_i = Phi(Z_i), where Phi is the standard
       normal CDF.
    4. Transform to target marginals: X_i = F_i^{-1}(U_i), where F_i is
       each metric's marginal CDF.

This decouples the dependence structure (copula) from the marginal
distributions, allowing each metric to follow its own distribution while
preserving realistic inter-metric correlations.

References:
    Nelsen, R.B. (2006). An Introduction to Copulas. Springer.
    Higham, N.J. (2002). Computing the nearest correlation matrix,
        a problem from finance. IMA Journal of Numerical Analysis, 22(3).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import scipy.stats as stats


# ---------------------------------------------------------------------------
# Supported marginal distribution builders
# ---------------------------------------------------------------------------

def _build_beta(params: dict[str, float]) -> stats.rv_continuous:
    """Build a Beta distribution from user-supplied parameters.

    Expected params: a, b, and optionally loc and scale for shifting
    the support from [0,1] to [loc, loc+scale].
    """
    return stats.beta(
        a=params["a"],
        b=params["b"],
        loc=params.get("loc", 0.0),
        scale=params.get("scale", 1.0),
    )


def _build_truncated_normal(params: dict[str, float]) -> stats.rv_continuous:
    """Build a truncated normal distribution.

    Expected params: mu, sigma, low, high.
    scipy.stats.truncnorm uses standardised bounds:
        a = (low - mu) / sigma,  b = (high - mu) / sigma
    """
    mu = params["mu"]
    sigma = params["sigma"]
    low = params["low"]
    high = params["high"]
    a_std = (low - mu) / sigma
    b_std = (high - mu) / sigma
    return stats.truncnorm(a=a_std, b=b_std, loc=mu, scale=sigma)


def _build_lognormal(params: dict[str, float]) -> stats.rv_continuous:
    """Build a log-normal distribution.

    Expected params: mu (mean of log), sigma (std of log).
    scipy.stats.lognorm parameterises as:
        s = sigma,  scale = exp(mu),  loc = 0
    """
    return stats.lognorm(s=params["sigma"], scale=np.exp(params["mu"]))


def _build_poisson(params: dict[str, float]) -> stats.rv_discrete:
    """Build a Poisson distribution.

    Expected params: mu (lambda, the rate parameter).
    """
    return stats.poisson(mu=params["mu"])


def _build_gamma(params: dict[str, float]) -> stats.rv_continuous:
    """Build a Gamma distribution.

    Expected params: alpha (shape), beta (rate).
    scipy.stats.gamma uses shape a and scale = 1/beta.
    """
    return stats.gamma(a=params["alpha"], scale=1.0 / params["beta"])


def _build_uniform(params: dict[str, float]) -> stats.rv_continuous:
    """Build a uniform distribution on [low, high].

    Expected params: low, high.
    scipy.stats.uniform(loc, scale) has support [loc, loc+scale].
    """
    low = params["low"]
    high = params["high"]
    return stats.uniform(loc=low, scale=high - low)


_DISTRIBUTION_BUILDERS: dict[str, Any] = {
    "beta": _build_beta,
    "truncated_normal": _build_truncated_normal,
    "lognormal": _build_lognormal,
    "poisson": _build_poisson,
    "gamma": _build_gamma,
    "uniform": _build_uniform,
}

# Names of discrete distributions that require integer rounding
_DISCRETE_DISTRIBUTIONS = {"poisson"}


# ---------------------------------------------------------------------------
# GaussianCopula
# ---------------------------------------------------------------------------

class GaussianCopula:
    """Gaussian Copula for generating correlated synthetic SDLC metrics.

    The copula separates the dependence structure from marginal distributions,
    making it possible to combine, e.g., a Beta-distributed code-coverage
    metric with a Poisson-distributed defect count while preserving their
    empirical correlation.

    Attributes:
        correlation_matrix: Validated PSD correlation matrix (d x d).
        metric_names: Ordered list of metric names matching matrix axes.
        rng: Seeded numpy random generator.
        cholesky_lower: Lower-triangular Cholesky factor of the correlation
            matrix, precomputed at construction time.
    """

    # Clipping bounds to prevent ppf from returning +/- inf
    _U_LOWER: float = 1e-10
    _U_UPPER: float = 1.0 - 1e-10

    def __init__(
        self,
        correlation_matrix: np.ndarray,
        metric_names: list[str],
        seed: int = 42,
    ) -> None:
        """Initialise the Gaussian Copula.

        Args:
            correlation_matrix: d x d correlation matrix. Must be symmetric
                with ones on the diagonal. Will be projected to the nearest
                PSD matrix if necessary.
            metric_names: Metric names corresponding to matrix rows/columns.
            seed: Random seed for reproducibility.

        Raises:
            ValueError: If the matrix dimensions do not match the number of
                metric names, or if the matrix is not square.
        """
        correlation_matrix = np.asarray(correlation_matrix, dtype=np.float64)

        if correlation_matrix.ndim != 2:
            raise ValueError("Correlation matrix must be 2-dimensional.")
        rows, cols = correlation_matrix.shape
        if rows != cols:
            raise ValueError(
                f"Correlation matrix must be square, got ({rows}, {cols})."
            )
        if rows != len(metric_names):
            raise ValueError(
                f"Matrix dimension ({rows}) does not match number of "
                f"metric names ({len(metric_names)})."
            )

        self.metric_names: list[str] = list(metric_names)
        self.correlation_matrix: np.ndarray = self.ensure_positive_definite(
            correlation_matrix
        )
        self.rng: np.random.Generator = np.random.default_rng(seed)

        # Pre-compute Cholesky factor for sampling
        self.cholesky_lower: np.ndarray = np.linalg.cholesky(
            self.correlation_matrix
        )

    # ------------------------------------------------------------------
    # Sampling
    # ------------------------------------------------------------------

    def sample_uniform(self, n_samples: int) -> np.ndarray:
        """Generate correlated uniform [0, 1] samples via the Gaussian copula.

        Steps:
            1. Draw independent standard-normal samples (n_samples x d).
            2. Induce correlation via L @ epsilon^T.
            3. Apply the standard-normal CDF (Phi) to obtain uniforms.

        Args:
            n_samples: Number of samples to generate.

        Returns:
            Array of shape (n_samples, d) with values in (0, 1), where d is
            the number of metrics.
        """
        d = len(self.metric_names)

        # Step 1: independent standard normals, shape (d, n_samples)
        epsilon = self.rng.standard_normal(size=(d, n_samples))

        # Step 2: correlate via Cholesky factor -> shape (d, n_samples)
        z = self.cholesky_lower @ epsilon  # (d, d) @ (d, n) = (d, n)

        # Step 3: Phi(z) -> uniform marginals, then transpose to (n, d)
        u = stats.norm.cdf(z).T  # (n_samples, d)

        # Clip to avoid ppf edge-case infinities
        np.clip(u, self._U_LOWER, self._U_UPPER, out=u)

        return u

    def sample(
        self,
        n_samples: int,
        marginals: dict[str, dict[str, Any]],
    ) -> pd.DataFrame:
        """Generate correlated samples with specified marginal distributions.

        For each metric the caller provides a distribution family, its
        parameters, and optional hard bounds. The copula produces correlated
        uniforms which are then mapped through each metric's inverse CDF.

        Args:
            n_samples: Number of rows to generate.
            marginals: Mapping from metric name to a specification dict:
                {
                    "distribution": one of "beta", "truncated_normal",
                        "lognormal", "poisson", "gamma", "uniform",
                    "params": dict of distribution-specific parameters,
                    "bounds": optional (min, max) tuple for hard clipping
                }
                Every metric in ``self.metric_names`` must appear.

        Returns:
            DataFrame with ``self.metric_names`` as columns and
            ``n_samples`` rows of correlated synthetic data.

        Raises:
            ValueError: If a metric is missing from *marginals* or uses an
                unsupported distribution name.
        """
        missing = set(self.metric_names) - set(marginals)
        if missing:
            raise ValueError(
                f"Marginal specification missing for metrics: "
                f"{sorted(missing)}"
            )

        u = self.sample_uniform(n_samples)  # (n_samples, d)

        result: dict[str, np.ndarray] = {}
        for col_idx, name in enumerate(self.metric_names):
            spec = marginals[name]
            dist_name: str = spec["distribution"]
            params: dict[str, float] = spec["params"]
            bounds: tuple[float, float] | None = spec.get("bounds")

            builder = _DISTRIBUTION_BUILDERS.get(dist_name)
            if builder is None:
                raise ValueError(
                    f"Unsupported distribution '{dist_name}' for metric "
                    f"'{name}'. Supported: "
                    f"{sorted(_DISTRIBUTION_BUILDERS.keys())}."
                )

            dist = builder(params)
            values: np.ndarray = dist.ppf(u[:, col_idx])

            # Discrete distributions: round to nearest integer
            if dist_name in _DISCRETE_DISTRIBUTIONS:
                values = np.rint(values).astype(np.int64)

            # Hard-clip to bounds when provided
            if bounds is not None:
                lo, hi = bounds
                values = np.clip(values, lo, hi)

            result[name] = values

        return pd.DataFrame(result)

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------

    @staticmethod
    def ensure_positive_definite(matrix: np.ndarray) -> np.ndarray:
        """Project a symmetric matrix onto the nearest positive-definite
        correlation matrix using the Higham (2002) alternating projections
        algorithm.

        The method iterates between two projections:
            S: project onto the set of symmetric PSD matrices (clamp
               eigenvalues to >= 0).
            U: project onto the set of matrices with unit diagonal.

        Convergence is checked via the Frobenius norm of the iterate
        difference.

        Args:
            matrix: Symmetric d x d matrix (typically a correlation matrix
                that may have become indefinite through manual editing).

        Returns:
            The nearest positive-definite correlation matrix (unit diagonal,
            all eigenvalues > 0) as a float64 array.
        """
        matrix = np.array(matrix, dtype=np.float64)

        # Quick check: if already PSD, return as-is
        eigenvalues = np.linalg.eigvalsh(matrix)
        if np.all(eigenvalues > 0):
            # Ensure unit diagonal and perfect symmetry
            d = matrix.shape[0]
            diag_sqrt = np.sqrt(np.diag(matrix))
            # If the diagonal is already all 1s, skip normalisation
            if np.allclose(diag_sqrt, 1.0):
                return (matrix + matrix.T) / 2.0
            outer = np.outer(diag_sqrt, diag_sqrt)
            result = matrix / outer
            np.fill_diagonal(result, 1.0)
            return (result + result.T) / 2.0

        # Higham alternating projections
        max_iterations = 1000
        tolerance = 1e-10
        n = matrix.shape[0]

        y = matrix.copy()
        delta_s = np.zeros_like(matrix)

        for _ in range(max_iterations):
            # Dykstra correction
            r = y - delta_s

            # Project onto PSD cone (S-projection)
            eigvals, eigvecs = np.linalg.eigh(r)
            eigvals = np.maximum(eigvals, 0.0)
            # Reconstruct using only components with non-negligible eigenvalues
            # to avoid overflow from multiplying large eigenvector matrices
            mask = eigvals > 1e-14
            x = (eigvecs[:, mask] * eigvals[mask]) @ eigvecs[:, mask].T

            delta_s = x - r

            # Project onto unit-diagonal matrices (U-projection)
            y_new = x.copy()
            np.fill_diagonal(y_new, 1.0)

            # Convergence check
            diff_norm = np.linalg.norm(y_new - y, ord="fro")
            y = y_new
            if diff_norm < tolerance:
                break

        # Final symmetry enforcement
        y = (y + y.T) / 2.0

        # Ensure strictly positive definite by nudging any remaining
        # near-zero eigenvalues
        eigvals_final = np.linalg.eigvalsh(y)
        min_eig = np.min(eigvals_final)
        if min_eig < 1e-12:
            nudge = 1e-8 - min_eig
            y += nudge * np.eye(n)
            # Re-normalise diagonal to 1
            d_sqrt = np.sqrt(np.diag(y))
            y = y / np.outer(d_sqrt, d_sqrt)
            np.fill_diagonal(y, 1.0)
            y = (y + y.T) / 2.0

        return y

    @staticmethod
    def build_correlation_matrix(
        metric_names: list[str],
        correlations: list[tuple[str, str, float]],
    ) -> np.ndarray:
        """Build a correlation matrix from pairwise correlation specifications.

        Pairs not listed default to rho = 0 (independence). The diagonal is
        always set to 1. The result is guaranteed to be positive semi-definite.

        Args:
            metric_names: Ordered list of metric names.
            correlations: List of (metric_a, metric_b, rho) tuples specifying
                pairwise Pearson correlations. Each rho must be in [-1, 1].

        Returns:
            A PSD correlation matrix of shape (d, d).

        Raises:
            ValueError: If a metric name in *correlations* is not found in
                *metric_names*, or if a rho value is outside [-1, 1].
        """
        name_to_idx = {name: i for i, name in enumerate(metric_names)}
        d = len(metric_names)
        matrix = np.eye(d, dtype=np.float64)

        for metric_a, metric_b, rho in correlations:
            if metric_a not in name_to_idx:
                raise ValueError(
                    f"Metric '{metric_a}' not found in metric_names."
                )
            if metric_b not in name_to_idx:
                raise ValueError(
                    f"Metric '{metric_b}' not found in metric_names."
                )
            if not -1.0 <= rho <= 1.0:
                raise ValueError(
                    f"Correlation rho={rho} for ({metric_a}, {metric_b}) "
                    f"is outside [-1, 1]."
                )

            i = name_to_idx[metric_a]
            j = name_to_idx[metric_b]
            matrix[i, j] = rho
            matrix[j, i] = rho

        return GaussianCopula.ensure_positive_definite(matrix)
