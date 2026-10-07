# SQuaD Nested Model Selection (PRESTO v4 revision, Phase 2b)

Replaces the paper's existing fixed-hyperparameter "best of 5, selected by holdout R2" protocol (Section 4.2.4) with nested_cv_harness.py's nested_select() for all three SQuaD variants: defect-fix rate, CVE-count, and the static-analysis-enriched defect-fix rate. A 95% pairs/case bootstrap CI (2000 resamples, seed 20260919) is added for each nested-selected model. All three (~408 projects) use the harness's default grids.

| Variant | Nested Model | Inner CV R2 | Nested Holdout R2 | 95% CI | Sig? | Old-Protocol Model | Old-Protocol Holdout R2 | Published (main_mdpi_v3) |
|---|---|---:|---:|---|:---:|---|---:|---|
| Defect-fix rate | Lasso Regression | 0.1129 | 0.1082 | [-0.0013, 0.2502] | no | Random Forest | 0.4496 | Random Forest (0.4020) |
| CVE-count (log1p) | Random Forest | 0.0938 | 0.2323 | [0.0551, 0.3628] | yes | Random Forest | 0.2323 | Random Forest (0.2450) |
| Enriched defect-fix rate | Random Forest | 0.2370 | 0.4955 | [0.0210, 0.7392] | yes | Ridge Regression | 0.5132 | Random Forest (0.4830) |

## Summary

- 2/3 nested-selected variants have a bootstrap CI excluding zero.
- Nested selection picks a different model than the old holdout-selection protocol in 2/3 variants.
