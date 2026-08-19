# SQuaD Defect-Fix Rate, Enriched with Real Static-Analysis Features

Extends the paper's SQuaD defect-fix-rate validation (Section 4.2.4) with real code-quality features from SonarQube, PMD, and CK -- aggregated from the 2026-08-14 full SQuaD data extraction's raw per-file/per-issue dumps (up to 678GB each) via DuckDB streaming aggregation, then rolled up to project level (mean across releases) and joined onto the existing process-metrics feature set. Tests whether genuine Code-phase static-analysis signal changes the paper's finding that the existing (process-metrics-only) result, Random Forest R2=0.402, 95% CI [-0.245, 0.748], is not statistically significant.

## Coverage

| Source | Projects covered (of 408) |
|---|---|
| SonarQube | 352 |
| PMD | 345 |
| CK | 311 |

Enriched feature count: 48 (base process-metrics-only: 13)

## Model Performance (80/20 split, same order as base pipeline)

| Model | CV R2 (mean +/- std) | Holdout R2 | MAE | RMSE |
|---|---|---|---|---|
| Random Forest | 0.2281 +/- 0.3518 | 0.4829 | 79.26 | 138.37 |
| Gradient Boosting | -0.4693 +/- 1.5052 | -0.0564 | 89.02 | 197.77 |
| Lasso Regression | -5.6549 +/- 8.1166 | -0.3927 | 111.22 | 227.08 |
| Ridge Regression | -4.1150 +/- 6.0897 | -0.5062 | 116.27 | 236.15 |
| Linear Regression | -45412.4265 +/- 90777.4146 | -0.5545 | 117.87 | 239.91 |

## Bootstrap 95% CI (2000-resample pairs/case bootstrap, seed 20260810)

| Model | Holdout R2 | 95% CI | Excludes zero |
|---|---|---|---|
| Random Forest | 0.4829 | [-0.0369, 0.7384] | False |
| Gradient Boosting | -0.0564 | [-1.2954, 0.6639] | False |
| Lasso Regression | -0.3927 | [-2.4357, 0.6499] | False |
| Ridge Regression | -0.5062 | [-2.8285, 0.6385] | False |
| Linear Regression | -0.5545 | [-2.9334, 0.6289] | False |

## Feature Importances (Random Forest, top 20)

| Rank | Feature | Importance |
|---|---|---|
| 1 | mean_age | 0.2698 |
| 2 | mean_n_auth | 0.1266 |
| 3 | mean_churn | 0.1226 |
| 4 | std_churn | 0.0879 |
| 5 | sq_mean_measures_classes | 0.0463 |
| 6 | mean_weighted_age | 0.0451 |
| 7 | sq_mean_measures_bugs | 0.0230 |
| 8 | pmd_mean_n_priority2 | 0.0218 |
| 9 | pmd_mean_n_violations | 0.0216 |
| 10 | sq_mean_measures_cognitive_complexity | 0.0214 |
| 11 | mean_lines_added | 0.0182 |
| 12 | mean_total_LOC | 0.0182 |
| 13 | mean_max_change_set | 0.0149 |
| 14 | mean_avg_churn | 0.0129 |
| 15 | ck_mean_avg_cbo | 0.0128 |
| 16 | ck_mean_avg_class_loc | 0.0124 |
| 17 | mean_change_set | 0.0122 |
| 18 | pmd_mean_n_priority1 | 0.0115 |
| 19 | sq_mean_measures_code_smells | 0.0095 |
| 20 | n_releases_observed | 0.0088 |

## Comparison to Paper's Existing Result

| | Existing (process-metrics only) | Enriched (+ SonarQube/PMD/CK) |
|---|---|---|
| Best model | Random Forest | Random Forest |
| Holdout R2 | 0.4023 | 0.4829 |
| RF 95% CI | [-0.2453, 0.7478] | [-0.0369, 0.7384] |
| RF excludes zero (significant) | No | False |
