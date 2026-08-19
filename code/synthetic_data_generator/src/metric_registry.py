"""
Metric Registry for the PRESTO Synthetic Data Generator.

Defines all 178 SDLC metrics used in the PRESTO framework, organized by
phase. Each metric includes its statistical distribution specification
calibrated against observed reference data from three real-world projects.

Column names match the existing CSV files exactly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class Phase(Enum):
    """SDLC phases tracked by the PRESTO framework."""

    PRODUCTION = "production"
    BUILD = "build"
    CODE = "code"
    TEST = "test"
    PERFORMANCE_TEST = "performance_test"
    CHAOS = "chaos"
    REQUIREMENTS = "requirements"
    UAT = "uat"


class DistributionType(Enum):
    """Supported statistical distribution types for metric generation."""

    BETA = "beta"
    TRUNCATED_NORMAL = "truncated_normal"
    LOGNORMAL = "lognormal"
    POISSON = "poisson"
    GAMMA = "gamma"
    NEGATIVE_BINOMIAL = "negative_binomial"


@dataclass(frozen=True)
class MetricDefinition:
    """Immutable definition of a single SDLC metric.

    Attributes:
        name: Column name matching existing CSV headers exactly.
        phase: SDLC phase this metric belongs to.
        distribution_type: Statistical distribution used for generation.
        params: Distribution-specific parameters. Keys vary by type:
            - beta: a, b (shape parameters for scipy.stats.beta)
            - truncated_normal: mu, sigma, low, high
            - lognormal: mu, sigma (of the underlying normal)
            - poisson: lam (lambda, the rate parameter)
            - gamma: shape, scale
            - negative_binomial: n, p
        bounds: (min_value, max_value) hard clipping bounds.
        unit: Human-readable unit string.
        high_importance: Whether this metric has strong correlation
            with the target variable (System Uptime).
    """

    name: str
    phase: Phase
    distribution_type: DistributionType
    params: Dict[str, float]
    bounds: Tuple[float, float]
    unit: str
    high_importance: bool = False


# ---------------------------------------------------------------------------
# Target metric constant
# ---------------------------------------------------------------------------
TARGET_METRIC_NAME = "System Uptime (%)"

# ---------------------------------------------------------------------------
# Production Run Metrics (20 metrics, excluding Date and Release Number)
# ---------------------------------------------------------------------------
_PRODUCTION_METRICS: List[MetricDefinition] = [
    MetricDefinition(
        name="Production Deployment Success Rate (%)",
        phase=Phase.PRODUCTION,
        distribution_type=DistributionType.BETA,
        params={"a": 6.0, "b": 1.5},
        bounds=(60.0, 100.0),
        unit="%",
        high_importance=True,
    ),
    MetricDefinition(
        name="Mean Time to Recovery (MTTR) (Minutes)",
        phase=Phase.PRODUCTION,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 2.8, "sigma": 0.7},
        bounds=(0.0, 120.0),
        unit="minutes",
        high_importance=True,
    ),
    MetricDefinition(
        name="System Uptime (%)",
        phase=Phase.PRODUCTION,
        distribution_type=DistributionType.BETA,
        params={"a": 15.0, "b": 1.0},
        bounds=(85.0, 100.0),
        unit="%",
        high_importance=True,
    ),
    MetricDefinition(
        name="Performance SLA Compliance (%)",
        phase=Phase.PRODUCTION,
        distribution_type=DistributionType.BETA,
        params={"a": 5.0, "b": 1.2},
        bounds=(60.0, 100.0),
        unit="%",
        high_importance=True,
    ),
    MetricDefinition(
        name="Production Incident Count",
        phase=Phase.PRODUCTION,
        distribution_type=DistributionType.POISSON,
        params={"lam": 8.0},
        bounds=(0.0, 50.0),
        unit="count",
        high_importance=True,
    ),
    MetricDefinition(
        name="Critical Issue Resolution Time (Hours)",
        phase=Phase.PRODUCTION,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 1.0, "sigma": 0.7},
        bounds=(0.0, 24.0),
        unit="hours",
        high_importance=True,
    ),
    MetricDefinition(
        name="Customer Satisfaction Score (1-10)",
        phase=Phase.PRODUCTION,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 8.1, "sigma": 1.4, "low": 1.0, "high": 10.0},
        bounds=(1.0, 10.0),
        unit="score",
        high_importance=False,
    ),
    MetricDefinition(
        name="Business Value Delivered Score (1-10)",
        phase=Phase.PRODUCTION,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 7.8, "sigma": 1.4, "low": 1.0, "high": 10.0},
        bounds=(1.0, 10.0),
        unit="score",
    ),
    MetricDefinition(
        name="Production Monitoring Coverage (%)",
        phase=Phase.PRODUCTION,
        distribution_type=DistributionType.BETA,
        params={"a": 5.5, "b": 1.2},
        bounds=(60.0, 100.0),
        unit="%",
        high_importance=True,
    ),
    MetricDefinition(
        name="Rollback Rate (%)",
        phase=Phase.PRODUCTION,
        distribution_type=DistributionType.GAMMA,
        params={"shape": 1.2, "scale": 6.0},
        bounds=(0.0, 50.0),
        unit="%",
        high_importance=True,
    ),
    MetricDefinition(
        name="Production Data Quality Score (1-10)",
        phase=Phase.PRODUCTION,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 7.9, "sigma": 1.4, "low": 1.0, "high": 10.0},
        bounds=(1.0, 10.0),
        unit="score",
    ),
    MetricDefinition(
        name="Feature Adoption Rate (%)",
        phase=Phase.PRODUCTION,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 76.0, "sigma": 15.0, "low": 30.0, "high": 100.0},
        bounds=(30.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Performance Baseline Achievement (%)",
        phase=Phase.PRODUCTION,
        distribution_type=DistributionType.BETA,
        params={"a": 5.0, "b": 1.3},
        bounds=(55.0, 100.0),
        unit="%",
        high_importance=True,
    ),
    MetricDefinition(
        name="Production Test Coverage (%)",
        phase=Phase.PRODUCTION,
        distribution_type=DistributionType.BETA,
        params={"a": 4.5, "b": 1.3},
        bounds=(50.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Production Environment Health Score (1-10)",
        phase=Phase.PRODUCTION,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 8.3, "sigma": 1.3, "low": 1.0, "high": 10.0},
        bounds=(1.0, 10.0),
        unit="score",
        high_importance=True,
    ),
    MetricDefinition(
        name="Change Failure Rate (%)",
        phase=Phase.PRODUCTION,
        distribution_type=DistributionType.GAMMA,
        params={"shape": 1.3, "scale": 7.0},
        bounds=(0.0, 50.0),
        unit="%",
        high_importance=True,
    ),
    MetricDefinition(
        name="Lead Time for Changes (Hours)",
        phase=Phase.PRODUCTION,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 3.2, "sigma": 0.6},
        bounds=(0.0, 120.0),
        unit="hours",
    ),
    MetricDefinition(
        name="Deployment Frequency (Per Week)",
        phase=Phase.PRODUCTION,
        distribution_type=DistributionType.GAMMA,
        params={"shape": 3.0, "scale": 1.3},
        bounds=(0.5, 15.0),
        unit="deploys/week",
    ),
    MetricDefinition(
        name="Recovery Time from Failures (Minutes)",
        phase=Phase.PRODUCTION,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 2.9, "sigma": 0.7},
        bounds=(0.0, 120.0),
        unit="minutes",
        high_importance=True,
    ),
    MetricDefinition(
        name="Customer Issue Resolution Time (Hours)",
        phase=Phase.PRODUCTION,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 1.2, "sigma": 0.7},
        bounds=(0.0, 24.0),
        unit="hours",
    ),
]

# ---------------------------------------------------------------------------
# Build Metrics (20 metrics)
# ---------------------------------------------------------------------------
_BUILD_METRICS: List[MetricDefinition] = [
    MetricDefinition(
        name="Build Success Rate (%)",
        phase=Phase.BUILD,
        distribution_type=DistributionType.BETA,
        params={"a": 5.0, "b": 1.3},
        bounds=(50.0, 100.0),
        unit="%",
        high_importance=True,
    ),
    MetricDefinition(
        name="Successful Builds",
        phase=Phase.BUILD,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 5.5, "sigma": 0.6},
        bounds=(10.0, 1000.0),
        unit="count",
    ),
    MetricDefinition(
        name="Failed Builds",
        phase=Phase.BUILD,
        distribution_type=DistributionType.POISSON,
        params={"lam": 15.0},
        bounds=(0.0, 80.0),
        unit="count",
    ),
    MetricDefinition(
        name="Build Frequency (Builds/Day)",
        phase=Phase.BUILD,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 2.8, "sigma": 0.6},
        bounds=(1.0, 80.0),
        unit="builds/day",
    ),
    MetricDefinition(
        name="Deployment Frequency (Deploys/Day)",
        phase=Phase.BUILD,
        distribution_type=DistributionType.GAMMA,
        params={"shape": 3.0, "scale": 0.75},
        bounds=(0.1, 10.0),
        unit="deploys/day",
    ),
    MetricDefinition(
        name="Average Deploy Time (Minutes)",
        phase=Phase.BUILD,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 3.4, "sigma": 0.6},
        bounds=(1.0, 180.0),
        unit="minutes",
    ),
    MetricDefinition(
        name="Build Duration (Minutes)",
        phase=Phase.BUILD,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 3.0, "sigma": 0.6},
        bounds=(1.0, 120.0),
        unit="minutes",
        high_importance=True,
    ),
    MetricDefinition(
        name="Build Queue Time (Minutes)",
        phase=Phase.BUILD,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 2.0, "sigma": 0.7},
        bounds=(0.0, 60.0),
        unit="minutes",
    ),
    MetricDefinition(
        name="Build Cache Hit Rate (%)",
        phase=Phase.BUILD,
        distribution_type=DistributionType.BETA,
        params={"a": 4.0, "b": 1.5},
        bounds=(30.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Artifact Size (MB)",
        phase=Phase.BUILD,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 5.2, "sigma": 0.6},
        bounds=(10.0, 1000.0),
        unit="MB",
    ),
    MetricDefinition(
        name="Dependency Updates",
        phase=Phase.BUILD,
        distribution_type=DistributionType.POISSON,
        params={"lam": 40.0},
        bounds=(0.0, 200.0),
        unit="count",
    ),
    MetricDefinition(
        name="Time to Fix Build Failures (Hours)",
        phase=Phase.BUILD,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 1.0, "sigma": 0.8},
        bounds=(0.0, 48.0),
        unit="hours",
        high_importance=True,
    ),
    MetricDefinition(
        name="Build Reproducibility Rate (%)",
        phase=Phase.BUILD,
        distribution_type=DistributionType.BETA,
        params={"a": 5.0, "b": 1.2},
        bounds=(50.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Artifact Promotion Rate (%)",
        phase=Phase.BUILD,
        distribution_type=DistributionType.BETA,
        params={"a": 4.5, "b": 1.3},
        bounds=(45.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Build Cost (USD)",
        phase=Phase.BUILD,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 4.3, "sigma": 0.9},
        bounds=(0.0, 800.0),
        unit="USD",
    ),
    MetricDefinition(
        name="Build Environment Consistency (%)",
        phase=Phase.BUILD,
        distribution_type=DistributionType.BETA,
        params={"a": 5.5, "b": 1.2},
        bounds=(50.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Build Rollback Frequency (Rollbacks/Month)",
        phase=Phase.BUILD,
        distribution_type=DistributionType.GAMMA,
        params={"shape": 1.0, "scale": 2.3},
        bounds=(0.0, 20.0),
        unit="rollbacks/month",
    ),
    MetricDefinition(
        name="Build Security Scan Results (Issues)",
        phase=Phase.BUILD,
        distribution_type=DistributionType.POISSON,
        params={"lam": 7.5},
        bounds=(0.0, 60.0),
        unit="count",
    ),
    MetricDefinition(
        name="Build Artifact Integrity (%)",
        phase=Phase.BUILD,
        distribution_type=DistributionType.BETA,
        params={"a": 8.0, "b": 1.0},
        bounds=(60.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Build Pipeline Efficiency (%)",
        phase=Phase.BUILD,
        distribution_type=DistributionType.BETA,
        params={"a": 4.5, "b": 1.3},
        bounds=(40.0, 100.0),
        unit="%",
        high_importance=True,
    ),
]

# ---------------------------------------------------------------------------
# Code Metrics (24 metrics)
# ---------------------------------------------------------------------------
_CODE_METRICS: List[MetricDefinition] = [
    MetricDefinition(
        name="Cyclomatic Complexity",
        phase=Phase.CODE,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 2.5, "sigma": 0.5},
        bounds=(1.0, 50.0),
        unit="complexity",
        high_importance=True,
    ),
    MetricDefinition(
        name="Code Smells",
        phase=Phase.CODE,
        distribution_type=DistributionType.NEGATIVE_BINOMIAL,
        params={"n": 3.0, "p": 0.03},
        bounds=(0.0, 500.0),
        unit="count",
    ),
    MetricDefinition(
        name="Lines of Code",
        phase=Phase.CODE,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 10.7, "sigma": 0.5},
        bounds=(5000.0, 250000.0),
        unit="LOC",
    ),
    MetricDefinition(
        name="Unit Test Coverage (%)",
        phase=Phase.CODE,
        distribution_type=DistributionType.BETA,
        params={"a": 5.0, "b": 1.2},
        bounds=(50.0, 100.0),
        unit="%",
        high_importance=True,
    ),
    MetricDefinition(
        name="Integration Test Coverage (%)",
        phase=Phase.CODE,
        distribution_type=DistributionType.BETA,
        params={"a": 3.5, "b": 1.5},
        bounds=(35.0, 100.0),
        unit="%",
        high_importance=True,
    ),
    MetricDefinition(
        name="Static Analysis Issues",
        phase=Phase.CODE,
        distribution_type=DistributionType.NEGATIVE_BINOMIAL,
        params={"n": 2.5, "p": 0.02},
        bounds=(0.0, 800.0),
        unit="count",
    ),
    MetricDefinition(
        name="Number of Commits",
        phase=Phase.CODE,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 5.5, "sigma": 0.6},
        bounds=(10.0, 1000.0),
        unit="count",
    ),
    MetricDefinition(
        name="Commits per Release",
        phase=Phase.CODE,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 5.5, "sigma": 0.6},
        bounds=(10.0, 1000.0),
        unit="count",
    ),
    MetricDefinition(
        name="Commit Frequency (Commits/Day)",
        phase=Phase.CODE,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 2.8, "sigma": 0.6},
        bounds=(1.0, 80.0),
        unit="commits/day",
    ),
    MetricDefinition(
        name="Pull Requests Merged",
        phase=Phase.CODE,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 3.8, "sigma": 0.6},
        bounds=(5.0, 200.0),
        unit="count",
    ),
    MetricDefinition(
        name="Pull Requests Declined",
        phase=Phase.CODE,
        distribution_type=DistributionType.POISSON,
        params={"lam": 2.5},
        bounds=(0.0, 15.0),
        unit="count",
    ),
    MetricDefinition(
        name="Code Review Comments",
        phase=Phase.CODE,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 5.3, "sigma": 0.5},
        bounds=(20.0, 1000.0),
        unit="count",
    ),
    MetricDefinition(
        name="Defects Identified (Unit)",
        phase=Phase.CODE,
        distribution_type=DistributionType.POISSON,
        params={"lam": 8.0},
        bounds=(0.0, 50.0),
        unit="count",
    ),
    MetricDefinition(
        name="Defects Identified (Integration)",
        phase=Phase.CODE,
        distribution_type=DistributionType.POISSON,
        params={"lam": 5.0},
        bounds=(0.0, 40.0),
        unit="count",
    ),
    MetricDefinition(
        name="Defects Identified (UAT)",
        phase=Phase.CODE,
        distribution_type=DistributionType.POISSON,
        params={"lam": 10.0},
        bounds=(0.0, 60.0),
        unit="count",
    ),
    MetricDefinition(
        name="Defects Reopened",
        phase=Phase.CODE,
        distribution_type=DistributionType.POISSON,
        params={"lam": 3.0},
        bounds=(0.0, 30.0),
        unit="count",
    ),
    MetricDefinition(
        name="Time to Resolve Defects (Hours)",
        phase=Phase.CODE,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 2.6, "sigma": 0.7},
        bounds=(0.0, 80.0),
        unit="hours",
    ),
    MetricDefinition(
        name="Code Review Turnaround Time (Hours)",
        phase=Phase.CODE,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 1.5, "sigma": 0.6},
        bounds=(0.0, 30.0),
        unit="hours",
    ),
    MetricDefinition(
        name="Defect Density (Defects/KLOC)",
        phase=Phase.CODE,
        distribution_type=DistributionType.GAMMA,
        params={"shape": 1.5, "scale": 1.1},
        bounds=(0.0, 10.0),
        unit="defects/KLOC",
        high_importance=True,
    ),
    MetricDefinition(
        name="Security Vulnerabilities",
        phase=Phase.CODE,
        distribution_type=DistributionType.POISSON,
        params={"lam": 4.0},
        bounds=(0.0, 40.0),
        unit="count",
        high_importance=True,
    ),
    MetricDefinition(
        name="Technical Debt (Hours)",
        phase=Phase.CODE,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 4.5, "sigma": 0.9},
        bounds=(0.0, 1000.0),
        unit="hours",
    ),
    MetricDefinition(
        name="Code Coverage Pass Rate (%)",
        phase=Phase.CODE,
        distribution_type=DistributionType.BETA,
        params={"a": 5.5, "b": 1.2},
        bounds=(50.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Code Duplication Rate (%)",
        phase=Phase.CODE,
        distribution_type=DistributionType.GAMMA,
        params={"shape": 1.8, "scale": 4.3},
        bounds=(0.0, 35.0),
        unit="%",
    ),
    MetricDefinition(
        name="Dead Code Percentage (%)",
        phase=Phase.CODE,
        distribution_type=DistributionType.GAMMA,
        params={"shape": 1.5, "scale": 1.7},
        bounds=(0.0, 15.0),
        unit="%",
    ),
]

# ---------------------------------------------------------------------------
# Test Metrics (21 metrics)
# ---------------------------------------------------------------------------
_TEST_METRICS: List[MetricDefinition] = [
    MetricDefinition(
        name="Unit Test Coverage (%)",
        phase=Phase.TEST,
        distribution_type=DistributionType.BETA,
        params={"a": 6.0, "b": 1.2},
        bounds=(60.0, 100.0),
        unit="%",
        high_importance=True,
    ),
    MetricDefinition(
        name="Integration Test Coverage (%)",
        phase=Phase.TEST,
        distribution_type=DistributionType.BETA,
        params={"a": 4.0, "b": 1.4},
        bounds=(45.0, 100.0),
        unit="%",
        high_importance=True,
    ),
    MetricDefinition(
        name="Contract Test Coverage (%)",
        phase=Phase.TEST,
        distribution_type=DistributionType.BETA,
        params={"a": 4.5, "b": 1.3},
        bounds=(50.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Security Test Issues",
        phase=Phase.TEST,
        distribution_type=DistributionType.POISSON,
        params={"lam": 6.0},
        bounds=(0.0, 40.0),
        unit="count",
    ),
    MetricDefinition(
        name="UAT Pass Rate (%)",
        phase=Phase.TEST,
        distribution_type=DistributionType.BETA,
        params={"a": 5.5, "b": 1.2},
        bounds=(55.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Test Cases Executed",
        phase=Phase.TEST,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 7.0, "sigma": 0.5},
        bounds=(100.0, 5000.0),
        unit="count",
    ),
    MetricDefinition(
        name="Test Pass Rate (%)",
        phase=Phase.TEST,
        distribution_type=DistributionType.BETA,
        params={"a": 8.0, "b": 1.0},
        bounds=(65.0, 100.0),
        unit="%",
        high_importance=True,
    ),
    MetricDefinition(
        name="Defect Detection Rate (Defects/Test)",
        phase=Phase.TEST,
        distribution_type=DistributionType.GAMMA,
        params={"shape": 1.5, "scale": 0.07},
        bounds=(0.0, 0.5),
        unit="defects/test",
    ),
    MetricDefinition(
        name="Time to Resolve Test Defects (Hours)",
        phase=Phase.TEST,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 2.2, "sigma": 0.6},
        bounds=(0.0, 50.0),
        unit="hours",
    ),
    MetricDefinition(
        name="Automated Test Ratio (%)",
        phase=Phase.TEST,
        distribution_type=DistributionType.BETA,
        params={"a": 4.0, "b": 1.4},
        bounds=(40.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Regression Test Pass Rate (%)",
        phase=Phase.TEST,
        distribution_type=DistributionType.BETA,
        params={"a": 9.0, "b": 1.0},
        bounds=(65.0, 100.0),
        unit="%",
        high_importance=True,
    ),
    MetricDefinition(
        name="Test Flakiness Rate (%)",
        phase=Phase.TEST,
        distribution_type=DistributionType.GAMMA,
        params={"shape": 1.2, "scale": 2.8},
        bounds=(0.0, 20.0),
        unit="%",
    ),
    MetricDefinition(
        name="Test Suite Execution Time (Minutes)",
        phase=Phase.TEST,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 3.7, "sigma": 0.5},
        bounds=(1.0, 200.0),
        unit="minutes",
    ),
    MetricDefinition(
        name="Defect Leakage (%)",
        phase=Phase.TEST,
        distribution_type=DistributionType.GAMMA,
        params={"shape": 1.5, "scale": 3.6},
        bounds=(0.0, 25.0),
        unit="%",
        high_importance=True,
    ),
    MetricDefinition(
        name="Test Environment Availability (%)",
        phase=Phase.TEST,
        distribution_type=DistributionType.BETA,
        params={"a": 10.0, "b": 1.0},
        bounds=(75.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Test Data Quality Score (1-10)",
        phase=Phase.TEST,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 8.6, "sigma": 1.2, "low": 1.0, "high": 10.0},
        bounds=(1.0, 10.0),
        unit="score",
    ),
    MetricDefinition(
        name="Test Automation Coverage (%)",
        phase=Phase.TEST,
        distribution_type=DistributionType.BETA,
        params={"a": 5.0, "b": 1.2},
        bounds=(50.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Test Maintenance Effort (Hours/Week)",
        phase=Phase.TEST,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 2.0, "sigma": 0.7},
        bounds=(0.0, 50.0),
        unit="hours/week",
    ),
    MetricDefinition(
        name="Test Stability Index (1-10)",
        phase=Phase.TEST,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 8.6, "sigma": 1.2, "low": 1.0, "high": 10.0},
        bounds=(1.0, 10.0),
        unit="score",
    ),
    MetricDefinition(
        name="API Test Coverage (%)",
        phase=Phase.TEST,
        distribution_type=DistributionType.BETA,
        params={"a": 6.0, "b": 1.2},
        bounds=(55.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Performance Test Coverage (%)",
        phase=Phase.TEST,
        distribution_type=DistributionType.BETA,
        params={"a": 3.5, "b": 1.3},
        bounds=(40.0, 100.0),
        unit="%",
    ),
]

# ---------------------------------------------------------------------------
# Performance Testing Metrics (20 metrics)
# ---------------------------------------------------------------------------
_PERFORMANCE_TEST_METRICS: List[MetricDefinition] = [
    MetricDefinition(
        name="Response Time (ms)",
        phase=Phase.PERFORMANCE_TEST,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 5.1, "sigma": 0.6},
        bounds=(1.0, 1000.0),
        unit="ms",
        high_importance=True,
    ),
    MetricDefinition(
        name="Throughput (RPS)",
        phase=Phase.PERFORMANCE_TEST,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 7.5, "sigma": 0.8},
        bounds=(100.0, 100000.0),
        unit="RPS",
        high_importance=True,
    ),
    MetricDefinition(
        name="Latency (ms)",
        phase=Phase.PERFORMANCE_TEST,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 4.0, "sigma": 0.6},
        bounds=(1.0, 500.0),
        unit="ms",
        high_importance=True,
    ),
    MetricDefinition(
        name="Concurrent Users",
        phase=Phase.PERFORMANCE_TEST,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 8.2, "sigma": 0.8},
        bounds=(100.0, 150000.0),
        unit="users",
    ),
    MetricDefinition(
        name="Error Rate (%)",
        phase=Phase.PERFORMANCE_TEST,
        distribution_type=DistributionType.GAMMA,
        params={"shape": 1.2, "scale": 1.2},
        bounds=(0.0, 10.0),
        unit="%",
        high_importance=True,
    ),
    MetricDefinition(
        name="CPU Utilization (%)",
        phase=Phase.PERFORMANCE_TEST,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 60.0, "sigma": 20.0, "low": 0.0, "high": 100.0},
        bounds=(0.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Memory Utilization (%)",
        phase=Phase.PERFORMANCE_TEST,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 64.0, "sigma": 20.0, "low": 0.0, "high": 100.0},
        bounds=(0.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Disk Utilization (%)",
        phase=Phase.PERFORMANCE_TEST,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 40.0, "sigma": 19.0, "low": 0.0, "high": 100.0},
        bounds=(0.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Network Utilization (%)",
        phase=Phase.PERFORMANCE_TEST,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 47.0, "sigma": 19.0, "low": 0.0, "high": 100.0},
        bounds=(0.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Peak Load (Users)",
        phase=Phase.PERFORMANCE_TEST,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 8.5, "sigma": 0.8},
        bounds=(500.0, 200000.0),
        unit="users",
    ),
    MetricDefinition(
        name="System Availability (%)",
        phase=Phase.PERFORMANCE_TEST,
        distribution_type=DistributionType.BETA,
        params={"a": 12.0, "b": 1.0},
        bounds=(80.0, 100.0),
        unit="%",
        high_importance=True,
    ),
    MetricDefinition(
        name="Resiliency Score (1-10)",
        phase=Phase.PERFORMANCE_TEST,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 8.2, "sigma": 1.4, "low": 1.0, "high": 10.0},
        bounds=(1.0, 10.0),
        unit="score",
    ),
    MetricDefinition(
        name="SLA Compliance Rate (%)",
        phase=Phase.PERFORMANCE_TEST,
        distribution_type=DistributionType.BETA,
        params={"a": 7.0, "b": 1.0},
        bounds=(55.0, 100.0),
        unit="%",
        high_importance=True,
    ),
    MetricDefinition(
        name="Performance Baseline Deviation (%)",
        phase=Phase.PERFORMANCE_TEST,
        distribution_type=DistributionType.GAMMA,
        params={"shape": 1.3, "scale": 6.5},
        bounds=(0.0, 60.0),
        unit="%",
    ),
    MetricDefinition(
        name="Load Test Scenario Coverage (%)",
        phase=Phase.PERFORMANCE_TEST,
        distribution_type=DistributionType.BETA,
        params={"a": 4.5, "b": 1.2},
        bounds=(35.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Performance Test Automation Rate (%)",
        phase=Phase.PERFORMANCE_TEST,
        distribution_type=DistributionType.BETA,
        params={"a": 3.5, "b": 1.3},
        bounds=(30.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Cache Hit Ratio (%)",
        phase=Phase.PERFORMANCE_TEST,
        distribution_type=DistributionType.BETA,
        params={"a": 5.0, "b": 1.3},
        bounds=(40.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Performance Regression Detection Rate (%)",
        phase=Phase.PERFORMANCE_TEST,
        distribution_type=DistributionType.BETA,
        params={"a": 5.5, "b": 1.2},
        bounds=(45.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Real User Monitoring Correlation (%)",
        phase=Phase.PERFORMANCE_TEST,
        distribution_type=DistributionType.BETA,
        params={"a": 5.0, "b": 1.3},
        bounds=(40.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Performance Test Coverage per Feature (%)",
        phase=Phase.PERFORMANCE_TEST,
        distribution_type=DistributionType.BETA,
        params={"a": 4.0, "b": 1.3},
        bounds=(35.0, 100.0),
        unit="%",
    ),
]

# ---------------------------------------------------------------------------
# Chaos Testing Metrics (20 metrics)
# ---------------------------------------------------------------------------
_CHAOS_METRICS: List[MetricDefinition] = [
    MetricDefinition(
        name="Chaos Test Scenarios Executed",
        phase=Phase.CHAOS,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 54.0, "sigma": 15.0, "low": 10.0, "high": 120.0},
        bounds=(10.0, 120.0),
        unit="count",
    ),
    MetricDefinition(
        name="Fault Injection Success Rate (%)",
        phase=Phase.CHAOS,
        distribution_type=DistributionType.BETA,
        params={"a": 4.5, "b": 1.3},
        bounds=(45.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="System Recovery Time (Minutes)",
        phase=Phase.CHAOS,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 1.2, "sigma": 0.6},
        bounds=(0.0, 30.0),
        unit="minutes",
        high_importance=True,
    ),
    MetricDefinition(
        name="Resilience Score (1-10)",
        phase=Phase.CHAOS,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 8.1, "sigma": 1.6, "low": 1.0, "high": 10.0},
        bounds=(1.0, 10.0),
        unit="score",
        high_importance=True,
    ),
    MetricDefinition(
        name="Service Degradation Response (%)",
        phase=Phase.CHAOS,
        distribution_type=DistributionType.BETA,
        params={"a": 3.5, "b": 1.4},
        bounds=(35.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Circuit Breaker Effectiveness (%)",
        phase=Phase.CHAOS,
        distribution_type=DistributionType.BETA,
        params={"a": 4.0, "b": 1.3},
        bounds=(40.0, 100.0),
        unit="%",
        high_importance=True,
    ),
    MetricDefinition(
        name="Mean Time to Recovery (MTTR) (Minutes)",
        phase=Phase.CHAOS,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 1.3, "sigma": 0.7},
        bounds=(0.0, 30.0),
        unit="minutes",
        high_importance=True,
    ),
    MetricDefinition(
        name="Service Mesh Stability (%)",
        phase=Phase.CHAOS,
        distribution_type=DistributionType.BETA,
        params={"a": 5.5, "b": 1.2},
        bounds=(55.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Load Balancer Effectiveness (%)",
        phase=Phase.CHAOS,
        distribution_type=DistributionType.BETA,
        params={"a": 4.5, "b": 1.2},
        bounds=(45.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Failover Success Rate (%)",
        phase=Phase.CHAOS,
        distribution_type=DistributionType.BETA,
        params={"a": 5.5, "b": 1.2},
        bounds=(50.0, 100.0),
        unit="%",
        high_importance=True,
    ),
    MetricDefinition(
        name="Data Consistency Under Chaos (%)",
        phase=Phase.CHAOS,
        distribution_type=DistributionType.BETA,
        params={"a": 6.0, "b": 1.1},
        bounds=(55.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Monitoring Alert Accuracy (%)",
        phase=Phase.CHAOS,
        distribution_type=DistributionType.BETA,
        params={"a": 5.0, "b": 1.2},
        bounds=(50.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Auto-scaling Response Time (Seconds)",
        phase=Phase.CHAOS,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 3.3, "sigma": 0.6},
        bounds=(0.0, 120.0),
        unit="seconds",
    ),
    MetricDefinition(
        name="Database Failover Time (Seconds)",
        phase=Phase.CHAOS,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 2.9, "sigma": 0.6},
        bounds=(0.0, 100.0),
        unit="seconds",
    ),
    MetricDefinition(
        name="Network Partition Tolerance (%)",
        phase=Phase.CHAOS,
        distribution_type=DistributionType.BETA,
        params={"a": 4.5, "b": 1.3},
        bounds=(45.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Chaos Engineering Coverage (%)",
        phase=Phase.CHAOS,
        distribution_type=DistributionType.BETA,
        params={"a": 3.5, "b": 1.4},
        bounds=(30.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Service Discovery Resilience (%)",
        phase=Phase.CHAOS,
        distribution_type=DistributionType.BETA,
        params={"a": 5.5, "b": 1.2},
        bounds=(55.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Graceful Degradation Score (1-10)",
        phase=Phase.CHAOS,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 8.2, "sigma": 1.6, "low": 1.0, "high": 10.0},
        bounds=(1.0, 10.0),
        unit="score",
    ),
    MetricDefinition(
        name="Blast Radius Containment (%)",
        phase=Phase.CHAOS,
        distribution_type=DistributionType.BETA,
        params={"a": 3.5, "b": 1.3},
        bounds=(40.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Error Budget Consumption (%)",
        phase=Phase.CHAOS,
        distribution_type=DistributionType.GAMMA,
        params={"shape": 1.5, "scale": 8.0},
        bounds=(0.0, 60.0),
        unit="%",
    ),
]

# ---------------------------------------------------------------------------
# Requirements Metrics (19 metrics)
# ---------------------------------------------------------------------------
_REQUIREMENTS_METRICS: List[MetricDefinition] = [
    MetricDefinition(
        name="Requirements Coverage (%)",
        phase=Phase.REQUIREMENTS,
        distribution_type=DistributionType.BETA,
        params={"a": 8.0, "b": 1.0},
        bounds=(75.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Requirements Completeness Score (1-10)",
        phase=Phase.REQUIREMENTS,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 8.8, "sigma": 1.0, "low": 1.0, "high": 10.0},
        bounds=(1.0, 10.0),
        unit="score",
    ),
    MetricDefinition(
        name="Requirements Clarity Index (1-10)",
        phase=Phase.REQUIREMENTS,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 8.4, "sigma": 1.1, "low": 1.0, "high": 10.0},
        bounds=(1.0, 10.0),
        unit="score",
    ),
    MetricDefinition(
        name="Requirements Stability Rate (%)",
        phase=Phase.REQUIREMENTS,
        distribution_type=DistributionType.BETA,
        params={"a": 5.0, "b": 1.3},
        bounds=(65.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Number of Requirements",
        phase=Phase.REQUIREMENTS,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 5.0, "sigma": 0.6},
        bounds=(10.0, 800.0),
        unit="count",
    ),
    MetricDefinition(
        name="Requirements Density (Req/Feature)",
        phase=Phase.REQUIREMENTS,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 2.1, "sigma": 0.5},
        bounds=(1.0, 40.0),
        unit="req/feature",
    ),
    MetricDefinition(
        name="Requirements Traceability (%)",
        phase=Phase.REQUIREMENTS,
        distribution_type=DistributionType.BETA,
        params={"a": 5.5, "b": 1.1},
        bounds=(70.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Requirements Validation Rate (%)",
        phase=Phase.REQUIREMENTS,
        distribution_type=DistributionType.BETA,
        params={"a": 6.0, "b": 1.1},
        bounds=(72.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Requirements Change Rate (Changes/Week)",
        phase=Phase.REQUIREMENTS,
        distribution_type=DistributionType.GAMMA,
        params={"shape": 2.3, "scale": 1.1},
        bounds=(0.0, 10.0),
        unit="changes/week",
    ),
    MetricDefinition(
        name="Requirements Review Cycle Time (Days)",
        phase=Phase.REQUIREMENTS,
        distribution_type=DistributionType.GAMMA,
        params={"shape": 2.5, "scale": 1.4},
        bounds=(0.0, 15.0),
        unit="days",
    ),
    MetricDefinition(
        name="Stakeholder Approval Rate (%)",
        phase=Phase.REQUIREMENTS,
        distribution_type=DistributionType.BETA,
        params={"a": 5.5, "b": 1.2},
        bounds=(65.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Requirements Defect Rate (Defects/Req)",
        phase=Phase.REQUIREMENTS,
        distribution_type=DistributionType.GAMMA,
        params={"shape": 1.5, "scale": 0.07},
        bounds=(0.0, 0.5),
        unit="defects/req",
    ),
    MetricDefinition(
        name="Requirements Ambiguity Score (1-10)",
        phase=Phase.REQUIREMENTS,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 2.6, "sigma": 1.3, "low": 0.0, "high": 10.0},
        bounds=(0.0, 10.0),
        unit="score",
    ),
    MetricDefinition(
        name="Business Value Score (1-10)",
        phase=Phase.REQUIREMENTS,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 8.7, "sigma": 0.9, "low": 1.0, "high": 10.0},
        bounds=(1.0, 10.0),
        unit="score",
    ),
    MetricDefinition(
        name="Requirements Prioritization Score (1-10)",
        phase=Phase.REQUIREMENTS,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 8.6, "sigma": 1.0, "low": 1.0, "high": 10.0},
        bounds=(1.0, 10.0),
        unit="score",
    ),
    MetricDefinition(
        name="Requirements Approval Time (Hours)",
        phase=Phase.REQUIREMENTS,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 2.4, "sigma": 0.7},
        bounds=(0.0, 60.0),
        unit="hours",
    ),
    MetricDefinition(
        name="Requirements Documentation Quality (1-10)",
        phase=Phase.REQUIREMENTS,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 8.5, "sigma": 1.0, "low": 1.0, "high": 10.0},
        bounds=(1.0, 10.0),
        unit="score",
    ),
    MetricDefinition(
        name="Stakeholder Engagement Level (1-10)",
        phase=Phase.REQUIREMENTS,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 8.5, "sigma": 0.9, "low": 1.0, "high": 10.0},
        bounds=(1.0, 10.0),
        unit="score",
    ),
    MetricDefinition(
        name="Requirements Testability Score (1-10)",
        phase=Phase.REQUIREMENTS,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 8.3, "sigma": 1.0, "low": 1.0, "high": 10.0},
        bounds=(1.0, 10.0),
        unit="score",
    ),
]

# ---------------------------------------------------------------------------
# UAT Metrics (20 metrics)
# ---------------------------------------------------------------------------
_UAT_METRICS: List[MetricDefinition] = [
    MetricDefinition(
        name="User Acceptance Pass Rate (%)",
        phase=Phase.UAT,
        distribution_type=DistributionType.BETA,
        params={"a": 5.0, "b": 1.3},
        bounds=(55.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Feature Acceptance Rate (%)",
        phase=Phase.UAT,
        distribution_type=DistributionType.BETA,
        params={"a": 4.5, "b": 1.3},
        bounds=(50.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Business Rule Validation Rate (%)",
        phase=Phase.UAT,
        distribution_type=DistributionType.BETA,
        params={"a": 3.5, "b": 1.3},
        bounds=(45.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="UAT Test Execution Rate (%)",
        phase=Phase.UAT,
        distribution_type=DistributionType.BETA,
        params={"a": 5.5, "b": 1.2},
        bounds=(60.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="User Satisfaction Score (1-10)",
        phase=Phase.UAT,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 8.1, "sigma": 1.3, "low": 1.0, "high": 10.0},
        bounds=(1.0, 10.0),
        unit="score",
    ),
    MetricDefinition(
        name="Business Value Realization Score (1-10)",
        phase=Phase.UAT,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 7.8, "sigma": 1.4, "low": 1.0, "high": 10.0},
        bounds=(1.0, 10.0),
        unit="score",
    ),
    MetricDefinition(
        name="UAT Cycle Time (Days)",
        phase=Phase.UAT,
        distribution_type=DistributionType.LOGNORMAL,
        params={"mu": 2.0, "sigma": 0.6},
        bounds=(0.0, 40.0),
        unit="days",
    ),
    MetricDefinition(
        name="UAT Defect Detection Rate (%)",
        phase=Phase.UAT,
        distribution_type=DistributionType.GAMMA,
        params={"shape": 1.8, "scale": 5.9},
        bounds=(0.0, 40.0),
        unit="%",
    ),
    MetricDefinition(
        name="Requirements Traceability Coverage (%)",
        phase=Phase.UAT,
        distribution_type=DistributionType.BETA,
        params={"a": 7.0, "b": 1.0},
        bounds=(65.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Sign-off Completion Rate (%)",
        phase=Phase.UAT,
        distribution_type=DistributionType.BETA,
        params={"a": 5.0, "b": 1.3},
        bounds=(55.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="User Training Completion Rate (%)",
        phase=Phase.UAT,
        distribution_type=DistributionType.BETA,
        params={"a": 4.0, "b": 1.3},
        bounds=(50.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="System Readiness Score (1-10)",
        phase=Phase.UAT,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 8.3, "sigma": 1.3, "low": 1.0, "high": 10.0},
        bounds=(1.0, 10.0),
        unit="score",
    ),
    MetricDefinition(
        name="UAT Environment Stability (%)",
        phase=Phase.UAT,
        distribution_type=DistributionType.BETA,
        params={"a": 9.0, "b": 1.0},
        bounds=(78.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Stakeholder Engagement Score (1-10)",
        phase=Phase.UAT,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 8.1, "sigma": 1.3, "low": 1.0, "high": 10.0},
        bounds=(1.0, 10.0),
        unit="score",
    ),
    MetricDefinition(
        name="UAT Test Data Quality Score (1-10)",
        phase=Phase.UAT,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 8.1, "sigma": 1.3, "low": 1.0, "high": 10.0},
        bounds=(1.0, 10.0),
        unit="score",
    ),
    MetricDefinition(
        name="Performance in UAT Environment (%)",
        phase=Phase.UAT,
        distribution_type=DistributionType.BETA,
        params={"a": 5.5, "b": 1.2},
        bounds=(60.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Regression Issues in UAT (%)",
        phase=Phase.UAT,
        distribution_type=DistributionType.GAMMA,
        params={"shape": 1.3, "scale": 4.5},
        bounds=(0.0, 30.0),
        unit="%",
    ),
    MetricDefinition(
        name="UAT Test Coverage (%)",
        phase=Phase.UAT,
        distribution_type=DistributionType.BETA,
        params={"a": 5.5, "b": 1.2},
        bounds=(55.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="Accessibility Compliance Rate (%)",
        phase=Phase.UAT,
        distribution_type=DistributionType.BETA,
        params={"a": 4.0, "b": 1.3},
        bounds=(50.0, 100.0),
        unit="%",
    ),
    MetricDefinition(
        name="UAT Documentation Quality Score (1-10)",
        phase=Phase.UAT,
        distribution_type=DistributionType.TRUNCATED_NORMAL,
        params={"mu": 8.0, "sigma": 1.4, "low": 1.0, "high": 10.0},
        bounds=(1.0, 10.0),
        unit="score",
    ),
]


# ---------------------------------------------------------------------------
# Phase-to-metrics mapping
# ---------------------------------------------------------------------------
_PHASE_METRICS_MAP: Dict[Phase, List[MetricDefinition]] = {
    Phase.PRODUCTION: _PRODUCTION_METRICS,
    Phase.BUILD: _BUILD_METRICS,
    Phase.CODE: _CODE_METRICS,
    Phase.TEST: _TEST_METRICS,
    Phase.PERFORMANCE_TEST: _PERFORMANCE_TEST_METRICS,
    Phase.CHAOS: _CHAOS_METRICS,
    Phase.REQUIREMENTS: _REQUIREMENTS_METRICS,
    Phase.UAT: _UAT_METRICS,
}


class MetricRegistry:
    """Central registry of all SDLC metrics in the PRESTO framework.

    Provides lookup by phase, by name, and identifies the target metric
    (System Uptime) used as the prediction variable. All metric definitions
    are immutable and registered at import time.

    Usage:
        registry = MetricRegistry()
        prod_metrics = registry.get_phase_metrics(Phase.PRODUCTION)
        target = registry.get_target_metric()
        all_metrics = registry.get_all_metrics()
    """

    def __init__(self) -> None:
        self._phase_map: Dict[Phase, List[MetricDefinition]] = _PHASE_METRICS_MAP
        self._name_index: Dict[str, MetricDefinition] = {}
        self._build_name_index()

    def _build_name_index(self) -> None:
        """Build a flat name-to-metric index for fast lookups.

        When the same column name appears in multiple phases (e.g.,
        "Unit Test Coverage (%)" in CODE and TEST), we keep only the
        first occurrence by phase enum order. Phase-specific lookups
        should use get_phase_metrics() + filter instead.
        """
        for phase in Phase:
            for metric in self._phase_map.get(phase, []):
                if metric.name not in self._name_index:
                    self._name_index[metric.name] = metric

    # -- Public API --------------------------------------------------------

    def get_phase_metrics(self, phase: Phase) -> List[MetricDefinition]:
        """Return all metric definitions for the given SDLC phase.

        Args:
            phase: The Phase enum member to query.

        Returns:
            List of MetricDefinition objects for the phase.

        Raises:
            KeyError: If the phase is not registered.
        """
        if phase not in self._phase_map:
            raise KeyError(f"Unknown phase: {phase}")
        return list(self._phase_map[phase])

    def get_all_metrics(self) -> List[MetricDefinition]:
        """Return every registered metric across all phases.

        The order follows Phase enum declaration order, with metrics
        within each phase in their registration order.

        Returns:
            Flat list of all MetricDefinition objects.
        """
        result: List[MetricDefinition] = []
        for phase in Phase:
            result.extend(self._phase_map.get(phase, []))
        return result

    def get_metric(self, name: str) -> MetricDefinition:
        """Look up a single metric by its exact column name.

        When a column name appears in multiple phases, the metric from
        the earliest phase (by Phase enum order) is returned. Use
        get_phase_metric() for phase-specific lookups.

        Args:
            name: Exact CSV column header string.

        Returns:
            The matching MetricDefinition.

        Raises:
            KeyError: If no metric with the given name is registered.
        """
        if name not in self._name_index:
            raise KeyError(
                f"Metric not found: '{name}'. "
                f"Available metrics: {sorted(self._name_index.keys())}"
            )
        return self._name_index[name]

    def get_phase_metric(
        self, name: str, phase: Phase
    ) -> MetricDefinition:
        """Look up a metric by name within a specific phase.

        Useful when the same column name exists in multiple phases
        with different distribution parameters.

        Args:
            name: Exact CSV column header string.
            phase: The Phase to search within.

        Returns:
            The matching MetricDefinition.

        Raises:
            KeyError: If the metric is not found in the given phase.
        """
        for metric in self._phase_map.get(phase, []):
            if metric.name == name:
                return metric
        raise KeyError(f"Metric '{name}' not found in phase {phase.value}")

    def get_target_metric(self) -> MetricDefinition:
        """Return the PRESTO target variable: System Uptime (%).

        This is the metric that the PRESTO ML models predict.

        Returns:
            MetricDefinition for System Uptime (%).
        """
        return self.get_phase_metric(TARGET_METRIC_NAME, Phase.PRODUCTION)

    def get_high_importance_metrics(self) -> List[MetricDefinition]:
        """Return all metrics marked as high importance for correlation
        with the target variable (System Uptime).

        Returns:
            List of MetricDefinition objects with high_importance=True.
        """
        return [m for m in self.get_all_metrics() if m.high_importance]

    def get_phase_column_names(self, phase: Phase) -> List[str]:
        """Return the ordered list of CSV column names for a phase.

        Does not include "Date" and "Release Number" (handled separately
        by the data generator).

        Args:
            phase: The Phase enum member to query.

        Returns:
            List of column name strings.
        """
        return [m.name for m in self.get_phase_metrics(phase)]

    def get_phases(self) -> List[Phase]:
        """Return all registered phases in declaration order.

        Returns:
            List of Phase enum members.
        """
        return list(Phase)

    @property
    def total_metric_count(self) -> int:
        """Total number of metric definitions across all phases."""
        return sum(len(metrics) for metrics in self._phase_map.values())

    def summary(self) -> str:
        """Return a human-readable summary of the registry contents.

        Returns:
            Multi-line string with phase counts and total.
        """
        lines = ["PRESTO Metric Registry Summary", "=" * 40]
        for phase in Phase:
            metrics = self._phase_map.get(phase, [])
            high = sum(1 for m in metrics if m.high_importance)
            lines.append(
                f"  {phase.value:<20s}: {len(metrics):3d} metrics "
                f"({high} high importance)"
            )
        lines.append("-" * 40)
        total_high = len(self.get_high_importance_metrics())
        lines.append(
            f"  {'TOTAL':<20s}: {self.total_metric_count:3d} metrics "
            f"({total_high} high importance)"
        )
        lines.append(f"  Target metric: {TARGET_METRIC_NAME}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Module-level convenience: pre-built registry singleton
# ---------------------------------------------------------------------------
_DEFAULT_REGISTRY: Optional[MetricRegistry] = None


def get_registry() -> MetricRegistry:
    """Return the module-level MetricRegistry singleton.

    Creates the registry on first call, then returns the same instance.

    Returns:
        The shared MetricRegistry instance.
    """
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = MetricRegistry()
    return _DEFAULT_REGISTRY


# ---------------------------------------------------------------------------
# Self-test when run directly
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    registry = get_registry()
    print(registry.summary())
    print()

    target = registry.get_target_metric()
    print(f"Target: {target.name} ({target.phase.value})")
    print(f"  Distribution: {target.distribution_type.value}")
    print(f"  Params: {target.params}")
    print(f"  Bounds: {target.bounds}")
    print()

    print("High-importance metrics:")
    for m in registry.get_high_importance_metrics():
        print(f"  [{m.phase.value}] {m.name}")
