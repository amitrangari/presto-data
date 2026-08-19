# ML Pipeline Results: SQuaD (real data, cross-sectional, per-project)

**Task:** predict mean per-release defect-fix rate (`n_fix`) from real process/churn characteristics aggregated per project. **Not** a 1:1 validation of the copula's 84 hand-specified correlations -- SQuaD has no matching metric names for that (see script docstring); this is an independent real-world process-metrics-predict-outcome test.

## Dataset Characteristics

| Property | Value |
|---|---|
| Projects (aggregation unit) | 408 |
| Features | 13 |
| Target mean (n_fix/release) | 136.76 |
| Target median (n_fix/release) | 59.10 |
| Target std (n_fix/release) | 226.08 |

## Model Performance

| Model | CV R2 (mean +/- std) | Holdout R2 | Holdout MAE | Holdout RMSE |
|---|---|---|---|---|
| Random Forest | -0.0541 +/- 0.8414 | 0.4023 | 81.65 | 148.77 |
| Gradient Boosting | -0.6124 +/- 1.8675 | -0.3253 | 106.84 | 221.52 |
| Lasso Regression | -6.1333 +/- 11.7465 | -0.4087 | 107.55 | 228.38 |
| Ridge Regression | -4.0313 +/- 7.8425 | -0.4421 | 108.49 | 231.08 |
| Linear Regression | -9.3159 +/- 17.2049 | -0.4545 | 109.11 | 232.06 |

## Feature Importances (Random Forest)

| Rank | Feature | Importance |
|---|---|---|
| 1 | mean_age | 0.3079 |
| 2 | mean_churn | 0.2028 |
| 3 | mean_n_auth | 0.1756 |
| 4 | std_churn | 0.0975 |
| 5 | mean_weighted_age | 0.0481 |
| 6 | mean_lines_added | 0.0389 |
| 7 | n_releases_observed | 0.0296 |
| 8 | mean_max_change_set | 0.0249 |
| 9 | mean_total_LOC | 0.0228 |
| 10 | mean_avg_churn | 0.0227 |
| 11 | mean_change_set | 0.0162 |
| 12 | mean_max_lines_added | 0.0067 |
| 13 | mean_max_churn | 0.0062 |

## Directional Correlation Check (not a 1:1 copula validation)

Empirical correlation of each process metric with `mean_n_fix` (defect-fix rate), across the 440 aggregated projects:

| Metric | Correlation with mean_n_fix |
|---|---|
| mean_age | 0.441 |
| mean_n_auth | 0.383 |
| mean_churn | 0.336 |
| mean_lines_added | 0.251 |
| mean_total_LOC | 0.235 |
| mean_change_set | 0.175 |
| mean_max_churn | 0.112 |

## Notes

- Real SQuaD data (CC-BY-4.0), 62,449 releases across 440 open-source projects, aggregated to one row per project (>= 5 releases required) to avoid a single dominant project (apache#servicemix-bundles, 27% of raw rows) skewing a release-level split.
- No SQuaD metric maps 1:1 to any of PRESTO's 164 SDLC metrics or the copula's 84 hand-specified correlation pairs -- this adapter tests the paper's general process-metrics-predict-outcome thesis on independent real data, not the specific copula correlation values themselves.
- 80/20 split (rows in `process_metrics.csv` groupby-aggregation order, not date-sorted -- SQuaD's process_metrics.csv has no per-project release date column, unlike release_data.csv), StandardScaler fit on train only, 5-fold TimeSeriesSplit CV.
