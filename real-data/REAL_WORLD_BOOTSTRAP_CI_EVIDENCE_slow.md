# Real-World Bootstrap Confidence Intervals

Extends `code/synthetic_data_generator/r1_analysis.py`'s bootstrap-CI procedure (pairs/case bootstrap on the holdout (y_true, y_pred) pairs, 2000 resamples, seed 20260810, fitted model held fixed) to the four real-world validation datasets, per the 2026-08-13 consensus review's Priority 1 finding. Same method, same seed, same resample count as the synthetic-domain analysis for direct comparability.

## Perfherder espn-loadtime, with-AR (n=3548)

| Model | Holdout R2 | 95% CI | Excludes zero |
|---|---|---|---|
| Ridge Regression | 0.5735 | [0.4988, 0.6354] | yes |
| Linear Regression | 0.5719 | [0.4973, 0.6339] | yes |
| Lasso Regression | 0.5719 | [0.5003, 0.6309] | yes |
| Random Forest | 0.2353 | [0.1473, 0.3109] | yes |
| Gradient Boosting | 0.1239 | [0.0197, 0.2153] | yes |

## Perfherder instagram-speedindex, with-AR (n=3177)

| Model | Holdout R2 | 95% CI | Excludes zero |
|---|---|---|---|
| Ridge Regression | 0.9127 | [0.8827, 0.9368] | yes |
| Linear Regression | 0.8798 | [0.8068, 0.9324] | yes |
| Lasso Regression | 0.8267 | [0.8017, 0.8473] | yes |
| Random Forest | 0.1527 | [0.1081, 0.1912] | yes |
| Gradient Boosting | 0.1113 | [0.0622, 0.1539] | yes |

## Perfherder nytimes-speedindex, with-AR (n=3225)

| Model | Holdout R2 | 95% CI | Excludes zero |
|---|---|---|---|
| Ridge Regression | 0.1666 | [0.0922, 0.2318] | yes |
| Linear Regression | 0.1659 | [0.0921, 0.2302] | yes |
| Lasso Regression | 0.1576 | [0.0821, 0.2233] | yes |
| Random Forest | 0.1261 | [0.0386, 0.2001] | yes |
| Gradient Boosting | 0.0308 | [-0.0682, 0.1116] | no |

## TravisTorrent DataDog/dd-agent (n=143925)

| Model | Holdout R2 | 95% CI | Excludes zero |
|---|---|---|---|
| Gradient Boosting | 0.0179 | [-0.0006, 0.0347] | no |
| Random Forest | -0.6226 | [-0.6527, -0.5925] | yes |
| Lasso Regression | -14034880.8822 | [-25663009.1779, -5013506.9059] | yes |
| Ridge Regression | -21699491.7121 | [-39677937.8708, -7751435.5323] | yes |
| Linear Regression | -21824054.8128 | [-39905774.4239, -7795923.2809] | yes |

## TravisTorrent bundler/bundler (n=80538)

| Model | Holdout R2 | 95% CI | Excludes zero |
|---|---|---|---|
| Random Forest | -0.1514 | [-0.1936, -0.1142] | yes |
| Gradient Boosting | -0.6101 | [-0.6945, -0.5396] | yes |
| Ridge Regression | -3.7187 | [-4.0966, -3.3902] | yes |
| Linear Regression | -3.8527 | [-4.2413, -3.5136] | yes |
| Lasso Regression | -4.4265 | [-4.8655, -4.0479] | yes |

## TravisTorrent getsentry/sentry (n=55890)

| Model | Holdout R2 | 95% CI | Excludes zero |
|---|---|---|---|
| Gradient Boosting | 0.0497 | [0.0343, 0.0639] | yes |
| Random Forest | -0.1126 | [-0.1314, -0.0951] | yes |
| Linear Regression | -3.9731 | [-4.1517, -3.8027] | yes |
| Ridge Regression | -3.9845 | [-4.1636, -3.8137] | yes |
| Lasso Regression | -4.2235 | [-4.4122, -4.0410] | yes |

## TravisTorrent gonum/matrix (n=2348)

| Model | Holdout R2 | 95% CI | Excludes zero |
|---|---|---|---|
| Random Forest | 0.0052 | [-0.2818, 0.2140] | no |
| Gradient Boosting | -0.1424 | [-0.4917, 0.1043] | no |
| Lasso Regression | -2.5166 | [-6.9568, -0.4985] | yes |
| Ridge Regression | -11.5621 | [-20.1135, -6.9634] | yes |
| Linear Regression | -12.8614 | [-21.9964, -7.8899] | yes |

## TravisTorrent mongodb/mongoid (n=36423)

| Model | Holdout R2 | 95% CI | Excludes zero |
|---|---|---|---|
| Gradient Boosting | -0.0396 | [-0.0481, -0.0315] | yes |
| Random Forest | -0.0857 | [-0.0943, -0.0773] | yes |
| Lasso Regression | -0.1620 | [-0.1753, -0.1488] | yes |
| Ridge Regression | -0.1639 | [-0.1775, -0.1507] | yes |
| Linear Regression | -0.1641 | [-0.1778, -0.1508] | yes |

## TravisTorrent rg3/youtube-dl (n=36260)

| Model | Holdout R2 | 95% CI | Excludes zero |
|---|---|---|---|
| Linear Regression | 0.4753 | [0.4545, 0.4945] | yes |
| Ridge Regression | 0.4751 | [0.4542, 0.4944] | yes |
| Lasso Regression | 0.4722 | [0.4511, 0.4920] | yes |
| Random Forest | 0.3890 | [0.3607, 0.4172] | yes |
| Gradient Boosting | 0.2855 | [0.2550, 0.3141] | yes |

## TravisTorrent rspec/rspec-core (n=29963)

| Model | Holdout R2 | 95% CI | Excludes zero |
|---|---|---|---|
| Random Forest | -0.2936 | [-0.3752, -0.2232] | yes |
| Gradient Boosting | -0.3871 | [-0.4620, -0.3216] | yes |
| Lasso Regression | -1.7351 | [-2.0059, -1.5145] | yes |
| Ridge Regression | -2.3278 | [-2.8164, -1.9469] | yes |
| Linear Regression | -3.2091 | [-3.8375, -2.7096] | yes |
