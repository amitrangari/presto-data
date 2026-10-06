"""
PRESTO v6: redraw Figure 5 (fig_06_leakage_comparison) and Figure 6 (fig_08_feature_importance)
directly from the values reported in the manuscript's tables, so figure and table cannot disagree.

  Figure 5 <- Tables 8 and 9 (model_perf_with / model_perf_without): ABC Cloud Provider,
              fixed-hyperparameter baseline, holdout R^2 with and without AR features.
  Figure 6 <- Table 12 (feature_importance): top-15 Random Forest permutation importances,
              without AR features, with each feature's SDLC phase.

No model is refit here; this is a plotting script only. Style matches generate_figures_v6.py.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import generate_figures_v6 as g  # shared style constants, OUT_DIR, _save

# ---------------------------------------------------------------------------
# Figure 5: Tables 8 and 9 (holdout R^2, fixed-hyperparameter baseline, ABC Cloud)
# ---------------------------------------------------------------------------
def generate_leakage_comparison() -> None:
    models = ["Random\nForest", "Lasso\nRegression", "Gradient\nBoosting", "Ridge\nRegression", "Linear\nRegression"]
    with_ar = [0.195, -0.020, -1.833, -11.286, -13.340]      # Table 8
    without_ar = [0.106, -0.020, -1.495, -5.582, -6.946]     # Table 9
    cap = -2.0
    disp_w = [max(v, cap) for v in with_ar]
    disp_wo = [max(v, cap) for v in without_ar]

    x = np.arange(len(models)); bw = 0.35
    fig, ax = plt.subplots(figsize=(8, 5.2))
    c_with, c_without = "#3274A1", "#E1812C"
    bw_bars = ax.bar(x - bw / 2, disp_w, bw, label="With AR features", color=c_with,
                     edgecolor="white", linewidth=0.5, zorder=3)
    bwo_bars = ax.bar(x + bw / 2, disp_wo, bw, label="Without AR features", color=c_without,
                      edgecolor="white", linewidth=0.5, zorder=3)
    ax.axhline(0, color="#666666", linestyle="--", linewidth=0.8, zorder=2)

    def label(bars, vals, disp, color):
        for bar, v, d in zip(bars, vals, disp):
            cx = bar.get_x() + bar.get_width() / 2
            if v < cap:  # capped: true value written inside the bar
                ax.text(cx, d + 0.08, f"{v:.3f}", ha="center", va="bottom", rotation=90,
                        fontsize=g._ANNOTATION_SIZE - 1, color="white", fontweight="bold")
            elif v >= 0:
                ax.text(cx, v + 0.04, f"{v:.3f}", ha="center", va="bottom",
                        fontsize=g._ANNOTATION_SIZE, color=color, fontweight="bold")
            else:
                ax.text(cx, v - 0.04, f"{v:.3f}", ha="center", va="top",
                        fontsize=g._ANNOTATION_SIZE, color=color, fontweight="bold")
    label(bw_bars, with_ar, disp_w, c_with)
    label(bwo_bars, without_ar, disp_wo, c_without)

    ax.set_ylabel("Holdout R² (ABC Cloud, fixed-hyperparameter baseline)", fontsize=g._LABEL_SIZE)
    ax.set_title("Impact of AR-Feature Removal on Holdout R²\n(corrected AR construction; values from Tables 8 and 9)",
                 fontsize=g._TITLE_SIZE - 1, fontweight="bold", pad=12)
    ax.set_xticks(x); ax.set_xticklabels(models, fontsize=g._TICK_SIZE)
    ax.set_ylim(-2.3, 0.5)
    ax.legend(fontsize=g._ANNOTATION_SIZE + 1, loc="lower left", framealpha=0.9, edgecolor="#cccccc")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.text(0.5, 0.005, "Bars below −2.0 are capped for display; true values are written inside the bar.",
             ha="center", va="bottom", fontsize=g._ANNOTATION_SIZE - 1, fontstyle="italic", color="#555555")
    fig.subplots_adjust(bottom=0.17)
    g._save(fig, "fig_06_leakage_comparison.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 6: Table 12 (top-15 permutation importances, without AR features)
# ---------------------------------------------------------------------------
def generate_feature_importance() -> None:
    rows = [  # (feature, importance %, phase) -- Table 12, ranks 1..15
        ("Test Environment Availability (%)", 20.61, "Test"),
        ("Build Success Rate (%), diff 1", 10.28, "Build"),
        ("Build Success Rate (%), diff 2", 5.91, "Build"),
        ("Customer Satisfaction Score (1-10), pct change 1", 4.00, "Production"),
        ("Requirements Approval Time (Hours)", 3.79, "Requirements"),
        ("Build Environment Consistency (%)", 3.38, "Build"),
        ("Customer Satisfaction Score (1-10), rolling cv 3", 3.35, "Production"),
        ("Build Success Rate (%), pct change 1", 3.06, "Build"),
        ("Build Frequency (Builds/Day)", 2.78, "Build"),
        ("Requirements Change Rate (Changes/Week)", 2.78, "Requirements"),
        ("Requirements Completeness Score (1-10)", 2.72, "Requirements"),
        ("Recovery Time from Failures (Minutes)", 2.46, "Production"),
        ("Requirements Density (Req/Feature)", 2.14, "Requirements"),
        ("Requirements Traceability Coverage (%)", 2.06, "UAT"),
        ("Customer Satisfaction Score (1-10), rolling mean 10", 2.02, "Production"),
    ]
    phase_color = {"Test": "#3274A1", "Build": "#17BECF", "Production": "#C44E52",
                   "Requirements": "#9467BD", "UAT": "#8C8C3A"}
    names = [r[0] for r in rows][::-1]; vals = [r[1] for r in rows][::-1]
    cols = [phase_color[r[2]] for r in rows][::-1]

    fig, ax = plt.subplots(figsize=(8.5, 6.2))
    y = np.arange(len(names))
    ax.barh(y, vals, color=cols, edgecolor="white", linewidth=0.5, zorder=3)
    for yi, v in zip(y, vals):
        ax.text(v + 0.25, yi, f"{v:.2f}%", va="center", fontsize=g._ANNOTATION_SIZE, color="#333333")
    ax.set_yticks(y); ax.set_yticklabels(names, fontsize=g._TICK_SIZE - 1)
    ax.set_xlabel("Permutation importance (% of total, Random Forest, without AR features)", fontsize=g._LABEL_SIZE)
    ax.set_title("Top 15 Feature Importances by SDLC Phase\n(ABC Cloud; values from Table 12)",
                 fontsize=g._TITLE_SIZE - 1, fontweight="bold", pad=12)
    ax.set_xlim(0, 24)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in phase_color.values()]
    ax.legend(handles, list(phase_color.keys()), title="SDLC phase", fontsize=g._ANNOTATION_SIZE,
              title_fontsize=g._ANNOTATION_SIZE + 1, loc="lower right", framealpha=0.9, edgecolor="#cccccc")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    fig.tight_layout()
    g._save(fig, "fig_08_feature_importance.png")
    plt.close(fig)


if __name__ == "__main__":
    g._apply_base_style()
    generate_leakage_comparison()
    generate_feature_importance()
    print("Done: Figures 5 and 6 redrawn from Tables 8/9 and 12.")
