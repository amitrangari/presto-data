# M10 — Nested Model Selection, All Synthetic Domains

Full-algorithm nested cross-validation (see `nested_cv_harness.py` for the protocol and hyperparameter grids), replacing the paper's fixed-holdout "best of 5 models" selection with a genuinely nested one: model and hyperparameter choice happens entirely within the outer 80% training partition via `TimeSeriesSplit(5)`; the outer 20% holdout is scored exactly once, by the already-selected configuration. This supersedes the selection *mechanism* in Section 3.2.4's Model-Selection Rule; it does not change the underlying data or feature engineering.

**Old-vs-new comparison** is against `main_mdpi_v3`'s already-published fixed-holdout-selection numbers (Tables `model_perf_with`/`model_perf_without`, `cross_domain`).

## abc-cloud-provider

### with_AR

| Model | Inner CV R² | Best hyperparameters | Holdout R² (all candidates, for reference only — not used for selection) | Holdout MAE | Holdout RMSE |
|---|---:|---|---:|---:|---:|
| Ridge Regression **(nested-selected)** | 0.0464 | alpha=1000.0 | 0.1111 | 0.4502 | 0.6000 |
| Lasso Regression | 0.0387 | alpha=1.0 | -0.0204 | 0.5570 | 0.6429 |
| Random Forest | -0.6163 | min_samples_leaf=2, random_state=42, max_depth=10, min_samples_split=5, n_estimators=50 | 0.3701 | 0.2493 | 0.5051 |
| Gradient Boosting | -1.4897 | min_samples_split=5, min_samples_leaf=2, random_state=42, learning_rate=0.2, max_depth=3, n_estimators=50 | 0.1344 | 0.2516 | 0.5921 |
| Linear Regression | -3.5833 |  | -13.3405 | 1.8389 | 2.4100 |

**Nested-selected:** Ridge Regression, holdout R² = 0.1111 (selected by inner CV R² = 0.0464, never by holdout score).
**Old fixed-holdout-selection protocol on this same split** would pick: Random Forest, holdout R² = 0.3701.
**Paper's already-published number** (main_mdpi_v3): Random Forest, holdout R² = 0.914.
**Verdict:** nested selection picks a DIFFERENT model as the published result (Ridge Regression vs. Random Forest); nested holdout R² differs from the published figure by -0.8029.
(n_train=136, n_test=34, n_features=273, wall time 54.0s)

### without_AR

| Model | Inner CV R² | Best hyperparameters | Holdout R² (all candidates, for reference only — not used for selection) | Holdout MAE | Holdout RMSE |
|---|---:|---|---:|---:|---:|
| Ridge Regression **(nested-selected)** | 0.1248 | alpha=1000.0 | 0.1077 | 0.4591 | 0.6012 |
| Lasso Regression | 0.0387 | alpha=1.0 | -0.0204 | 0.5570 | 0.6429 |
| Random Forest | -0.7293 | min_samples_leaf=2, random_state=42, max_depth=10, min_samples_split=2, n_estimators=50 | 0.1897 | 0.2990 | 0.5729 |
| Gradient Boosting | -1.7806 | min_samples_split=5, min_samples_leaf=2, random_state=42, learning_rate=0.05, max_depth=3, n_estimators=50 | 0.2152 | 0.2798 | 0.5638 |
| Linear Regression | -4.9006 |  | -6.9455 | 1.4472 | 1.7939 |

**Nested-selected:** Ridge Regression, holdout R² = 0.1077 (selected by inner CV R² = 0.1248, never by holdout score).
**Old fixed-holdout-selection protocol on this same split** would pick: Gradient Boosting, holdout R² = 0.2152.
**Paper's already-published number** (main_mdpi_v3): Random Forest, holdout R² = 0.107.
**Verdict:** nested selection picks a DIFFERENT model as the published result (Ridge Regression vs. Random Forest); nested holdout R² differs from the published figure by +0.0007.
(n_train=136, n_test=34, n_features=241, wall time 48.7s)

## card-payment-processor

### with_AR

| Model | Inner CV R² | Best hyperparameters | Holdout R² (all candidates, for reference only — not used for selection) | Holdout MAE | Holdout RMSE |
|---|---:|---|---:|---:|---:|
| Ridge Regression **(nested-selected)** | 0.6150 | alpha=316.22776601683796 | 0.6383 | 0.6572 | 0.8439 |
| Random Forest | 0.5103 | min_samples_leaf=2, random_state=42, max_depth=5, min_samples_split=2, n_estimators=200 | 0.4336 | 0.4761 | 1.0560 |
| Lasso Regression | 0.4760 | alpha=1.0 | 0.3610 | 0.7724 | 1.1217 |
| Linear Regression | 0.4476 |  | 0.3885 | 0.9076 | 1.0972 |
| Gradient Boosting | 0.2845 | min_samples_split=5, min_samples_leaf=2, random_state=42, learning_rate=0.2, max_depth=6, n_estimators=200 | -0.0079 | 0.6369 | 1.4087 |

**Nested-selected:** Ridge Regression, holdout R² = 0.6383 (selected by inner CV R² = 0.6150, never by holdout score).
**Old fixed-holdout-selection protocol on this same split** would pick: Ridge Regression, holdout R² = 0.6383.
(n_train=120, n_test=30, n_features=273, wall time 45.9s)

### without_AR

| Model | Inner CV R² | Best hyperparameters | Holdout R² (all candidates, for reference only — not used for selection) | Holdout MAE | Holdout RMSE |
|---|---:|---|---:|---:|---:|
| Ridge Regression **(nested-selected)** | 0.6347 | alpha=316.22776601683796 | 0.6082 | 0.7116 | 0.8784 |
| Random Forest | 0.5116 | min_samples_leaf=2, random_state=42, max_depth=5, min_samples_split=2, n_estimators=100 | 0.4833 | 0.4753 | 1.0086 |
| Lasso Regression | 0.4760 | alpha=1.0 | 0.3610 | 0.7724 | 1.1217 |
| Linear Regression | 0.4519 |  | 0.3047 | 0.9406 | 1.1700 |
| Gradient Boosting | 0.3093 | min_samples_split=5, min_samples_leaf=2, random_state=42, learning_rate=0.1, max_depth=6, n_estimators=50 | -0.0457 | 0.6133 | 1.4349 |

**Nested-selected:** Ridge Regression, holdout R² = 0.6082 (selected by inner CV R² = 0.6347, never by holdout score).
**Old fixed-holdout-selection protocol on this same split** would pick: Ridge Regression, holdout R² = 0.6082.
**Paper's already-published number** (main_mdpi_v3): Random Forest, holdout R² = 0.475.
**Verdict:** nested selection picks a DIFFERENT model as the published result (Ridge Regression vs. Random Forest); nested holdout R² differs from the published figure by +0.1332.
(n_train=120, n_test=30, n_features=241, wall time 41.3s)

## xyz-sales-force

### with_AR

| Model | Inner CV R² | Best hyperparameters | Holdout R² (all candidates, for reference only — not used for selection) | Holdout MAE | Holdout RMSE |
|---|---:|---|---:|---:|---:|
| Lasso Regression **(nested-selected)** | 0.6087 | alpha=0.31622776601683794 | 0.6202 | 0.4405 | 0.6817 |
| Ridge Regression | 0.5596 | alpha=316.22776601683796 | 0.4878 | 0.5602 | 0.7917 |
| Gradient Boosting | 0.3993 | min_samples_split=5, min_samples_leaf=2, random_state=42, learning_rate=0.2, max_depth=3, n_estimators=50 | 0.5138 | 0.3961 | 0.7713 |
| Random Forest | 0.3885 | min_samples_leaf=2, random_state=42, max_depth=5, min_samples_split=5, n_estimators=100 | 0.4883 | 0.4429 | 0.7914 |
| Linear Regression | 0.1383 |  | -3.2492 | 1.8641 | 2.2804 |

**Nested-selected:** Lasso Regression, holdout R² = 0.6202 (selected by inner CV R² = 0.6087, never by holdout score).
**Old fixed-holdout-selection protocol on this same split** would pick: Lasso Regression, holdout R² = 0.6202.
(n_train=160, n_test=40, n_features=273, wall time 639.2s)

### without_AR

| Model | Inner CV R² | Best hyperparameters | Holdout R² (all candidates, for reference only — not used for selection) | Holdout MAE | Holdout RMSE |
|---|---:|---|---:|---:|---:|
| Lasso Regression **(nested-selected)** | 0.6033 | alpha=0.31622776601683794 | 0.6202 | 0.4405 | 0.6817 |
| Ridge Regression | 0.5695 | alpha=316.22776601683796 | 0.4621 | 0.5854 | 0.8114 |
| Random Forest | 0.4074 | min_samples_leaf=2, random_state=42, max_depth=None, min_samples_split=5, n_estimators=100 | 0.4871 | 0.4478 | 0.7922 |
| Gradient Boosting | 0.3194 | min_samples_split=5, min_samples_leaf=2, random_state=42, learning_rate=0.2, max_depth=3, n_estimators=200 | 0.5800 | 0.3530 | 0.7169 |
| Linear Regression | -0.0989 |  | -5.1850 | 2.1889 | 2.7512 |

**Nested-selected:** Lasso Regression, holdout R² = 0.6202 (selected by inner CV R² = 0.6033, never by holdout score).
**Old fixed-holdout-selection protocol on this same split** would pick: Lasso Regression, holdout R² = 0.6202.
**Paper's already-published number** (main_mdpi_v3): Gradient Boosting, holdout R² = 0.490.
**Verdict:** nested selection picks a DIFFERENT model as the published result (Lasso Regression vs. Gradient Boosting); nested holdout R² differs from the published figure by +0.1302.
(n_train=160, n_test=40, n_features=241, wall time 67.2s)
