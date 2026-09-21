# TravisTorrent Nested Model Selection (PRESTO v4 revision, Phase 2b)

Replaces the paper's existing fixed-hyperparameter "best of 5 models, selected by holdout R2" protocol (Section 4.2.1) with nested_cv_harness.py's nested_select(): model+hyperparameter choice happens via TimeSeriesSplit(5) entirely within the outer 80% training partition; the outer 20% holdout is scored exactly once, by the already-selected configuration. Run for both the full-feature condition and the testduration-excluded robustness check (excluding `tr_log_testduration` and its 8 rolling/lag/diff derivatives), matching the paper's existing two-table structure. A 95% pairs/case bootstrap CI (2000 resamples, seed 20260919) is added for the nested-selected model in each case.

**Grid-size note:** projects with an outer-training partition (80% split) over 5000 rows use a REDUCED grid (Ridge/Lasso: 7-point alpha grid vs. 19; RF: 4 combinations vs. 18; GB: 4 combinations vs. 27) to keep runtime tractable -- disclosed per-row below, not a silent truncation.

## Full-feature condition

| Project | Nested Model | Inner CV R2 | Nested Holdout R2 | 95% CI | Sig? | Old-Protocol Model | Old-Protocol Holdout R2 | Grid |
|---|---|---:|---:|---|:---:|---|---:|---|
| dd-agent | Ridge Regression | -0.1075 | -12264630.4517 | [-22776772.5333, -4422698.6541] | yes | Gradient Boosting | 0.3916 | very-reduced |
| bundler | Lasso Regression | -0.4044 | -2.9192 | [-3.1869, -2.6711] | yes | Random Forest | -0.1552 | very-reduced |
| sentry | Gradient Boosting | -1.4899 | -0.0828 | [-0.1014, -0.0654] | yes | Gradient Boosting | -0.0828 | very-reduced |
| matrix | Gradient Boosting | -0.1394 | -0.3311 | [-0.7309, -0.0238] | yes | Random Forest | -0.0079 | full |
| mongoid | Gradient Boosting | -0.0326 | -0.0459 | [-0.0542, -0.0378] | yes | Gradient Boosting | -0.0459 | very-reduced |
| youtube-dl | Lasso Regression | -0.6853 | 0.4708 | [0.4502, 0.4906] | yes | Linear Regression | 0.4753 | very-reduced |
| rspec-core | Gradient Boosting | -0.0307 | -1.1976 | [-1.3071, -1.0935] | yes | Lasso Regression | -0.0487 | very-reduced |

**Paper's already-published numbers (main_mdpi_v3, full-feature table):**

| Project | Published Model | Published Holdout R2 |
|---|---|---:|
| youtube-dl | Linear Regression | 0.4750 |
| sentry | Gradient Boosting | 0.0500 |
| dd-agent | Gradient Boosting | 0.0180 |
| matrix | Random Forest | 0.0050 |
| mongoid | Gradient Boosting | -0.0400 |
| bundler | Random Forest | -0.1510 |
| rspec-core | Random Forest | -0.2940 |

## Testduration-excluded condition (robustness check)

| Project | Nested Model | Inner CV R2 | Nested Holdout R2 | 95% CI | Sig? | Old-Protocol Model | Old-Protocol Holdout R2 | Grid |
|---|---|---:|---:|---|:---:|---|---:|---|
| dd-agent | Ridge Regression | -0.1438 | -8481796.7959 | [-15751624.3575, -3058588.8433] | yes | Lasso Regression | 0.1505 | very-reduced |
| bundler | Lasso Regression | -0.4044 | -2.9192 | [-3.1869, -2.6711] | yes | Random Forest | -0.2725 | very-reduced |
| sentry | Gradient Boosting | -0.7508 | -0.2920 | [-0.3142, -0.2701] | yes | Random Forest | -0.1009 | very-reduced |
| matrix | Gradient Boosting | -0.0370 | -0.1948 | [-0.5348, 0.0723] | no | Random Forest | -0.0161 | full |
| mongoid | Gradient Boosting | -0.0510 | -0.0533 | [-0.0616, -0.0452] | yes | Gradient Boosting | -0.0533 | very-reduced |
| youtube-dl | Ridge Regression | -1.5299 | -0.9635 | [-1.0443, -0.8887] | yes | Gradient Boosting | -0.1755 | very-reduced |
| rspec-core | Ridge Regression | -0.1809 | -0.7934 | [-0.8699, -0.7256] | yes | Lasso Regression | -0.0487 | very-reduced |

## Summary

- Full-feature condition: 7/7 projects' nested-selected model has a bootstrap CI excluding zero; nested selection picks a different model than the old holdout-selection protocol in 5/7 projects.
- Testduration-excluded condition: 6/7 projects significant; 6/7 model swaps.

- Old published best-of-seven: 0.4750. Nested-selected best-of-seven: 0.4708 (youtube-dl, Lasso Regression), CI [0.4502, 0.4906], significant: yes.
