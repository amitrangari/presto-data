# Mozilla Perfherder Nested Model Selection (PRESTO v4 revision, Phase 2b)

Replaces the paper's existing fixed-hyperparameter "best of 5, selected by holdout R2" protocol (Section 4.2.2) with nested_cv_harness.py's nested_select() for the 3 main signatures (with-AR / alert-history-only) and the 2 bug-enriched signatures (alert-flag-only / bug-metadata-enriched). A 95% pairs/case bootstrap CI (2000 resamples, seed 20260919) is added for each nested-selected model. All 5 datasets are small enough (thousands of pushes) to use the harness's default (unshrunk) grids.

## Main signatures

| Signature | Condition | Nested Model | Inner CV R2 | Nested Holdout R2 | 95% CI | Sig? | Old-Protocol Model | Old-Protocol Holdout R2 | Published (main_mdpi_v3) |
|---|---|---|---:|---:|---|:---:|---|---:|---:|
| espn-loadtime | with-AR | Lasso Regression | 0.0123 | 0.5773 | [0.5017, 0.6432] | yes | Lasso Regression | 0.5773 | 0.5740 |
| espn-loadtime | without-AR (alert-history only) | Lasso Regression | -4.0884 | -3.1923 | [-3.6509, -2.8192] | yes | Linear Regression | -3.1908 | -3.1910 |
| instagram-speedindex | with-AR | Lasso Regression | 0.0703 | 0.9164 | [0.8912, 0.9364] | yes | Ridge Regression | 0.9221 | 0.9130 |
| instagram-speedindex | without-AR (alert-history only) | Lasso Regression | -0.3018 | -0.3719 | [-0.4448, -0.3103] | yes | Gradient Boosting | -0.3663 | -0.3670 |
| nytimes-speedindex | with-AR | Lasso Regression | 0.2202 | 0.1650 | [0.0906, 0.2297] | yes | Ridge Regression | 0.1666 | 0.1670 |
| nytimes-speedindex | without-AR (alert-history only) | Lasso Regression | -13.9378 | -3.5130 | [-3.9909, -3.1338] | yes | Lasso Regression | -3.5130 | -3.5630 |

## Bug-enriched signatures

| Signature | Condition | Nested Model | Inner CV R2 | Nested Holdout R2 | 95% CI | Sig? | Old-Protocol Model | Old-Protocol Holdout R2 | Published (main_mdpi_v3) |
|---|---|---|---:|---:|---|:---:|---|---:|---:|
| installer-size-osx-cross | alert-flag-only | Random Forest | -54.3962 | -58.2902 | [-60.7001, -56.1848] | yes | Ridge Regression | -56.0390 | -56.0600 |
| installer-size-osx-cross | bug-metadata-enriched | Gradient Boosting | -3.0091 | -4.1101 | [-4.3611, -3.8826] | yes | Ridge Regression | -1.0019 | -2.5600 |
| build-metric-osx-aarch64 | alert-flag-only | Gradient Boosting | -32.9485 | -42.0567 | [-44.3826, -39.9638] | yes | Linear Regression | -41.3056 | -41.3100 |
| build-metric-osx-aarch64 | bug-metadata-enriched | Linear Regression | -6.2349 | -1.5990 | [-1.7961, -1.4136] | yes | Lasso Regression | -1.5675 | -1.5700 |

## Summary

- 10/10 nested-selected cases have a bootstrap CI excluding zero.
- Nested selection picks a different model than the old holdout-selection protocol in 8/10 cases.
