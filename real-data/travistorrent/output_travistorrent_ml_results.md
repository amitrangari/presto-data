# ML Pipeline Results: TravisTorrent (real data, within-project temporal)

**Task:** predict build duration (`tr_duration`, seconds) from real CI/build process characteristics, per project, using an 80/20 temporal split. Reimplemented adapter (R7) -- see script docstring for full methodology and data provenance.

**Median best-model R² across all 7 projects: 0.005** (4/7 projects achieve positive R²).

## Best model per project

| Project | Builds | Best Model | Holdout R² | MAE (s) |
|---|---:|---|---:|---:|
| rg3/youtube-dl | 36260 | Linear Regression | 0.475 | 1700.2 |
| getsentry/sentry | 55890 | Gradient Boosting | 0.050 | 238.3 |
| DataDog/dd-agent | 143925 | Gradient Boosting | 0.018 | 1540.3 |
| gonum/matrix | 2348 | Random Forest | 0.005 | 47.5 |
| mongodb/mongoid | 36423 | Gradient Boosting | -0.040 | 5162.1 |
| bundler/bundler | 80538 | Random Forest | -0.151 | 5118.3 |
| rspec/rspec-core | 29963 | Random Forest | -0.294 | 1013.1 |

## Full model comparison, per project

### DataDog/dd-agent (143925 builds, 149 features)

| Model | CV R² (mean +/- std) | Holdout R² | Holdout MAE | Holdout RMSE |
|---|---|---|---|---|
| Gradient Boosting | -0.3514 +/- 0.4799 | 0.0179 | 1540.28 | 1834.30 |
| Random Forest | -0.6875 +/- 0.5331 | -0.6226 | 2035.60 | 2357.70 |
| Lasso Regression | -1.2110 +/- 1.9116 | -14034880.8822 | 149260.28 | 6934085.38 |
| Ridge Regression | -1.2354 +/- 1.8789 | -21699491.7121 | 185300.32 | 8622031.28 |
| Linear Regression | -1.2407 +/- 1.8772 | -21824054.8128 | 185827.63 | 8646742.69 |

### bundler/bundler (80538 builds, 149 features)

| Model | CV R² (mean +/- std) | Holdout R² | Holdout MAE | Holdout RMSE |
|---|---|---|---|---|
| Random Forest | -1.5902 +/- 1.0620 | -0.1514 | 5118.32 | 6857.34 |
| Gradient Boosting | -1.5717 +/- 1.5171 | -0.6101 | 6617.30 | 8109.05 |
| Ridge Regression | -3.4120 +/- 4.0134 | -3.7187 | 12250.40 | 13881.89 |
| Linear Regression | -4.3572 +/- 3.2230 | -3.8527 | 12416.65 | 14077.68 |
| Lasso Regression | -2.8971 +/- 2.9709 | -4.4265 | 13163.18 | 14886.73 |

### getsentry/sentry (55890 builds, 149 features)

| Model | CV R² (mean +/- std) | Holdout R² | Holdout MAE | Holdout RMSE |
|---|---|---|---|---|
| Gradient Boosting | -1.1754 +/- 0.5923 | 0.0497 | 238.30 | 313.68 |
| Random Forest | -0.9300 +/- 0.4334 | -0.1126 | 271.44 | 339.40 |
| Linear Regression | -114.1924 +/- 207.9887 | -3.9731 | 625.26 | 717.57 |
| Ridge Regression | -54.2633 +/- 91.7601 | -3.9845 | 626.09 | 718.39 |
| Lasso Regression | -8.6360 +/- 7.3888 | -4.2235 | 652.40 | 735.41 |

### gonum/matrix (2348 builds, 149 features)

| Model | CV R² (mean +/- std) | Holdout R² | Holdout MAE | Holdout RMSE |
|---|---|---|---|---|
| Random Forest | -0.2202 +/- 0.1975 | 0.0052 | 47.53 | 65.60 |
| Gradient Boosting | -0.1720 +/- 0.4599 | -0.1424 | 49.78 | 70.30 |
| Lasso Regression | -12.7830 +/- 18.5557 | -2.5166 | 68.63 | 123.34 |
| Ridge Regression | -5.8734 +/- 5.7711 | -11.5621 | 184.87 | 233.11 |
| Linear Regression | -10676.3488 +/- 20990.5624 | -12.8614 | 196.53 | 244.87 |

### mongodb/mongoid (36423 builds, 149 features)

| Model | CV R² (mean +/- std) | Holdout R² | Holdout MAE | Holdout RMSE |
|---|---|---|---|---|
| Gradient Boosting | -2.0407 +/- 3.5364 | -0.0396 | 5162.11 | 9105.66 |
| Random Forest | -0.9315 +/- 1.2991 | -0.0857 | 5382.85 | 9305.25 |
| Lasso Regression | -1.9386 +/- 1.5672 | -0.1620 | 5521.00 | 9626.76 |
| Ridge Regression | -2.2858 +/- 1.5973 | -0.1639 | 5547.56 | 9634.79 |
| Linear Regression | -2.5692 +/- 1.4801 | -0.1641 | 5549.13 | 9635.61 |

### rg3/youtube-dl (36260 builds, 149 features)

| Model | CV R² (mean +/- std) | Holdout R² | Holdout MAE | Holdout RMSE |
|---|---|---|---|---|
| Linear Regression | -0.5686 +/- 0.8548 | 0.4753 | 1700.20 | 2465.89 |
| Ridge Regression | -0.3701 +/- 0.8946 | 0.4751 | 1699.85 | 2466.21 |
| Lasso Regression | -0.3273 +/- 0.7643 | 0.4722 | 1694.95 | 2473.12 |
| Random Forest | -2.5482 +/- 3.6453 | 0.3890 | 1573.83 | 2660.97 |
| Gradient Boosting | -3.6754 +/- 4.3111 | 0.2855 | 1792.91 | 2877.41 |

### rspec/rspec-core (29963 builds, 149 features)

| Model | CV R² (mean +/- std) | Holdout R² | Holdout MAE | Holdout RMSE |
|---|---|---|---|---|
| Random Forest | -0.1493 +/- 0.3033 | -0.2936 | 1013.07 | 1600.49 |
| Gradient Boosting | -0.0483 +/- 0.1796 | -0.3871 | 1193.38 | 1657.35 |
| Lasso Regression | -1.1742 +/- 0.5111 | -1.7351 | 1735.82 | 2327.25 |
| Ridge Regression | -1.4683 +/- 0.6080 | -2.3278 | 1856.91 | 2567.06 |
| Linear Regression | -1.4458 +/- 0.3404 | -3.2091 | 2132.72 | 2887.02 |

## Notes

- Real TravisTorrent data (CC-BY-4.0, Figshare doi:10.6084/m9.figshare.19314170), filtered to the 7 projects the manuscript names, non-PR builds only, deduped to one row per build, outliers (below 1st/above 99th percentile of tr_duration) removed.
- 4 of 8 SDLC phases covered (Code, Test, Build, Project); `tr_log_buildduration` is 100% NA in this dataset and was dropped rather than used as a Build-phase feature.
- 80/20 temporal split (sorted by `gh_build_started_at`), StandardScaler fit on train only, 5-fold TimeSeriesSplit CV, same 5 scikit-learn models used throughout this paper.
