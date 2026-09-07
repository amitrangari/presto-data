# M3 — Nested-CV Alpha Tuning for Ridge/Lasso

Protocol: GridSearchCV over alpha in [1e-3 .. 1e6] (19 log-spaced points -- widened from an initial [1e-3 .. 1e3] after two Ridge cases selected the grid boundary; all selected alphas are now interior points), inner cv=TimeSeriesSplit(5) within the fixed 80% outer-training split only; best alpha refit on the full outer-train, scored on the untouched 20% outer holdout. Compared against the paper's existing fixed alpha=1.0 baseline on the identical split.

## abc-cloud-provider

| Condition | Model | Best alpha | Inner CV R² | Tuned Holdout R² | alpha=1.0 Holdout R² | Δ (tuned − baseline) |
|---|---|---:|---:|---:|---:|---:|
| with_AR | Ridge | 1000 | 0.5079 | 0.3581 | -0.1937 | +0.5517 |
| with_AR | Lasso | 0.0316228 | 0.3222 | 0.4022 | 0.1288 | +0.2733 |
| without_AR | Ridge | 1000 | 0.4396 | 0.0673 | -7.2850 | +7.3523 |
| without_AR | Lasso | 1 | 0.3406 | 0.1288 | 0.1288 | +0.0000 |

For context, Random Forest (fixed hyperparameters, unchanged) scores holdout R² = 0.2683 on the without-AR condition.

## card-payment-processor

| Condition | Model | Best alpha | Inner CV R² | Tuned Holdout R² | alpha=1.0 Holdout R² | Δ (tuned − baseline) |
|---|---|---:|---:|---:|---:|---:|
| with_AR | Ridge | 316.228 | 0.6711 | 0.8408 | 0.4935 | +0.3474 |
| with_AR | Lasso | 0.01 | 0.5170 | 0.6999 | 0.3615 | +0.3384 |
| without_AR | Ridge | 316.228 | 0.6078 | 0.7656 | -0.2154 | +0.9809 |
| without_AR | Lasso | 1 | 0.4644 | 0.3615 | 0.3615 | +0.0000 |

For context, Random Forest (fixed hyperparameters, unchanged) scores holdout R² = 0.3392 on the without-AR condition.

## xyz-sales-force

| Condition | Model | Best alpha | Inner CV R² | Tuned Holdout R² | alpha=1.0 Holdout R² | Δ (tuned − baseline) |
|---|---|---:|---:|---:|---:|---:|
| with_AR | Ridge | 100 | 0.7179 | 0.5177 | -0.7381 | +1.2558 |
| with_AR | Lasso | 0.0316228 | 0.7929 | 0.8881 | 0.0121 | +0.8761 |
| without_AR | Ridge | 316.228 | 0.5545 | 0.1531 | -4.1042 | +4.2573 |
| without_AR | Lasso | 0.316228 | 0.5930 | 0.4183 | 0.0121 | +0.4063 |

For context, Random Forest (fixed hyperparameters, unchanged) scores holdout R² = 0.2546 on the without-AR condition.
