# M9 — System Availability (%) Ablation

Protocol: for each domain and each of the with-AR / without-AR feature conditions, remove `System Availability (%)` and every engineered feature derived from it (rolling/lag/cross-phase composites), retrain and re-evaluate Random Forest (the model whose feature importances flagged this feature in Section 4.5) with unchanged fixed hyperparameters, and compare holdout R² and the new top feature to the full-feature-set baseline.

## abc-cloud-provider

| Condition | Features (full → ablated) | RF Holdout R² (full) | RF Holdout R² (ablated) | Δ | Sys. Avail. rank (full) | New top feature (ablated) |
|---|---|---:|---:|---:|---|---|
| with_AR | 273 → 272 | 0.9141 | 0.8717 | -0.0424 | #6 (4.2%) | System Uptime (%)_pct_change_3 (29.4%) |
| without_AR | 241 → 240 | 0.1065 | -0.0145 | -0.1210 | #4 (10.8%) | Test Environment Availability (%) (21.9%) |

## card-payment-processor

| Condition | Features (full → ablated) | RF Holdout R² (full) | RF Holdout R² (ablated) | Δ | Sys. Avail. rank (full) | New top feature (ablated) |
|---|---|---:|---:|---:|---|---|
| with_AR | 273 → 272 | 0.8073 | 0.9028 | +0.0954 | #2 (13.2%) | System Uptime (%)_diff_2 (17.8%) |
| without_AR | 241 → 240 | 0.4752 | 0.7203 | +0.2450 | #1 (33.1%) | UAT Environment Stability (%) (36.6%) |

## xyz-sales-force

| Condition | Features (full → ablated) | RF Holdout R² (full) | RF Holdout R² (ablated) | Δ | Sys. Avail. rank (full) | New top feature (ablated) |
|---|---|---:|---:|---:|---|---|
| with_AR | 273 → 272 | 0.9448 | 0.9539 | +0.0091 | #6 (5.7%) | System Uptime (%)_pct_change_1 (24.8%) |
| without_AR | 241 → 240 | 0.4872 | 0.3507 | -0.1365 | #1 (33.8%) | UAT Environment Stability (%) (44.0%) |
