# ML Pipeline Results: GHALogs (real data, cross-sectional)

**Task:** predict mean CI run duration (seconds) from real repository process/popularity characteristics -- no target-derived features possible (cross-sectional, not time series; see README_VALIDATION.md for why).

## Dataset Characteristics

| Property | Value |
|---|---|
| Repositories | 28443 |
| Features | 23 |
| Target mean (sec) | 1326.9 |
| Target std (sec) | 5108.1 |
| Target median (sec) | 310.5 |

## Model Performance

| Model | CV R2 (mean +/- std) | Holdout R2 | Holdout MAE | Holdout RMSE |
|---|---|---|---|---|
| Gradient Boosting | 0.0353 +/- 0.1953 | 0.1130 | 1280.78 | 6832.85 |
| Lasso Regression | -0.1557 +/- 0.4622 | 0.0999 | 1385.73 | 6882.91 |
| Ridge Regression | -0.1641 +/- 0.4580 | 0.0998 | 1386.07 | 6883.14 |
| Linear Regression | -0.1652 +/- 0.4578 | 0.0998 | 1386.08 | 6883.14 |
| Random Forest | 0.2609 +/- 0.0578 | 0.0964 | 1292.26 | 6896.16 |

## Top 15 Feature Importances (Random Forest)

| Rank | Feature | Importance |
|---|---|---|
| 1 | mean_n_steps | 0.4864 |
| 2 | success_rate | 0.0641 |
| 3 | blankLines | 0.0524 |
| 4 | commentLines | 0.0497 |
| 5 | size | 0.0450 |
| 6 | codeLines | 0.0366 |
| 7 | repo_age_days | 0.0282 |
| 8 | totalPullRequests | 0.0259 |
| 9 | stargazers | 0.0226 |
| 10 | watchers | 0.0211 |
| 11 | totalIssues | 0.0204 |
| 12 | releases | 0.0171 |
| 13 | comment_density | 0.0166 |
| 14 | forks | 0.0166 |
| 15 | contributors | 0.0166 |

## Notes

- Real GHALogs data (CC-BY-SA-4.0), 117,295 repo+workflow combinations, capped at 5 runs each -- too short for within-entity AR features.
- Cross-sectional design: chronological (pushedAt-sorted) 80/20 split, TimeSeriesSplit CV, StandardScaler fit on train only.
- Zero target-derived features possible -- this is a clean test of the process-metrics-predict-performance claim with no leakage risk at all.
