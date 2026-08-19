# ML Pipeline Results: SQuaD Vulnerability Prediction (real data, cross-sectional, per-project)

**Task:** predict `log1p(cve_count)` -- the number of distinct CVE IDs linked to a project's issue tracker -- from real process/churn characteristics aggregated per project. Companion to the defect-fix-rate SQuaD adapter (`output_squad_ml_results.md`); same 408-project aggregation unit, different real outcome variable (security vulnerabilities instead of bug-fix commits).

## Dataset Characteristics

| Property | Value |
|---|---|
| Projects (aggregation unit) | 408 |
| Projects with >=1 linked CVE | 161 (39.5%) |
| Features | 14 |
| Max CVE count (single project) | 222 |
| Mean CVE count | 9.26 |
| Target mean (log1p cve_count) | 0.867 |
| Target std (log1p cve_count) | 1.368 |

## Model Performance

| Model | CV R2 (mean +/- std) | Holdout R2 | Holdout MAE | Holdout RMSE |
|---|---|---|---|---|
| Random Forest | 0.0585 +/- 0.2695 | 0.2453 | 0.958 | 1.332 |
| Gradient Boosting | -0.1937 +/- 0.5446 | 0.2007 | 0.991 | 1.371 |
| Lasso Regression | -0.0370 +/- 0.0422 | -0.0324 | 1.184 | 1.558 |
| Ridge Regression | -0.9641 +/- 1.2152 | -0.8367 | 1.291 | 2.078 |
| Linear Regression | -1.8543 +/- 2.2765 | -0.9490 | 1.317 | 2.140 |

## Feature Importances (Random Forest)

| Rank | Feature | Importance |
|---|---|---|
| 1 | mean_n_fix | 0.1776 |
| 2 | n_releases_observed | 0.1576 |
| 3 | mean_total_LOC | 0.1103 |
| 4 | mean_lines_added | 0.0803 |
| 5 | mean_n_auth | 0.0779 |
| 6 | mean_age | 0.0693 |
| 7 | mean_change_set | 0.0677 |
| 8 | std_churn | 0.0447 |
| 9 | mean_max_change_set | 0.0436 |
| 10 | mean_max_lines_added | 0.0399 |
| 11 | mean_weighted_age | 0.0387 |
| 12 | mean_avg_churn | 0.0364 |
| 13 | mean_max_churn | 0.0293 |
| 14 | mean_churn | 0.0265 |

## Directional Correlation Check

Empirical correlation of each process metric with raw `cve_count`, across the 408 aggregated projects:

| Metric | Correlation with cve_count |
|---|---|
| mean_n_fix | 0.335 |
| mean_age | 0.290 |
| mean_max_churn | 0.173 |
| mean_churn | 0.155 |
| mean_total_LOC | 0.138 |
| mean_lines_added | 0.082 |
| mean_n_auth | 0.067 |
| mean_change_set | 0.015 |

## Notes

- CVE linkage from SQuaD's `cve_data.csv` (5,294 rows, 175 distinct projects, 1,479 distinct CVE IDs, GitHub Dependabot/security-advisory sourced). 247/408 qualifying projects (>=5 releases) have zero linked CVEs; target is heavily right-skewed (max 222, apache#ofbiz-framework), hence log1p transform.
- Interpret with caution: CVE disclosure count reflects a project's exposure surface (popularity, dependency-scanner coverage) at least as much as its own process characteristics, so this is a harder and more confounded prediction target than defect-fix rate. A weak result is a substantive finding about the limits of process-metrics-only vulnerability prediction, not a pipeline failure.
- Same aggregation, split (80/20, in groupby-aggregation row order), scaling (StandardScaler fit on train only), and 5-fold TimeSeriesSplit CV protocol as the companion defect-fix-rate adapter, to keep the two SQuaD results directly comparable.
