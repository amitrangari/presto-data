#!/usr/bin/env python3
"""Regenerate fig_09 (ablation curve) and fig_10 (phase contribution) from the PA-RFE
reimplementation (pa_rfe.py), replacing the carried-over-from-original-submission figures.

Data below is copied verbatim from PA_RFE_REIMPLEMENTATION_RESULTS.md (ABC Cloud Provider,
the primary domain, matching the existing figure captions' framing) -- rerun pa_rfe.py to
regenerate that report if the underlying data or algorithm changes.

Usage: python regenerate_parfe_figures.py
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

# ABC Cloud Provider ablation curve, from PA_RFE_REIMPLEMENTATION_RESULTS.md
ABLATION_CURVE = [
    (241, 0.3295), (236, 0.5187), (231, 0.6243), (226, 0.6163), (221, 0.6575),
    (216, 0.6339), (211, 0.6423), (206, 0.6948), (201, 0.6910), (196, 0.7251),
    (191, 0.6974), (186, 0.6811), (181, 0.7153), (176, 0.7268), (171, 0.7059),
    (166, 0.7274), (161, 0.6743), (156, 0.7263), (151, 0.7196), (146, 0.5418),
    (141, 0.6910), (136, 0.7449), (131, 0.7881), (126, 0.7603), (121, 0.8052),
    (116, 0.7656), (111, 0.7640), (106, 0.7663), (101, 0.8092), (96, 0.8114),
    (91, 0.8103), (86, 0.7972), (81, 0.8241), (76, 0.8215), (71, 0.8025),
    (66, 0.7942), (61, 0.7844), (56, 0.7918), (51, 0.8025), (46, 0.7836),
    (41, 0.7828), (36, 0.7905), (31, 0.8163), (26, 0.7911), (21, 0.8036),
    (16, 0.5798),
]
OPTIMAL_N_FEATURES = 81
OPTIMAL_VAL_R2 = 0.8241
OPTIMAL_TEST_R2 = -0.279

PHASE_CONTRIBUTION = [
    ("Performance Test", 35.4), ("Requirements", 29.0), ("Test", 19.2),
    ("UAT", 8.9), ("Production", 5.9), ("Chaos", 0.8), ("Build", 0.7), ("Code", 0.2),
]


def generate_ablation_curve() -> None:
    print("Generating fig_09_ablation_curve.png ...")
    n_features = [n for n, _ in ABLATION_CURVE]
    val_r2 = [r for _, r in ABLATION_CURVE]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(n_features, val_r2, color="#3274A1", linewidth=1.6, marker="o",
            markersize=3.5, zorder=3)
    ax.invert_xaxis()

    ax.axvline(x=OPTIMAL_N_FEATURES, color="#c44e52", linestyle="--", linewidth=1.0, zorder=2)
    ax.annotate(
        f"Optimal: {OPTIMAL_N_FEATURES} features\nval $R^2$={OPTIMAL_VAL_R2:.3f}, "
        f"test $R^2$={OPTIMAL_TEST_R2:.3f}",
        xy=(OPTIMAL_N_FEATURES, OPTIMAL_VAL_R2), xytext=(150, 0.42),
        fontsize=gf._ANNOTATION_SIZE,
        arrowprops=dict(arrowstyle="->", color="#666666", lw=0.8),
        color="#c44e52",
    )

    ax.set_xlabel("Number of features remaining", fontsize=gf._LABEL_SIZE)
    ax.set_ylabel("Validation $R^2$", fontsize=gf._LABEL_SIZE)
    ax.set_title("PA-RFE Ablation Curve (ABC Cloud Provider)",
                 fontsize=gf._TITLE_SIZE, fontweight="bold", pad=12)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(0.1))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5", linewidth=0.6, zorder=0)

    fig.tight_layout()
    fig.text(
        0.5, 0.01,
        "Validation $R^2$ selects the optimum; the large val->test gap (0.824 -> -0.279) shows "
        "why test $R^2$, not validation $R^2$, is the reported metric.",
        ha="center", va="bottom", fontsize=gf._ANNOTATION_SIZE, fontstyle="italic",
        color="#555555",
    )
    fig.subplots_adjust(bottom=0.16)
    gf._save_figure(fig, "fig_09_ablation_curve.png")
    plt.close(fig)


def generate_phase_contribution() -> None:
    print("Generating fig_10_phase_contribution.png ...")
    labels = [p for p, _ in PHASE_CONTRIBUTION]
    values = [v for _, v in PHASE_CONTRIBUTION]

    fig, ax = plt.subplots(figsize=(8, 5))
    y_pos = range(len(labels))
    bars = ax.barh(list(y_pos), values, color="#3274A1", edgecolor="white",
                    linewidth=0.5, zorder=3)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(labels, fontsize=gf._TICK_SIZE)
    ax.invert_yaxis()

    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.8, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", fontsize=gf._ANNOTATION_SIZE,
                color="#3274A1", fontweight="bold")

    ax.set_xlabel("% of permutation importance at optimal subset", fontsize=gf._LABEL_SIZE)
    ax.set_title(f"Phase Contribution at PA-RFE's Optimal Subset\n"
                 f"({OPTIMAL_N_FEATURES} features, ABC Cloud Provider)",
                 fontsize=gf._TITLE_SIZE, fontweight="bold", pad=12)
    ax.set_xlim(0, max(values) * 1.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    fig.text(
        0.5, 0.01,
        "8 of 8 real SDLC phases retain representation (the 9th, virtual cross_phase group, "
        "is freely eliminable by design and drops out).",
        ha="center", va="bottom", fontsize=gf._ANNOTATION_SIZE, fontstyle="italic",
        color="#555555",
    )
    fig.subplots_adjust(bottom=0.16, left=0.22)
    gf._save_figure(fig, "fig_10_phase_contribution.png")
    plt.close(fig)


def main() -> None:
    gf._apply_base_style()
    generate_ablation_curve()
    generate_phase_contribution()
    print("Done.")


if __name__ == "__main__":
    main()
