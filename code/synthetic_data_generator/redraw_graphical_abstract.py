#!/usr/bin/env python3
"""Redraw the PRESTO graphical abstract (R6 fix).

The original `00-Graphical-Abstract.png` (not code-generated, made in an
external design tool with no source in this repo) was flagged by the
consensus review as depicting tooling never used by the study (XGBoost, SHAP,
MLflow, Optuna, GridSearchCV, Apache Spark, Kafka, Kubernetes, Terraform,
Ansible, ...) and reporting stale/mismatched numbers (R^2=0.387 attributed to
Gradient Boosting as "best"; Testing 30.3% / Build 7.5% / Code 4.1% phase
importance; MAE=0.257, RMSE=0.547 -- none of which match the corrected
pipeline's Table results).

This script regenerates it from the actual, current, corrected pipeline
results only -- five scikit-learn models, no hyperparameter search, no
fictitious deployment stack -- and stores it as ordinary matplotlib-generated
source, unlike the original.

Usage:
    python redraw_graphical_abstract.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrow

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

import generate_figures as gf  # noqa: E402  (reuse style/save helpers)

# ---------------------------------------------------------------------------
# Corrected content (matches paper-work/overleaf/main.md as of 2026-08-10)
# ---------------------------------------------------------------------------
PHASES = [
    "Requirements", "Code", "Build", "Test",
    "Performance Test", "Chaos", "UAT", "Production",
]

MODELS_WITHOUT_AR = [
    ("Ridge", 0.108, True),
    ("Gradient Boosting", 0.215, False),
    ("Random Forest", 0.190, False),
    ("Lasso", -0.020, False),
    ("Linear Regression", -6.946, False),
]

PHASE_IMPORTANCE = [
    ("Build", 32.1),
    ("Test", 21.1),
    ("Production", 19.7),
    ("Requirements", 12.7),
    ("Code", 4.9),
    ("UAT", 3.8),
]

COL_BG = ["#eaf1fb", "#fdeeea", "#fff8e1", "#eafaf0"]
COL_ACCENT = ["#2a5fa8", "#c1502e", "#a67c00", "#1e7a4c"]


def _rounded_panel(ax, x, y, w, h, facecolor, edgecolor):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.006,rounding_size=0.012",
        linewidth=1.2, edgecolor=edgecolor, facecolor=facecolor,
        transform=ax.transAxes, zorder=1,
    )
    ax.add_patch(box)


def generate() -> None:
    fig = plt.figure(figsize=(15.5, 8.2))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    fig.text(
        0.5, 0.965,
        "PRESTO: Predicting Software System Performance from SDLC Metrics",
        ha="center", va="top", fontsize=16, fontweight="bold",
    )
    fig.text(
        0.5, 0.93,
        "164 raw metrics, 8 SDLC phases -> 273 engineered features -> 5 scikit-learn models, "
        "nested cross-validation selection (Section 3.2.5)",
        ha="center", va="top", fontsize=10.5, color="#444444",
    )

    col_w = 0.225
    gap = 0.02
    x0 = 0.02
    y0, h = 0.08, 0.78
    xs = [x0 + i * (col_w + gap) for i in range(4)]

    # ---------------- Panel 1: SDLC Data Sources ----------------
    _rounded_panel(ax, xs[0], y0, col_w, h, COL_BG[0], COL_ACCENT[0])
    fig.text(xs[0] + col_w / 2, y0 + h - 0.035, "SDLC Data Sources\n(8 phases)",
              ha="center", va="top", fontsize=12, fontweight="bold", color=COL_ACCENT[0])
    for i, phase in enumerate(PHASES):
        yy = y0 + h - 0.16 - i * 0.075
        ax.add_patch(FancyBboxPatch(
            (xs[0] + 0.015, yy - 0.025), col_w - 0.03, 0.05,
            boxstyle="round,pad=0.004,rounding_size=0.01",
            linewidth=0.8, edgecolor=COL_ACCENT[0], facecolor="white",
            transform=ax.transAxes, zorder=2,
        ))
        fig.text(xs[0] + col_w / 2, yy, phase, ha="center", va="center", fontsize=9.5)
    fig.text(xs[0] + col_w / 2, y0 + 0.03, "164 raw metrics", ha="center", va="bottom",
              fontsize=10.5, fontweight="bold", color=COL_ACCENT[0])

    # ---------------- Panel 2: Feature Engineering ----------------
    _rounded_panel(ax, xs[1], y0, col_w, h, COL_BG[1], COL_ACCENT[1])
    fig.text(xs[1] + col_w / 2, y0 + h - 0.035, "Feature Engineering",
              ha="center", va="top", fontsize=12, fontweight="bold", color=COL_ACCENT[1])
    fe_items = [
        ("Rolling windows", "shifted 1 period first (no same-row leakage)\nwindows 3, 5, 7, 10"),
        ("Lag features", "steps 1, 2, 3, 5\nlag / diff / pct_change"),
        ("Cross-phase composites", "quality_score, stability_score"),
    ]
    yy = y0 + h - 0.17
    for title, sub in fe_items:
        ax.add_patch(FancyBboxPatch(
            (xs[1] + 0.015, yy - 0.075), col_w - 0.03, 0.135,
            boxstyle="round,pad=0.004,rounding_size=0.01",
            linewidth=0.8, edgecolor=COL_ACCENT[1], facecolor="white",
            transform=ax.transAxes, zorder=2,
        ))
        fig.text(xs[1] + col_w / 2, yy + 0.035, title, ha="center", va="center",
                  fontsize=9.5, fontweight="bold")
        fig.text(xs[1] + col_w / 2, yy - 0.018, sub, ha="center", va="center", fontsize=8)
        yy -= 0.19
    fig.text(xs[1] + col_w / 2, y0 + 0.045, "273 features", ha="center", va="bottom",
              fontsize=10.5, fontweight="bold", color=COL_ACCENT[1])
    fig.text(xs[1] + col_w / 2, y0 + 0.02, "241 SDLC process + 32 autoregressive", ha="center",
              va="bottom", fontsize=8, color="#444444")

    # ---------------- Panel 3: Model Comparison ----------------
    _rounded_panel(ax, xs[2], y0, col_w, h, COL_BG[2], COL_ACCENT[2])
    fig.text(xs[2] + col_w / 2, y0 + h - 0.035, "Model Comparison\n(ABC Cloud, nested-CV selected)",
              ha="center", va="top", fontsize=12, fontweight="bold", color=COL_ACCENT[2])
    bar_left = xs[2] + 0.03
    bar_axis_w = col_w - 0.09
    zero_frac = 1.0 / 11.0  # domain [-10, 1] -> 0 sits near the left
    yy = y0 + h - 0.18
    for name, r2, is_best in MODELS_WITHOUT_AR:
        clamped = max(-10.0, min(1.0, r2))
        frac = (clamped - (-10.0)) / 11.0
        fig.text(xs[2] + col_w / 2, yy + 0.032, name, ha="center", va="bottom",
                  fontsize=9, fontweight="bold" if is_best else "normal")
        ax.plot(
            [bar_left, bar_left + bar_axis_w], [yy - 0.008, yy - 0.008],
            color="#999999", lw=0.6, transform=ax.transAxes, zorder=2,
        )
        bcolor = "#1e7a4c" if r2 >= 0 else "#a83232"
        x_lo = bar_left + bar_axis_w * min(zero_frac, frac)
        x_hi = bar_left + bar_axis_w * max(zero_frac, frac)
        ax.add_patch(plt.Rectangle(
            (x_lo, yy - 0.024), max(x_hi - x_lo, 0.002), 0.026,
            facecolor=bcolor, edgecolor="none", transform=ax.transAxes, zorder=3,
        ))
        label = f"R² = {r2:.3f}" + (" ✓ nested-selected" if is_best else "")
        fig.text(bar_left + bar_axis_w + 0.01, yy - 0.011, label, ha="left", va="center",
                  fontsize=8.5, color=bcolor, fontweight="bold" if is_best else "normal")
        yy -= 0.115
    fig.text(xs[2] + col_w / 2, y0 + 0.06,
              "With AR (history) features: R² ≈ 0.11\n(was 0.914; collapsed once a second,\nprev. undisclosed leakage bug was fixed)",
              ha="center", va="bottom", fontsize=8, color="#444444")
    fig.text(xs[2] + col_w / 2, y0 + 0.02,
              "with-AR no longer beats without-AR --\nboth CIs now include zero",
              ha="center", va="bottom", fontsize=7.5, color="#666666")

    # ---------------- Panel 4: Key Results ----------------
    _rounded_panel(ax, xs[3], y0, col_w, h, COL_BG[3], COL_ACCENT[3])
    fig.text(xs[3] + col_w / 2, y0 + h - 0.035, "Key Results",
              ha="center", va="top", fontsize=12, fontweight="bold", color=COL_ACCENT[3])
    fig.text(xs[3] + col_w / 2, y0 + h - 0.1, "R² = 0.11–0.62", ha="center",
              va="top", fontsize=19, fontweight="bold", color=COL_ACCENT[3])
    fig.text(xs[3] + col_w / 2, y0 + h - 0.14, "SDLC process features alone,\nacross 3 enterprise domains",
              ha="center", va="top", fontsize=8, color="#444444")

    fig.text(xs[3] + 0.02, y0 + h - 0.24, "Top predictive phases:", fontsize=9,
              fontweight="bold")
    yy = y0 + h - 0.28
    max_pct = PHASE_IMPORTANCE[0][1]
    for name, pct in PHASE_IMPORTANCE:
        bw = (col_w - 0.09) * (pct / max_pct)
        ax.add_patch(plt.Rectangle(
            (xs[3] + 0.02, yy - 0.018), bw, 0.024,
            facecolor=COL_ACCENT[3], edgecolor="none", transform=ax.transAxes, zorder=2,
        ))
        fig.text(xs[3] + 0.02 + bw + 0.008, yy - 0.006, f"{name} {pct:.1f}%",
                  ha="left", va="center", fontsize=8)
        yy -= 0.05
    fig.text(xs[3] + col_w / 2, yy - 0.01,
              "Build outweighs Code 6.6:1 -- hypothesis,\nunverified on real SDLC data",
              ha="center", va="top", fontsize=7.3, style="italic", color="#666666")

    fig.text(xs[3] + 0.02, y0 + 0.135, "Potential applications:", fontsize=9,
              fontweight="bold")
    apps = [
        "Release risk scoring",
        "Test-infra investment prioritization",
        "Early warning for deployment decisions",
        "Cross-team process benchmarking",
    ]
    yy = y0 + 0.115
    for a in apps:
        fig.text(xs[3] + 0.03, yy, f"• {a}", ha="left", va="top", fontsize=7.6)
        yy -= 0.026

    fig.text(
        0.5, 0.035,
        "Real-world validation (TravisTorrent, Mozilla Perfherder, GHALogs, SQuaD) reported separately -- "
        "synthetic-domain R² alone reflects the copula generator's hand-specified structure "
        "(confirmed by ablation), not independently discovered signal. Confirmatory evidence limited "
        "to SQuaD (CVE-count, enriched defect-fix) and Perfherder (AR-persistence).",
        ha="center", va="bottom", fontsize=7.3, color="#666666", style="italic",
    )

    gf._save_figure(fig, "00-Graphical-Abstract.png")
    plt.close(fig)


def main() -> None:
    gf._apply_base_style()
    print("Redrawing graphical abstract (R6 fix)...")
    generate()
    print("Done.")


if __name__ == "__main__":
    main()
