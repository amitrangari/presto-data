#!/usr/bin/env python3
"""New figure for M3: nested-CV alpha tuning vs. the paper's untuned alpha=1.0
baseline, per domain, without-AR condition, with Random Forest (fixed
hyperparameters) shown as a reference line.

Data below is copied verbatim from M3_NESTED_CV_TUNING_EVIDENCE.md (rerun
m3_nested_cv_tuning.py to regenerate that report if the underlying data changes).

Usage: python regenerate_fig15_m3_tuning.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

import generate_figures as gf  # noqa: E402

# domain -> {ridge_untuned, ridge_tuned, lasso_untuned, lasso_tuned, rf_fixed}
DATA = {
    "ABC Cloud\n(primary)": dict(ridge_untuned=-7.285, ridge_tuned=0.067,
                                  lasso_untuned=0.129, lasso_tuned=0.129, rf_fixed=0.268),
    "Card Payment\nProcessor": dict(ridge_untuned=-0.215, ridge_tuned=0.766,
                                     lasso_untuned=0.362, lasso_tuned=0.362, rf_fixed=0.339),
    "XYZ Sales\nForce": dict(ridge_untuned=-4.104, ridge_tuned=0.153,
                              lasso_untuned=0.012, lasso_tuned=0.418, rf_fixed=0.255),
}


def generate() -> None:
    print("Generating fig_15_m3_nested_cv_tuning.png ...")
    domains = list(DATA.keys())
    x = np.arange(len(domains))
    width = 0.18

    fig, ax = plt.subplots(figsize=(9.5, 5.8))

    ridge_tuned = [DATA[d]["ridge_tuned"] for d in domains]
    lasso_tuned = [DATA[d]["lasso_tuned"] for d in domains]
    rf_fixed = [DATA[d]["rf_fixed"] for d in domains]

    # Clip untuned bars for display (they go to -7.3); show a break annotation.
    ridge_untuned_display = [max(v, -1.0) for v in (DATA[d]["ridge_untuned"] for d in domains)]
    ridge_untuned_actual = [DATA[d]["ridge_untuned"] for d in domains]

    b1 = ax.bar(x - 1.5 * width, ridge_untuned_display, width, label="Ridge (untuned, α=1.0)",
                color="#c44e52", edgecolor="white", linewidth=0.5, zorder=3)
    b2 = ax.bar(x - 0.5 * width, ridge_tuned, width, label="Ridge (nested-CV tuned)",
                color="#3274A1", edgecolor="white", linewidth=0.5, zorder=3)
    b3 = ax.bar(x + 0.5 * width, lasso_tuned, width, label="Lasso (tuned; ≈untuned in 2/3 domains)",
                color="#E1812C", edgecolor="white", linewidth=0.5, zorder=3)
    b4 = ax.bar(x + 1.5 * width, rf_fixed, width, label="Random Forest (fixed, unchanged)",
                color="#3A923A", edgecolor="white", linewidth=0.5, zorder=3)

    ax.axhline(y=0, color="#333333", linestyle="-", linewidth=0.8, zorder=2)

    for bar, val, actual in zip(b1, ridge_untuned_display, ridge_untuned_actual):
        label = f"{actual:.2f}" if actual != val else f"{val:.3f}"
        ax.text(bar.get_x() + bar.get_width() / 2, -1.05, label, ha="center", va="top",
                fontsize=gf._ANNOTATION_SIZE - 1, fontweight="bold", color="#c44e52", rotation=90)

    for bars in (b2, b3, b4):
        for bar in bars:
            val = bar.get_height()
            va = "bottom" if val >= 0 else "top"
            offset = 0.02 if val >= 0 else -0.02
            ax.text(bar.get_x() + bar.get_width() / 2, val + offset, f"{val:.3f}",
                    ha="center", va=va, fontsize=gf._ANNOTATION_SIZE - 1,
                    fontweight="bold", color="#333333")

    ax.set_ylabel("Holdout R² (without AR features)", fontsize=gf._LABEL_SIZE)
    ax.set_title("Nested-CV Alpha Tuning vs. Untuned Baseline, by Domain",
                 fontsize=gf._TITLE_SIZE, fontweight="bold", pad=12)
    ax.set_ylim(-1.15, 0.90)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(0.2))
    ax.set_xticks(x)
    ax.set_xticklabels(domains, fontsize=gf._TICK_SIZE)

    ax.legend(fontsize=gf._ANNOTATION_SIZE, loc="upper left", framealpha=0.9,
              edgecolor="#cccccc", ncol=1)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    gf._save_figure(fig, "fig_15_m3_nested_cv_tuning.png")
    plt.close(fig)


def main() -> None:
    gf._apply_base_style()
    generate()
    print("\nDone.")


if __name__ == "__main__":
    main()
