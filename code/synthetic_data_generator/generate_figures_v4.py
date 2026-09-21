#!/usr/bin/env python3
"""Regenerate PRESTO v4 figures with corrected (nested-CV / AR-leakage-fixed / GHALogs-
ablated) numbers. Reuses generate_figures.py's styling conventions; all data below is
sourced directly from this revision's evidence files, not from the stale arrays in that
script.

Output: /Volumes/4TB/papers/presto/paper-work/overleaf/presto-mdpi-09-18-2026/images/
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np

OUT_DIR = Path("/Volumes/4TB/papers/presto/paper-work/overleaf/presto-mdpi-09-18-2026/images")
OUT_DIR.mkdir(parents=True, exist_ok=True)

_DPI = 500
_TITLE_SIZE = 13
_LABEL_SIZE = 11
_TICK_SIZE = 10
_ANNOTATION_SIZE = 9
_BG_COLOR = "white"


def _apply_base_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": _BG_COLOR, "axes.facecolor": _BG_COLOR,
        "axes.edgecolor": "#333333", "axes.linewidth": 0.8, "axes.grid": False,
        "xtick.labelsize": _TICK_SIZE, "ytick.labelsize": _TICK_SIZE,
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "figure.dpi": _DPI, "savefig.dpi": _DPI,
        "savefig.bbox": "tight", "savefig.pad_inches": 0.15,
    })


def _save(fig, filename: str) -> None:
    stem = filename.rsplit(".", 1)[0]
    png_path = OUT_DIR / f"{stem}.png"
    svg_path = OUT_DIR / f"{stem}.svg"
    fig.savefig(png_path, dpi=_DPI, bbox_inches="tight", facecolor=_BG_COLOR)
    fig.savefig(svg_path, bbox_inches="tight", facecolor=_BG_COLOR)
    print(f"  Saved: {png_path}")
    print(f"  Saved: {svg_path}")


# ---------------------------------------------------------------------------
# 1. Cross-domain validation, nested-CV-selected (NESTED_MODEL_SELECTION_EVIDENCE.md)
# ---------------------------------------------------------------------------
def generate_cross_domain_nested() -> None:
    print("\n[1/4] Generating fig_07_cross_domain_nested.png ...")
    domains = ["ABC Cloud\nProvider", "Card Payment\nProcessor", "XYZ Sales\nForce"]
    without_ar = [0.108, 0.608, 0.620]
    without_ar_model = ["Ridge", "Ridge", "Lasso"]
    with_ar = [0.111, 0.638, 0.620]
    with_ar_model = ["Ridge", "Ridge", "Lasso"]

    x = np.arange(len(domains))
    bw = 0.35
    fig, ax = plt.subplots(figsize=(8, 5.2))
    c_without, c_with = "#E1812C", "#3274A1"

    bars_wo = ax.bar(x - bw / 2, without_ar, bw, label="Without AR Features",
                      color=c_without, edgecolor="white", linewidth=0.5, zorder=3)
    bars_w = ax.bar(x + bw / 2, with_ar, bw, label="With AR Features",
                     color=c_with, edgecolor="white", linewidth=0.5, zorder=3)

    ax.axhline(y=0, color="#666666", linestyle="--", linewidth=0.8, zorder=2)

    for bar, val, model in zip(bars_wo, without_ar, without_ar_model):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.015, f"{val:.3f}\n({model})",
                ha="center", va="bottom", fontsize=_ANNOTATION_SIZE, color=c_without,
                fontweight="bold")
    for bar, val, model in zip(bars_w, with_ar, with_ar_model):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.015, f"{val:.3f}\n({model})",
                ha="center", va="bottom", fontsize=_ANNOTATION_SIZE, color=c_with,
                fontweight="bold")

    ax.set_ylabel("Nested-CV-Selected Holdout R²", fontsize=_LABEL_SIZE)
    ax.set_title("Cross-Domain Validation: Nested Model Selection\n"
                  "(replaces fixed-holdout-selection protocol; algorithm selected via inner CV, never by holdout score)",
                  fontsize=_TITLE_SIZE - 1, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(domains, fontsize=_TICK_SIZE)
    ax.set_ylim(0, 0.80)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(0.1))
    ax.legend(fontsize=_ANNOTATION_SIZE + 1, loc="upper left", framealpha=0.9, edgecolor="#cccccc")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    _save(fig, "fig_07_cross_domain_nested.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 2. TravisTorrent nested selection, full-feature condition
#    (TRAVISTORRENT_NESTED_SELECTION_EVIDENCE.md)
# ---------------------------------------------------------------------------
def generate_travistorrent_nested() -> None:
    print("\n[2/4] Generating fig_11_real_world_performance.png ...")
    projects = ["youtube-dl", "sentry", "matrix", "mongoid", "rspec-core", "bundler", "dd-agent"]
    nested_r2 = [0.4708, -0.0828, -0.3311, -0.0459, -1.1976, -2.9192, -12264630.4517]
    old_r2 = [0.4750, 0.0500, 0.0050, -0.0400, -0.2940, -0.1510, 0.0180]
    sig = [True, True, True, True, True, True, True]  # all 7 CIs exclude zero per evidence file

    # dd-agent's nested R2 is off the chart by seven orders of magnitude; cap for display,
    # annotate the true value, same convention as fig_06's capped-bar treatment.
    cap = -2.0
    nested_display = [max(v, cap) for v in nested_r2]
    capped = [v < cap for v in nested_r2]

    x = np.arange(len(projects))
    bw = 0.35
    fig, ax = plt.subplots(figsize=(9, 5.5))
    c_old, c_new = "#999999", "#3274A1"

    bars_old = ax.bar(x - bw / 2, old_r2, bw, label="Old protocol (published, main_mdpi_v3)",
                       color=c_old, edgecolor="white", linewidth=0.5, zorder=3)
    bars_new = ax.bar(x + bw / 2, nested_display, bw, label="Nested-CV-selected (this revision)",
                       color=c_new, edgecolor="white", linewidth=0.5, zorder=3)

    ax.axhline(y=0, color="#666666", linestyle="--", linewidth=0.8, zorder=2)

    for bar, val in zip(bars_old, old_r2):
        offset = 0.05 if val >= 0 else -0.05
        va = "bottom" if val >= 0 else "top"
        ax.text(bar.get_x() + bar.get_width() / 2, val + offset, f"{val:.3f}",
                ha="center", va=va, fontsize=_ANNOTATION_SIZE - 1, color=c_old, fontweight="bold")
    for bar, val, disp, cap_flag in zip(bars_new, nested_r2, nested_display, capped):
        if cap_flag:
            ax.text(bar.get_x() + bar.get_width() / 2, disp - 0.08,
                    "R² ≈ −12.3M*", ha="center", va="top",
                    fontsize=_ANNOTATION_SIZE - 1, color="white", fontweight="bold", rotation=90)
        else:
            offset = 0.05 if val >= 0 else -0.05
            va = "bottom" if val >= 0 else "top"
            ax.text(bar.get_x() + bar.get_width() / 2, val + offset, f"{val:.3f}",
                    ha="center", va=va, fontsize=_ANNOTATION_SIZE - 1, color=c_new, fontweight="bold")

    ax.set_ylabel("Holdout R² (full-feature condition)", fontsize=_LABEL_SIZE)
    ax.set_title("TravisTorrent: Nested-CV Selection vs. Old Fixed-Holdout-Selection Protocol",
                 fontsize=_TITLE_SIZE, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(projects, fontsize=_TICK_SIZE, rotation=15, ha="right")
    ax.set_ylim(-2.3, 0.65)
    ax.legend(fontsize=_ANNOTATION_SIZE + 1, loc="upper right", framealpha=0.9, edgecolor="#cccccc")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.text(0.5, 0.01,
             "* dd-agent's nested selection picks Ridge Regression via a misleadingly favorable "
             "inner-CV score; actual holdout R² = −12,264,630 (severe multicollinearity "
             "instability), reported as a genuine limitation of nested selection itself, not omitted.",
             ha="center", va="bottom", fontsize=_ANNOTATION_SIZE - 1, fontstyle="italic", color="#555555")
    fig.subplots_adjust(bottom=0.22)
    _save(fig, "fig_11_real_world_performance.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 3. Perfherder nested selection, main signatures (PERFHERDER_NESTED_SELECTION_EVIDENCE.md)
# ---------------------------------------------------------------------------
def generate_perfherder_nested() -> None:
    print("\n[3/4] Generating fig_13_perfherder_validation.png ...")
    signatures = ["ESPN\nload time", "Instagram\nspeed index", "NYTimes\nspeed index"]
    r2_with = [0.5773, 0.9164, 0.1650]
    r2_without = [-3.1923, -0.3719, -3.5130]
    r2_without_display = [max(v, -4.0) for v in r2_without]

    x = np.arange(len(signatures))
    bw = 0.35
    fig, ax = plt.subplots(figsize=(7, 5))
    color_with, color_without = "#3274A1", "#E1812C"

    bars_with = ax.bar(x - bw / 2, r2_with, bw, label="With AR Features (nested-selected)",
                        color=color_with, edgecolor="white", linewidth=0.5, zorder=3)
    bars_without = ax.bar(x + bw / 2, r2_without_display, bw,
                           label="Without AR (alert-history only, nested-selected)",
                           color=color_without, edgecolor="white", linewidth=0.5, zorder=3)

    ax.axhline(y=0, color="#666666", linestyle="--", linewidth=0.8, zorder=2)
    for bar, val in zip(bars_with, r2_with):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.03, f"{val:.3f}",
                ha="center", va="bottom", fontsize=_ANNOTATION_SIZE, color=color_with, fontweight="bold")
    for bar, val, disp in zip(bars_without, r2_without, r2_without_display):
        ax.text(bar.get_x() + bar.get_width() / 2, disp - 0.08, f"{val:.2f}",
                ha="center", va="top", fontsize=_ANNOTATION_SIZE, color="white", fontweight="bold")

    ax.set_ylabel("Nested-CV-Selected Holdout R² (Lasso Regression)", fontsize=_LABEL_SIZE)
    ax.set_xlabel("Real Mozilla Perfherder Signature", fontsize=_LABEL_SIZE)
    ax.set_title("Real-Data Validation: AR Features vs. Alert-History Only\n(nested selection; results essentially unchanged from prior revision)",
                 fontsize=_TITLE_SIZE - 1, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(signatures, fontsize=_TICK_SIZE)
    ax.set_ylim(-4.3, 1.2)
    ax.legend(fontsize=_ANNOTATION_SIZE, loc="lower left", framealpha=0.9, edgecolor="#cccccc")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    _save(fig, "fig_13_perfherder_validation.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 4. GHALogs: full-feature vs mean_n_steps-ablated (GHALOGS_ABLATION_EVIDENCE.md)
# ---------------------------------------------------------------------------
def generate_ghalogs_before_after() -> None:
    print("\n[4/4] Generating fig_14_ghalogs_validation.png ...")
    models = ["Gradient\nBoosting", "Lasso\nRegression", "Ridge\nRegression",
              "Linear\nRegression", "Random\nForest"]
    r2_full = [0.113, 0.100, 0.100, 0.100, 0.096]
    sig_full = [True, True, True, True, True]
    r2_ablated = [-0.0685, 0.0069, 0.0068, 0.0068, -0.0440]
    sig_ablated = [False, False, False, False, False]

    x = np.arange(len(models))
    bw = 0.35
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    c_full, c_ablated = "#3A923A", "#C44E52"

    bars_full = ax.bar(x - bw / 2, r2_full, bw, label="Full feature set (incl. mean_n_steps) — all 5 significant",
                        color=c_full, edgecolor="white", linewidth=0.5, zorder=3)
    bars_abl = ax.bar(x + bw / 2, r2_ablated, bw, label="mean_n_steps excluded — none significant",
                       color=c_ablated, edgecolor="white", linewidth=0.5, zorder=3)

    ax.axhline(y=0, color="#666666", linestyle="--", linewidth=0.8, zorder=2)
    for bar, val in zip(bars_full, r2_full):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.004, f"{val:.3f}",
                ha="center", va="bottom", fontsize=_ANNOTATION_SIZE, color=c_full, fontweight="bold")
    for bar, val in zip(bars_abl, r2_ablated):
        offset = 0.004 if val >= 0 else -0.006
        va = "bottom" if val >= 0 else "top"
        ax.text(bar.get_x() + bar.get_width() / 2, val + offset, f"{val:.3f}",
                ha="center", va=va, fontsize=_ANNOTATION_SIZE, color=c_ablated, fontweight="bold")

    ax.set_ylabel("Holdout R² (CI Run Duration)", fontsize=_LABEL_SIZE)
    ax.set_title("GHALogs: Significance Does Not Survive Excluding a Near-Tautological Feature\n(28,443 repositories; mean_n_steps is 48.6% of Random Forest importance in the full-feature model)",
                 fontsize=_TITLE_SIZE - 1, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=_TICK_SIZE)
    ax.set_ylim(-0.10, 0.16)
    ax.legend(fontsize=_ANNOTATION_SIZE, loc="upper right", framealpha=0.9, edgecolor="#cccccc")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    _save(fig, "fig_14_ghalogs_validation.png")
    plt.close(fig)


def main() -> None:
    _apply_base_style()
    print("PRESTO v4 Figure Regeneration")
    print("=" * 50)
    generate_cross_domain_nested()
    generate_travistorrent_nested()
    generate_perfherder_nested()
    generate_ghalogs_before_after()
    print("\nDone. 4 figures regenerated.")


if __name__ == "__main__":
    main()
