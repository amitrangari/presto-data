# M3 — Nested-CV Alpha Tuning for Ridge/Lasso

Protocol: GridSearchCV over alpha in [1e-3 .. 1e6] (19 log-spaced points -- widened from an initial [1e-3 .. 1e3] after two Ridge cases selected the grid boundary; all selected alphas are now interior points), inner cv=TimeSeriesSplit(5) within the fixed 80% outer-training split only; best alpha refit on the full outer-train, scored on the untouched 20% outer holdout. Compared against the paper's existing fixed alpha=1.0 baseline on the identical split.

## abc-cloud-provider

| Condition | Model | Best alpha | Inner CV R² | Tuned Holdout R² | alpha=1.0 Holdout R² | Δ (tuned − baseline) |
|---|---|---:|---:|---:|---:|---:|
| with_AR | Ridge | 1000 | 0.2295 | 0.3248 | -0.5917 | +0.9165 |
| with_AR | Lasso | 0.0316228 | 0.1924 | 0.7318 | -0.0204 | +0.7523 |
| without_AR | Ridge | 1000 | 0.1248 | 0.1077 | -5.5823 | +5.6900 |
| without_AR | Lasso | 1 | 0.0387 | -0.0204 | -0.0204 | +0.0000 |

For context, Random Forest (fixed hyperparameters, unchanged) scores holdout R² = 0.1065 on the without-AR condition.

## card-payment-processor

| Condition | Model | Best alpha | Inner CV R² | Tuned Holdout R² | alpha=1.0 Holdout R² | Δ (tuned − baseline) |
|---|---|---:|---:|---:|---:|---:|
| with_AR | Ridge | 100 | 0.7265 | 0.7069 | 0.7068 | +0.0001 |
| with_AR | Lasso | 0.0316228 | 0.5223 | 0.8505 | 0.3610 | +0.4895 |
| without_AR | Ridge | 316.228 | 0.6347 | 0.6082 | 0.3695 | +0.2387 |
| without_AR | Lasso | 1 | 0.4760 | 0.3610 | 0.3610 | +0.0000 |

For context, Random Forest (fixed hyperparameters, unchanged) scores holdout R² = 0.4752 on the without-AR condition.

## xyz-sales-force

| Condition | Model | Best alpha | Inner CV R² | Tuned Holdout R² | alpha=1.0 Holdout R² | Δ (tuned − baseline) |
|---|---|---:|---:|---:|---:|---:|
| with_AR | Ridge | 100 | 0.7397 | 0.6996 | -0.0336 | +0.7331 |
| with_AR | Lasso | 0.0316228 | 0.8200 | 0.9489 | 0.2448 | +0.7041 |
| without_AR | Ridge | 316.228 | 0.5695 | 0.4621 | -3.5612 | +4.0232 |
| without_AR | Lasso | 0.316228 | 0.6033 | 0.6202 | 0.2322 | +0.3881 |

For context, Random Forest (fixed hyperparameters, unchanged) scores holdout R² = 0.4872 on the without-AR condition.
