# M9 — System Availability (%) Ablation

Protocol: for each domain and each of the with-AR / without-AR feature conditions, remove `System Availability (%)` and every engineered feature derived from it (rolling/lag/cross-phase composites), retrain and re-evaluate Random Forest (the model whose feature importances flagged this feature in Section 4.5) with unchanged fixed hyperparameters, and compare holdout R² and the new top feature to the full-feature-set baseline.

## abc-cloud-provider

| Condition | Features (full → ablated) | RF Holdout R² (full) | RF Holdout R² (ablated) | Δ | Sys. Avail. rank (full) | New top feature (ablated) |
|---|---|---:|---:|---:|---|---|
| with_AR | 273 → 272 | 0.9501 | 0.9412 | -0.0089 | #5 (3.9%) | System Uptime (%)_pct_change_3 (27.0%) |
| without_AR | 241 → 240 | 0.2683 | -0.0419 | -0.3102 | #2 (14.8%) | Test Environment Availability (%) (23.0%) |

## card-payment-processor

| Condition | Features (full → ablated) | RF Holdout R² (full) | RF Holdout R² (ablated) | Δ | Sys. Avail. rank (full) | New top feature (ablated) |
|---|---|---:|---:|---:|---|---|
| with_AR | 273 → 272 | 0.7867 | 0.9428 | +0.1560 | #1 (28.8%) | UAT Environment Stability (%) (13.6%) |
| without_AR | 241 → 240 | 0.3392 | 0.7063 | +0.3671 | #1 (48.2%) | UAT Environment Stability (%) (30.9%) |

## xyz-sales-force

| Condition | Features (full → ablated) | RF Holdout R² (full) | RF Holdout R² (ablated) | Δ | Sys. Avail. rank (full) | New top feature (ablated) |
|---|---|---:|---:|---:|---|---|
| with_AR | 273 → 272 | 0.9707 | 0.9640 | -0.0067 | #6 (2.6%) | System Uptime (%)_pct_change_1 (25.9%) |
| without_AR | 241 → 240 | 0.2546 | 0.1680 | -0.0866 | #2 (19.0%) | UAT Environment Stability (%) (42.1%) |
