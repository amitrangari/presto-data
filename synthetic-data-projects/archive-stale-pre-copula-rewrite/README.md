# Synthetic data projects — restored 2026-08-08

Three synthetic SDLC datasets, restored from `presto` repo git history (commit `74f0ea3`,
2026-01-21) after being deleted from the working tree and gitignored in commit `2703170`
the same day. Original paths were `code/projects/<name>/`; the generator/analysis code that
produced them lived alongside the data but was left in git history rather than copied here
(only `synthetic-data/*.csv` plus a few documentation files were carried over — notebooks,
`.pkl` models, logs, and `__pycache__` were intentionally excluded as build artifacts, not data).

## IMPORTANT — this is NOT the data behind the MDPI paper's reported results

This restored data was produced by an **earlier, deterministic-target generator**
(`y = f(metrics) + ε`, `f()` hand-specified by domain experts). That is the generator behind
`paper-work/archive/superseded_drafts/main_org.md` and `main_ieee.tex`, which reported the
circular **R² = 0.992** result that got the paper desk-rejected from IEEE Access.

The current manuscript (`paper-work/overleaf/main_mdpi.tex`) uses a **rewritten Gaussian-copula
generator** (`paper-work/code/synthetic_data_generator/`, added 2026-04-04, commit `336a304`)
where the target is copula-correlated rather than a deterministic function of the features — the
specific fix that collapsed the reported R² from 0.992 to 0.387. That generator's actual output
was never committed (gitignored under `code/synthetic_data_generator/output/`) and does not
currently exist on disk anywhere. **To get the dataset that matches the numbers in the current
paper, the pipeline must be re-run**: `paper-work/code/synthetic_data_generator/run_pipeline.py`,
using the seeds already published in the manuscript (42 / ABC Cloud, 123 / XYZ Sales Force,
456 / Card Payment Processor) and the profiles in `config/domain_profiles.yaml`.

Evidence this restored data predates the copula rewrite:

| Domain | `domain_profiles.yaml` spec (current) | Restored `release-data.csv` |
|---|---|---|
| abc-cloud-provider | 170 releases | 170 releases (matches — likely stable across both generator versions) |
| xyz-sales-force | 200 releases | 97 releases (does not match) |
| card-payment-processor | 150 releases | no `release-data.csv` present at all |

## Contents

Each `<project>/synthetic-data/` folder has per-SDLC-phase CSVs: `requirements_metrics.csv`,
`code_metrics.csv`, `build_metrics.csv`, `test_metrics.csv`, `uat_metrics.csv`,
`performance_testing_metrics.csv`, `chaos_testing_metrics.csv`, `production_run_metrics.csv`,
plus `release-data.csv` / `release-history.md` where present.

## Use for the "top 3 real vs. 3 synthetic" comparison

See `../top3_real_vs_synthetic.md` for how these three domains line up against the top 3
real-data candidates identified in `sdlc_metrics_data_catalog.md`.
