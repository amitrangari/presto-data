# Real-World Bootstrap Confidence Intervals

Extends `code/synthetic_data_generator/r1_analysis.py`'s bootstrap-CI procedure (pairs/case bootstrap on the holdout (y_true, y_pred) pairs, 2000 resamples, seed 20260810, fitted model held fixed) to the four real-world validation datasets, per the 2026-08-13 consensus review's Priority 1 finding. Same method, same seed, same resample count as the synthetic-domain analysis for direct comparability.

## GHALogs (mean CI run duration, n=28443)

| Model | Holdout R2 | 95% CI | Excludes zero |
|---|---|---|---|
| Gradient Boosting | 0.1130 | [0.0501, 0.3558] | yes |
| Lasso Regression | 0.0999 | [0.0620, 0.2665] | yes |
| Ridge Regression | 0.0998 | [0.0620, 0.2667] | yes |
| Linear Regression | 0.0998 | [0.0620, 0.2666] | yes |
| Random Forest | 0.0964 | [0.0210, 0.2989] | yes |

## SQuaD defect-fix rate (n=408)

| Model | Holdout R2 | 95% CI | Excludes zero |
|---|---|---|---|
| Random Forest | 0.4023 | [-0.2453, 0.7478] | no |
| Gradient Boosting | -0.3253 | [-1.4081, 0.3982] | no |
| Lasso Regression | -0.4087 | [-2.5537, 0.6647] | no |
| Ridge Regression | -0.4421 | [-2.6508, 0.6704] | no |
| Linear Regression | -0.4545 | [-2.6845, 0.6704] | no |

## SQuaD CVE-count, log1p (n=408)

| Model | Holdout R2 | 95% CI | Excludes zero |
|---|---|---|---|
| Random Forest | 0.2453 | [0.0526, 0.3700] | yes |
| Gradient Boosting | 0.2237 | [-0.0533, 0.4065] | no |
| Lasso Regression | -0.0324 | [-0.1282, -0.0003] | yes |
| Ridge Regression | -0.8367 | [-2.3286, 0.0664] | no |
| Linear Regression | -0.9490 | [-2.4676, 0.0420] | no |
