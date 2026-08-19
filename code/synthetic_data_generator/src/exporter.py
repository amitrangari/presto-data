"""
Data exporter for synthetic SDLC metric datasets.

Exports generated DataFrames to CSV files that exactly match the column
naming, numeric precision, and directory layout used by the existing
PRESTO project datasets. Also generates release-data.csv with semantic
versioning and a generation_metadata.json for reproducibility.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Phase-to-filename mapping (must match existing project layout)
# ---------------------------------------------------------------------------

PHASE_FILE_MAP: dict[str, str] = {
    "production": "production_run_metrics.csv",
    "build": "build_metrics.csv",
    "code": "code_metrics.csv",
    "test": "test_metrics.csv",
    "performance": "performance_testing_metrics.csv",
    "chaos": "chaos_testing_metrics.csv",
    "requirements": "requirements_metrics.csv",
    "uat": "uat_metrics.csv",
}


# ---------------------------------------------------------------------------
# Precision rules per column-name pattern
# ---------------------------------------------------------------------------

# Columns whose values should be written as integers.
_INTEGER_KEYWORDS: list[str] = [
    "count",
    "number of",
    "commits",
    "pull requests",
    "builds",
    "scenarios executed",
    "test cases",
    "lines of code",
    "dependency updates",
    "concurrent users",
    "peak load",
    "security vulnerabilities",
    "number of requirements",
    "build security scan results",
]

# Columns whose values get 2-decimal precision (scores, densities, rates < 1).
_TWO_DECIMAL_KEYWORDS: list[str] = [
    "score",
    "density",
    "defect detection rate",
    "defect rate",
    "requirements density",
]


def _precision_for_column(col_name: str) -> Optional[int]:
    """Return the number of decimal places for a column, or None for int."""
    col_lower = col_name.lower()
    for kw in _INTEGER_KEYWORDS:
        if kw in col_lower:
            return None  # integer
    for kw in _TWO_DECIMAL_KEYWORDS:
        if kw in col_lower:
            return 2
    # Default: 1 decimal place (percentages, times, sizes, etc.)
    return 1


# ---------------------------------------------------------------------------
# Release name / description templates
# ---------------------------------------------------------------------------

_RELEASE_ADJECTIVES: list[str] = [
    "Stable", "Enhanced", "Optimized", "Hardened", "Streamlined",
    "Refined", "Fortified", "Accelerated", "Resilient", "Polished",
    "Robust", "Agile", "Reliable", "Secure", "Scalable",
    "Efficient", "Modern", "Unified", "Dynamic", "Balanced",
]

_MAJOR_DESCRIPTIONS: list[str] = [
    "Major platform release with new features and architectural improvements.",
    "Significant feature additions and infrastructure enhancements.",
    "New capabilities across multiple modules with expanded coverage.",
    "Platform-wide improvements with new service integrations.",
    "Major milestone introducing foundational system changes.",
    "Broad feature release with performance and stability gains.",
    "Large-scale update with new APIs and service expansions.",
    "Comprehensive update spanning compute, storage, and networking layers.",
    "Feature-rich release with cross-cutting quality improvements.",
    "Strategic release delivering new business-critical functionality.",
]

_MINOR_DESCRIPTIONS: list[str] = [
    "Incremental improvements and minor feature refinements.",
    "Targeted enhancements to existing modules and services.",
    "Quality-of-life improvements and configuration optimizations.",
    "Minor feature additions and dependency updates.",
    "Focused improvements to monitoring and observability.",
    "Service stability improvements and minor bug fixes.",
    "Usability enhancements and performance tuning.",
    "Iterative improvements based on operational feedback.",
]

_PATCH_DESCRIPTIONS: list[str] = [
    "Critical bug fixes and stability improvements.",
    "Hotfix addressing production issues and edge cases.",
    "Targeted patches for recently identified defects.",
    "Security patches and vulnerability remediation.",
    "Performance regression fixes and memory optimizations.",
    "Patch release resolving customer-reported issues.",
    "Bug fixes improving reliability under high load.",
    "Maintenance patch with dependency security updates.",
]


# ---------------------------------------------------------------------------
# DataExporter
# ---------------------------------------------------------------------------


class DataExporter:
    """Export synthetic SDLC metric DataFrames to CSV files.

    Creates a directory structure matching the existing PRESTO project
    layout and writes each SDLC phase as a separate CSV with exact
    column names, date formatting, and numeric precision.

    Parameters
    ----------
    output_dir : str
        Root directory under which domain-specific subdirectories are created.
    """

    def __init__(self, output_dir: str) -> None:
        self.output_dir = Path(output_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def export_dataset(
        self,
        data: dict[str, pd.DataFrame],
        domain_name: str,
    ) -> Path:
        """Export a complete dataset (all phases) to CSV files.

        Parameters
        ----------
        data : dict[str, pd.DataFrame]
            Mapping of phase name to DataFrame. Expected keys are a subset of:
            ``'production'``, ``'build'``, ``'code'``, ``'test'``,
            ``'performance'``, ``'chaos'``, ``'requirements'``, ``'uat'``.
        domain_name : str
            Domain identifier used as the subdirectory name (e.g.,
            ``'abc-cloud-provider'``).

        Returns
        -------
        Path
            Absolute path to the output directory containing the CSVs.
        """
        domain_dir = self.output_dir / domain_name
        domain_dir.mkdir(parents=True, exist_ok=True)

        for phase_key, df in data.items():
            filename = PHASE_FILE_MAP.get(phase_key)
            if filename is None:
                raise ValueError(
                    f"Unknown phase key '{phase_key}'. "
                    f"Expected one of: {list(PHASE_FILE_MAP.keys())}"
                )
            output_path = domain_dir / filename
            self._write_csv(df, output_path)

        return domain_dir

    def generate_release_data(
        self,
        n_releases: int,
        start_date: str,
        release_freq_days: int = 14,
        seed: int = 42,
    ) -> pd.DataFrame:
        """Generate a release-data.csv DataFrame with semantic versioning.

        Parameters
        ----------
        n_releases : int
            Total number of releases to generate.
        start_date : str
            ISO-format start date (YYYY-MM-DD) for the first release.
        release_freq_days : int
            Average number of days between releases. Actual spacing varies
            slightly: patches come sooner (3-7 days after their parent),
            minors at roughly the given frequency, majors at 1-2x frequency.
        seed : int
            Random seed for reproducible type assignment and naming.

        Returns
        -------
        pd.DataFrame
            DataFrame with columns: Date, Release Number, Type, Name,
            Description.
        """
        rng = np.random.default_rng(seed)
        base_date = pd.Timestamp(start_date)

        # Assign release types with target distribution:
        # ~15% Major, ~50% Minor, ~35% Patch
        # Constraint: first release is always Major; patches follow a
        # Major or Minor (never two patches in a row).
        types: list[str] = []
        for i in range(n_releases):
            if i == 0:
                types.append("Major")
                continue
            prev_type = types[-1]
            roll = rng.random()
            if prev_type == "Patch":
                # After a patch, next is Major or Minor (no consecutive patches)
                types.append("Major" if roll < 0.25 else "Minor")
            else:
                if roll < 0.15:
                    types.append("Major")
                elif roll < 0.65:
                    types.append("Minor")
                else:
                    types.append("Patch")

        # Generate semantic version numbers
        versions = _generate_versions(types)

        # Generate dates with type-aware spacing
        dates: list[pd.Timestamp] = [base_date]
        for i in range(1, n_releases):
            rtype = types[i]
            if rtype == "Patch":
                gap = int(rng.integers(3, 8))  # 3-7 days
            elif rtype == "Minor":
                gap = int(rng.integers(
                    max(7, release_freq_days - 4),
                    release_freq_days + 5,
                ))
            else:
                # Major releases spaced further apart
                gap = int(rng.integers(release_freq_days, release_freq_days * 2 + 1))
            dates.append(dates[-1] + pd.Timedelta(days=gap))

        # Generate names and descriptions
        names: list[str] = []
        descriptions: list[str] = []
        adj_pool = list(_RELEASE_ADJECTIVES)
        rng.shuffle(adj_pool)

        for i, rtype in enumerate(types):
            adj = adj_pool[i % len(adj_pool)]
            version_short = versions[i].replace(".", "-")
            names.append(f"{adj} Release {version_short}")

            if rtype == "Major":
                desc = rng.choice(_MAJOR_DESCRIPTIONS)
            elif rtype == "Minor":
                desc = rng.choice(_MINOR_DESCRIPTIONS)
            else:
                desc = rng.choice(_PATCH_DESCRIPTIONS)
            descriptions.append(str(desc))

        return pd.DataFrame({
            "Date": [d.strftime("%Y-%m-%d") for d in dates],
            "Release Number": versions,
            "Type": types,
            "Name": names,
            "Description": descriptions,
        })

    def save_metadata(self, domain_name: str, metadata: dict) -> None:
        """Save generation metadata as JSON for reproducibility.

        Parameters
        ----------
        domain_name : str
            Domain subdirectory name.
        metadata : dict
            Arbitrary metadata (seed, parameters, timestamp, etc.).
            A ``generated_at`` field is added automatically if not present.
        """
        domain_dir = self.output_dir / domain_name
        domain_dir.mkdir(parents=True, exist_ok=True)

        meta = dict(metadata)
        if "generated_at" not in meta:
            meta["generated_at"] = datetime.utcnow().isoformat() + "Z"

        output_path = domain_dir / "generation_metadata.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, default=str)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _write_csv(df: pd.DataFrame, path: Path) -> None:
        """Write a DataFrame to CSV with correct formatting.

        - Date column: YYYY-MM-DD string (no time component).
        - Integer columns: no decimal point.
        - Score/density columns: 2 decimal places.
        - All other numeric columns: 1 decimal place.
        - No index column in output.
        """
        formatted = df.copy()

        # Ensure Date column is a clean date string
        if "Date" in formatted.columns:
            formatted["Date"] = pd.to_datetime(formatted["Date"]).dt.strftime(
                "%Y-%m-%d"
            )

        # Apply per-column precision
        skip_cols = {"Date", "Release Number", "Type", "Name", "Description"}
        for col in formatted.columns:
            if col in skip_cols:
                continue
            if not pd.api.types.is_numeric_dtype(formatted[col]):
                continue

            precision = _precision_for_column(col)
            if precision is None:
                # Integer column
                formatted[col] = formatted[col].round(0).astype(int)
            else:
                formatted[col] = formatted[col].round(precision)

        formatted.to_csv(path, index=False)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _generate_versions(types: list[str]) -> list[str]:
    """Generate semantic version strings from a sequence of release types.

    Rules:
    - Major increments the first number, resets second and third to 0.
    - Minor increments the second number, resets third to 0.
    - Patch increments the third number.

    The first release is always treated as the initial version (1.0.0).
    """
    major = 0
    minor = 0
    patch = 0
    versions: list[str] = []

    for i, rtype in enumerate(types):
        if i == 0:
            major = 1
            minor = 0
            patch = 0
        elif rtype == "Major":
            major += 1
            minor = 0
            patch = 0
        elif rtype == "Minor":
            minor += 1
            patch = 0
        else:
            patch += 1
        versions.append(f"{major}.{minor}.{patch}")

    return versions
