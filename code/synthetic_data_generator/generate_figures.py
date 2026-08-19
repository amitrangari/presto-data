#!/usr/bin/env python3
"""Generate publication-quality figures for the PRESTO paper.

Produces three figures from ML pipeline results, formatted for IEEE Access
(two-column layout, 300+ DPI, clean professional style).

Figures generated:
    1. fig_06_leakage_comparison.png   - With vs without target leakage
    2. fig_07_cross_domain.png         - Cross-domain validation results
    3. fig_08_feature_importance.png   - Top 15 RF feature importances

Usage:
    python generate_figures.py

Output locations:
    - Paper images: <repo>/paper/images/
    - Local copy:   output/figures/
"""
from __future__ import annotations

import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_LOCAL_FIGURES_DIR = _SCRIPT_DIR / "output" / "figures"
_PAPER_IMAGES_DIR = Path("/Volumes/4TB/presto/paper-work/overleaf/images")

# ---------------------------------------------------------------------------
# Style constants
# ---------------------------------------------------------------------------
_DPI = 300
_TITLE_SIZE = 13
_LABEL_SIZE = 11
_TICK_SIZE = 10
_ANNOTATION_SIZE = 9
_BG_COLOR = "white"


def _apply_base_style() -> None:
    """Set matplotlib rcParams for a clean, professional look."""
    plt.rcParams.update({
        "figure.facecolor": _BG_COLOR,
        "axes.facecolor": _BG_COLOR,
        "axes.edgecolor": "#333333",
        "axes.linewidth": 0.8,
        "axes.grid": False,
        "xtick.labelsize": _TICK_SIZE,
        "ytick.labelsize": _TICK_SIZE,
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "figure.dpi": _DPI,
        "savefig.dpi": _DPI,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.15,
    })


def _save_figure(fig: plt.Figure, filename: str) -> None:
    """Save figure (PNG and SVG) to both output locations."""
    stem = filename.rsplit(".", 1)[0]
    for directory in (_LOCAL_FIGURES_DIR, _PAPER_IMAGES_DIR):
        directory.mkdir(parents=True, exist_ok=True)
        png_path = directory / f"{stem}.png"
        svg_path = directory / f"{stem}.svg"
        fig.savefig(png_path, dpi=_DPI, bbox_inches="tight", facecolor=_BG_COLOR)
        fig.savefig(svg_path, bbox_inches="tight", facecolor=_BG_COLOR)
        print(f"  Saved: {png_path}")
        print(f"  Saved: {svg_path}")


# ---------------------------------------------------------------------------
# Figure 1: Leakage Comparison
# ---------------------------------------------------------------------------
def generate_leakage_comparison() -> None:
    """Grouped bar chart: model R2 with vs without target-derived features."""
    print("\n[1/3] Generating fig_06_leakage_comparison.png ...")

    models = ["Linear\nRegression", "Ridge\nRegression", "Lasso\nRegression",
              "Random\nForest", "Gradient\nBoosting"]
    r2_with    = [-0.256, -0.194, 0.129, 0.950, 0.865]
    r2_without = [-9.124, -7.285, 0.129, 0.268, 0.251]

    # Actual values for annotation (before capping)
    actual_without = list(r2_without)

    # Cap extreme negatives at -1.0 for display
    cap = -1.0
    r2_without_display = [max(v, cap) for v in r2_without]
    capped_flags = [v < cap for v in actual_without]

    x = np.arange(len(models))
    bar_width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))

    color_with = "#3274A1"
    color_without = "#E1812C"

    bars_with = ax.bar(x - bar_width / 2, r2_with, bar_width,
                       label="With AR Features",
                       color=color_with, edgecolor="white", linewidth=0.5,
                       zorder=3)
    bars_without = ax.bar(x + bar_width / 2, r2_without_display, bar_width,
                          label="Without AR Features",
                          color=color_without, edgecolor="white", linewidth=0.5,
                          zorder=3)

    # Baseline at R2 = 0
    ax.axhline(y=0, color="#666666", linestyle="--", linewidth=0.8, zorder=2)

    # Value labels on bars
    for bar, val in zip(bars_with, r2_with):
        y_pos = bar.get_height() + 0.02
        ax.text(bar.get_x() + bar.get_width() / 2, y_pos,
                f"{val:.3f}", ha="center", va="bottom",
                fontsize=_ANNOTATION_SIZE, color=color_with, fontweight="bold")

    for bar, val, actual, capped in zip(bars_without, r2_without_display,
                                         actual_without, capped_flags):
        if capped:
            # Place label inside the bar for capped values
            y_pos = bar.get_height() - 0.05
            label = f"{actual:.1f}*"
            ax.text(bar.get_x() + bar.get_width() / 2, y_pos,
                    label, ha="center", va="top",
                    fontsize=_ANNOTATION_SIZE, color="white", fontweight="bold")
        else:
            offset = 0.02 if val >= 0 else -0.04
            va = "bottom" if val >= 0 else "top"
            ax.text(bar.get_x() + bar.get_width() / 2, val + offset,
                    f"{val:.3f}", ha="center", va=va,
                    fontsize=_ANNOTATION_SIZE, color=color_without,
                    fontweight="bold")

    ax.set_ylabel("Holdout R\u00b2", fontsize=_LABEL_SIZE)
    ax.set_xlabel("Model", fontsize=_LABEL_SIZE)
    ax.set_title("Impact of Autoregressive (AR) Feature Removal on Model Performance",
                 fontsize=_TITLE_SIZE, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=_TICK_SIZE)
    ax.set_ylim(-1.15, 1.1)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(0.25))

    ax.legend(fontsize=_ANNOTATION_SIZE + 1, loc="upper left",
              framealpha=0.9, edgecolor="#cccccc")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()

    # Footnote for capped values (placed after tight_layout to avoid overlap)
    fig.text(0.5, 0.01,
             "* Values capped at \u22121.0 for display. "
             "Actual: LR = \u22129.12, Ridge = \u22127.29",
             ha="center", va="bottom",
             fontsize=_ANNOTATION_SIZE, fontstyle="italic", color="#555555")

    fig.subplots_adjust(bottom=0.18)
    _save_figure(fig, "fig_06_leakage_comparison.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 2: Cross-Domain Validation
# ---------------------------------------------------------------------------
def generate_cross_domain() -> None:
    """Bar chart: best holdout R2 per domain without target leakage."""
    print("\n[2/3] Generating fig_07_cross_domain.png ...")

    domains = ["ABC Cloud\nProvider", "Card Payment\nProcessor",
               "XYZ Sales\nForce"]
    best_r2 = [0.268, 0.362, 0.255]
    best_models = ["Random Forest", "Lasso", "Random Forest"]
    colors = ["#3274A1", "#E1812C", "#3A923A"]

    avg_r2 = float(np.mean(best_r2))

    fig, ax = plt.subplots(figsize=(7, 5))

    bars = ax.bar(domains, best_r2, width=0.55, color=colors,
                  edgecolor="white", linewidth=0.5, zorder=3)

    # Average line
    ax.axhline(y=avg_r2, color="#888888", linestyle="--", linewidth=1.0,
               zorder=2, label=f"Average R\u00b2 = {avg_r2:.3f}")

    # Value labels on top of bars
    for bar, val in zip(bars, best_r2):
        ax.text(bar.get_x() + bar.get_width() / 2,
                val + 0.008,
                f"{val:.3f}",
                ha="center", va="bottom",
                fontsize=_LABEL_SIZE, fontweight="bold", color="#333333")

    # Best model annotations below bars
    for bar, model in zip(bars, best_models):
        ax.text(bar.get_x() + bar.get_width() / 2,
                -0.02,
                f"Best: {model}",
                ha="center", va="top",
                fontsize=_ANNOTATION_SIZE, fontstyle="italic",
                color="#555555")

    ax.set_ylabel("Best Holdout R\u00b2 (Without AR Features)",
                  fontsize=_LABEL_SIZE)
    ax.set_title("Cross-Domain Validation Results (Without AR Features)",
                 fontsize=_TITLE_SIZE, fontweight="bold", pad=12)
    ax.set_ylim(-0.06, 0.50)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(0.1))

    ax.legend(fontsize=_ANNOTATION_SIZE + 1, loc="upper right",
              framealpha=0.9, edgecolor="#cccccc")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    _save_figure(fig, "fig_07_cross_domain.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 3: Feature Importance
# ---------------------------------------------------------------------------
def generate_feature_importance() -> None:
    """Horizontal bar chart: top 15 RF feature importances by SDLC phase."""
    print("\n[3/3] Generating fig_08_feature_importance.png ...")

    features = [
        ("Test Environment Availability (%)",          0.429, "Test"),
        ("Test Pass Rate (%)",                         0.106, "Test"),
        ("stability_score",                            0.053, "Cross"),
        ("Build Artifact Integrity (%)",               0.050, "Build"),
        ("Cust. Satisfaction, lag 5",                  0.032, "Prod"),
        ("Business Value Score (1-10)",                0.026, "Req"),
        ("Build Success Rate (%)",                     0.023, "Build"),
        ("Build Success Rate, diff 1",                 0.023, "Build"),
        ("Requirements Change Rate",                   0.021, "Req"),
        ("Cust. Satisfaction, rolling std 3",          0.016, "Prod"),
        ("Build Success Rate, diff 3",                 0.016, "Build"),
        ("Requirements Density",                       0.014, "Req"),
        ("Code Review Turnaround Time (Hrs)",          0.013, "Code"),
        ("Commits per Release",                        0.013, "Code"),
        ("Cust. Satisfaction, pct change 1",           0.012, "Prod"),
    ]

    phase_colors = {
        "Test":  "#3274A1",
        "Perf":  "#3A923A",
        "Req":   "#9467BD",
        "UAT":   "#E1812C",
        "Prod":  "#C44E52",
        "Build": "#17BECF",
        "Chaos": "#7F7F7F",
        "Cross": "#BCBD22",
        "Code":  "#8C564B",
    }

    # Reverse so highest importance is at the top
    features_sorted = list(reversed(features))

    names = [f[0] for f in features_sorted]
    importances = [f[1] for f in features_sorted]
    phases = [f[2] for f in features_sorted]
    bar_colors = [phase_colors[p] for p in phases]

    y = np.arange(len(names))

    fig, ax = plt.subplots(figsize=(8, 6))

    bars = ax.barh(y, importances, height=0.65, color=bar_colors,
                   edgecolor="white", linewidth=0.4, zorder=3)

    # Value labels at the end of each bar
    for bar, val in zip(bars, importances):
        ax.text(val + 0.002, bar.get_y() + bar.get_height() / 2,
                f"{val:.3f}", va="center", ha="left",
                fontsize=_ANNOTATION_SIZE, color="#333333")

    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=_TICK_SIZE)
    ax.set_xlabel("Permutation Importance (normalized)", fontsize=_LABEL_SIZE)
    ax.set_title("Top 15 Feature Importances (Without AR Features)",
                 fontsize=_TITLE_SIZE, fontweight="bold", pad=12)
    ax.set_xlim(0, max(importances) * 1.18)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Legend for SDLC phases (ordered by appearance frequency)
    phase_order = ["Test", "Cross", "Build", "Prod", "Req", "Code", "Perf", "UAT", "Chaos"]
    legend_handles = []
    for phase in phase_order:
        if phase in phases:
            patch = matplotlib.patches.Patch(
                facecolor=phase_colors[phase], edgecolor="white",
                label=phase
            )
            legend_handles.append(patch)

    ax.legend(handles=legend_handles, title="SDLC Phase",
              fontsize=_ANNOTATION_SIZE, title_fontsize=_ANNOTATION_SIZE + 1,
              loc="lower right", framealpha=0.9, edgecolor="#cccccc",
              ncol=2)

    fig.tight_layout()
    _save_figure(fig, "fig_08_feature_importance.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 4: Mozilla Perfherder real-data validation
# ---------------------------------------------------------------------------
def generate_perfherder_validation() -> None:
    """Grouped bar chart: with-AR vs without-AR R2 for 3 real Perfherder signatures."""
    print("\n[4/5] Generating fig_13_perfherder_validation.png ...")

    signatures = ["ESPN\nload time", "Instagram\nspeed index", "NYTimes\nspeed index"]
    r2_with = [0.574, 0.913, 0.167]
    r2_without = [-3.191, -0.367, -3.563]
    r2_without_display = [max(v, -4.0) for v in r2_without]

    x = np.arange(len(signatures))
    bar_width = 0.35

    fig, ax = plt.subplots(figsize=(7, 5))
    color_with = "#3274A1"
    color_without = "#E1812C"

    bars_with = ax.bar(x - bar_width / 2, r2_with, bar_width,
                        label="With AR Features", color=color_with,
                        edgecolor="white", linewidth=0.5, zorder=3)
    bars_without = ax.bar(x + bar_width / 2, r2_without_display, bar_width,
                           label="Without AR Features (alert-history only)",
                           color=color_without, edgecolor="white", linewidth=0.5, zorder=3)

    ax.axhline(y=0, color="#666666", linestyle="--", linewidth=0.8, zorder=2)

    for bar, val in zip(bars_with, r2_with):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.03, f"{val:.3f}",
                ha="center", va="bottom", fontsize=_ANNOTATION_SIZE,
                color=color_with, fontweight="bold")
    for bar, val, disp in zip(bars_without, r2_without, r2_without_display):
        ax.text(bar.get_x() + bar.get_width() / 2, disp - 0.08, f"{val:.2f}",
                ha="center", va="top", fontsize=_ANNOTATION_SIZE,
                color="white", fontweight="bold")

    ax.set_ylabel("Holdout R² (Ridge Regression)", fontsize=_LABEL_SIZE)
    ax.set_xlabel("Real Mozilla Perfherder Signature", fontsize=_LABEL_SIZE)
    ax.set_title("Real-Data Validation: AR Features vs. Alert-History Only",
                 fontsize=_TITLE_SIZE, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(signatures, fontsize=_TICK_SIZE)
    ax.set_ylim(-4.3, 1.2)
    ax.legend(fontsize=_ANNOTATION_SIZE + 1, loc="lower left", framealpha=0.9, edgecolor="#cccccc")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    _save_figure(fig, "fig_13_perfherder_validation.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 5: GHALogs cross-sectional validation
# ---------------------------------------------------------------------------
def generate_ghalogs_validation() -> None:
    """Bar chart: holdout R2 per model, GHALogs cross-sectional CI-duration prediction."""
    print("\n[5/5] Generating fig_14_ghalogs_validation.png ...")

    models = ["Gradient\nBoosting", "Lasso\nRegression", "Ridge\nRegression",
              "Linear\nRegression", "Random\nForest"]
    r2 = [0.113, 0.100, 0.100, 0.100, 0.096]
    colors = ["#3274A1"] * len(models)
    colors[0] = "#3A923A"  # highlight best

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(models, r2, width=0.55, color=colors, edgecolor="white",
                   linewidth=0.5, zorder=3)
    for bar, val in zip(bars, r2):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.003, f"{val:.3f}",
                ha="center", va="bottom", fontsize=_LABEL_SIZE, fontweight="bold",
                color="#333333")

    ax.set_ylabel("Holdout R² (CI Run Duration)", fontsize=_LABEL_SIZE)
    ax.set_title("GHALogs: Real Process Metrics → CI Duration\n(28,443 repositories, zero leakage risk)",
                 fontsize=_TITLE_SIZE, fontweight="bold", pad=12)
    ax.set_ylim(0, 0.16)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    _save_figure(fig, "fig_14_ghalogs_validation.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    """Generate all PRESTO paper figures."""
    _apply_base_style()

    print("PRESTO Figure Generator")
    print("=" * 50)
    print(f"Output (local):  {_LOCAL_FIGURES_DIR}")
    print(f"Output (paper):  {_PAPER_IMAGES_DIR}")

    generate_leakage_comparison()
    generate_cross_domain()
    generate_feature_importance()
    generate_perfherder_validation()
    generate_ghalogs_validation()

    print("\nDone. All 5 figures generated.")


if __name__ == "__main__":
    main()
