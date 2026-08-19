# Synthetic data projects — regenerated 2026-08-09 (current, matches paper's copula generator)

Three synthetic SDLC datasets produced by the current Gaussian-copula generator
(`code/synthetic_data_generator/`), using the seeds published in the manuscript (42 / ABC Cloud
Provider, 123 / XYZ Sales Force, 456 / Card Payment Processor) and the profiles in
`code/synthetic_data_generator/config/domain_profiles.yaml`. Each `<domain>/` folder here also
includes `ml_results.md` — the full feature-engineering + 5-model training/evaluation output from
`run_pipeline.py`, both with and without target-derived features.

**This regeneration also carries a bug fix.** `run_pipeline.py::add_rolling_features()` previously
computed rolling-window statistics without shifting the series first, so features like
`System Uptime (%)_rolling_mean_3` included the current row — literal same-row leakage for 20 of
the paper's 32 "target-derived" features (the other 12, lag-based, were already correctly shifted).
This is now fixed (rolling stats are computed on the series shifted by 1 period). See
`code/synthetic_data_generator/R2_LAG_SHIFT_FIX_EVIDENCE.md` for the full bug description and a
controlled before/after comparison across all three domains. Headline finding: the fix barely moves
Random Forest's holdout R² (the paper's headline model) but substantially changes Linear/Ridge/
Gradient Boosting in some domains — evidence the original R²=0.946 was not primarily an artifact of
the bug, but that other models' "with-leakage" numbers were.

## Contents

Each `<domain>/` folder has per-SDLC-phase CSVs (`requirements_metrics.csv`, `code_metrics.csv`,
`build_metrics.csv`, `test_metrics.csv`, `uat_metrics.csv`, `performance_testing_metrics.csv`,
`chaos_testing_metrics.csv`, `production_run_metrics.csv`), `release-data.csv`,
`generation_metadata.json`, `validation_report.{md,json}` (copula correlation/bounds validation),
and `ml_results.md` (pipeline results).

## Prior stale data

The previous restored-from-git-history copies (pre-copula-rewrite, produced the circular R²=0.992
result from the desk-rejected IEEE draft) are archived at `archive-stale-pre-copula-rewrite/` for
provenance. Do not use them for anything paper-related.

## Use for the "top 3 real vs. 3 synthetic" comparison

See `../top3_real_vs_synthetic.md` for how these three domains line up against the top 3 real-data
candidates identified in `sdlc_metrics_data_catalog.md` (Mozilla Perfherder, SQuaD, GHALogs —
download in progress, see `../real-data/`).
