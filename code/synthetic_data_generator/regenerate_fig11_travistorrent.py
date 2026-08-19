#!/usr/bin/env python3
"""Regenerate fig_11_real_world_performance from the R7-reimplemented TravisTorrent
adapter (run_pipeline_travistorrent.py), replacing the stale figure from the original
submission (dated 2026-08-08, before the reimplementation).

Data below is copied verbatim from
real-data/travistorrent/output_travistorrent_ml_results.md (rerun that adapter to
regenerate this report if the underlying data or pipeline changes).

Usage: python regenerate_fig11_travistorrent.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

import generate_figures as gf  # noqa: E402

# Best-model holdout R^2 per project, from output_travistorrent_ml_results.md, sorted descending.
PROJECTS = [
    ("youtube-dl", 0.475, "Linear Reg."),
    ("sentry", 0.050, "Grad. Boost"),
    ("dd-agent", 0.018, "Grad. Boost"),
    ("matrix", 0.005, "Rand. Forest"),
    ("mongoid", -0.040, "Grad. Boost"),
    ("bundler", -0.151, "Rand. Forest"),
    ("rspec-core", -0.294, "Rand. Forest"),
]
SYNTHETIC_BASELINE_R2 = 0.268  # ABC Cloud Provider, Section 4.2


def generate_real_world_performance() -> None:
    print("Generating fig_11_real_world_performance.png ...")
    names = [p for p, _, _ in PROJECTS]
    r2 = [r for _, r, _ in PROJECTS]
    models = [m for _, _, m in PROJECTS]
    colors = ["#3A923A" if v >= 0 else "#c44e52" for v in r2]

    fig, ax = plt.subplots(figsize=(10.5, 5.5))

    bars = ax.bar(names, r2, width=0.6, color=colors, edgecolor="white",
                   linewidth=0.5, zorder=3)

    ax.axhline(y=SYNTHETIC_BASELINE_R2, color="#888888", linestyle="--",
               linewidth=1.0, zorder=2,
               label=f"Synthetic baseline (ABC Cloud, R² = {SYNTHETIC_BASELINE_R2:.3f})")
    ax.axhline(y=0, color="#333333", linestyle="-", linewidth=0.8, zorder=2)

    for bar, val in zip(bars, r2):
        va = "bottom" if val >= 0 else "top"
        offset = 0.012 if val >= 0 else -0.012
        ax.text(bar.get_x() + bar.get_width() / 2, val + offset, f"{val:.3f}",
                ha="center", va=va, fontsize=gf._LABEL_SIZE, fontweight="bold",
                color="#333333")

    for bar, model in zip(bars, models):
        ax.text(bar.get_x() + bar.get_width() / 2, -0.36, model,
                ha="center", va="top", fontsize=gf._ANNOTATION_SIZE - 1.5,
                fontstyle="italic", color="#555555", rotation=0)

    ax.set_ylabel("Best-Model Holdout R²", fontsize=gf._LABEL_SIZE)
    ax.set_title("Real-World Build Duration Prediction (TravisTorrent, 7 Projects)",
                 fontsize=gf._TITLE_SIZE, fontweight="bold", pad=12)
    ax.set_ylim(-0.42, 0.62)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(0.1))

    ax.legend(fontsize=gf._ANNOTATION_SIZE + 1, loc="upper right",
              framealpha=0.9, edgecolor="#cccccc")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    gf._save_figure(fig, "fig_11_real_world_performance.png")
    plt.close(fig)


def main() -> None:
    gf._apply_base_style()
    generate_real_world_performance()
    print("\nDone.")


if __name__ == "__main__":
    main()
