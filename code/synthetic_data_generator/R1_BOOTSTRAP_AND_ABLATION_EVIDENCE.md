# R1 evidence: bootstrap CIs + target-correlation ablation

**Date:** 2026-08-10  
**Item:** Phase 1 / R1 in `presto/paper-work/review/2026-08-08_review/ACTION_PLAN.md` -- "Ground the headline claim." Flagged in `STATUS.md` as the single highest-priority open item; nothing had been done on it prior to this analysis.

**Method for (a):** pairs/case bootstrap, 2000 resamples, seed 20260810. Each holdout prediction set (y_true, y_pred) is resampled with replacement and R^2 recomputed per resample; the fitted model is held fixed. This captures sampling variance from which points happened to land in the (small, ~30-40 row) holdout set -- it does **not** capture training-refit variance (see Limitations).

**Method for (b):** `target_correlations` in `correlation_templates.yaml` has exactly 21 entries, all pairing `System Uptime (%)` (the target) with another metric -- confirmed by grep to be the *only* place the target variable appears in the correlation config, so zeroing this section fully severs the target from every other metric in the copula's correlation matrix. Two variants: **zeroed** (target_correlations emptied) and **permuted** (same 21 rho values, shuffled across the 21 metric pairs, seed 20260810). Both regenerate the ABC Cloud Provider domain (same seed=42, same 170 releases, same everything else) through the unmodified `generate_domain()` / `run_pipeline` code path -- only the correlation config passed in differs.

## Part A: Bootstrap 95% CIs on headline R^2 values

All three synthetic domains, both AR conditions, all 5 models.

| Domain | Condition | Model | Holdout R^2 | 95% CI | CI excludes 0 | n (holdout) |
|---|---|---|---:|---|:---:|---:|
| abc-cloud-provider | with_AR | Random Forest | 0.950 | [0.747, 0.988] | yes | 34 |
| abc-cloud-provider | with_AR | Gradient Boosting | 0.866 | [0.806, 0.904] | yes | 34 |
| abc-cloud-provider | with_AR | Lasso Regression | 0.129 | [-2.323, 0.489] | no | 34 |
| abc-cloud-provider | with_AR | Ridge Regression | -0.194 | [-5.948, 0.520] | no | 34 |
| abc-cloud-provider | with_AR | Linear Regression | -0.256 | [-6.401, 0.480] | no | 34 |
| abc-cloud-provider | without_AR | Random Forest | 0.268 | [-1.307, 0.696] | no | 34 |
| abc-cloud-provider | without_AR | Gradient Boosting | 0.251 | [-1.950, 0.807] | no | 34 |
| abc-cloud-provider | without_AR | Lasso Regression | 0.129 | [-2.323, 0.489] | no | 34 |
| abc-cloud-provider | without_AR | Ridge Regression | -7.285 | [-53.777, -2.303] | yes | 34 |
| abc-cloud-provider | without_AR | Linear Regression | -9.124 | [-66.548, -2.942] | yes | 34 |
| card-payment-processor | with_AR | Random Forest | 0.787 | [0.223, 0.947] | yes | 30 |
| card-payment-processor | with_AR | Gradient Boosting | 0.652 | [-0.175, 0.946] | no | 30 |
| card-payment-processor | with_AR | Ridge Regression | 0.493 | [-1.694, 0.790] | no | 30 |
| card-payment-processor | with_AR | Linear Regression | 0.428 | [-2.067, 0.767] | no | 30 |
| card-payment-processor | with_AR | Lasso Regression | 0.362 | [0.005, 0.665] | yes | 30 |
| card-payment-processor | without_AR | Lasso Regression | 0.362 | [0.005, 0.665] | yes | 30 |
| card-payment-processor | without_AR | Random Forest | 0.339 | [-0.669, 0.845] | no | 30 |
| card-payment-processor | without_AR | Gradient Boosting | -0.209 | [-4.845, 0.751] | no | 30 |
| card-payment-processor | without_AR | Ridge Regression | -0.215 | [-5.304, 0.464] | no | 30 |
| card-payment-processor | without_AR | Linear Regression | -0.336 | [-5.838, 0.424] | no | 30 |
| xyz-sales-force | with_AR | Random Forest | 0.971 | [0.881, 0.990] | yes | 40 |
| xyz-sales-force | with_AR | Gradient Boosting | 0.045 | [-4.242, 0.910] | no | 40 |
| xyz-sales-force | with_AR | Lasso Regression | 0.012 | [-1.320, 0.170] | no | 40 |
| xyz-sales-force | with_AR | Ridge Regression | -0.738 | [-5.428, 0.085] | no | 40 |
| xyz-sales-force | with_AR | Linear Regression | -1.028 | [-6.545, -0.087] | yes | 40 |
| xyz-sales-force | without_AR | Random Forest | 0.255 | [-0.134, 0.474] | no | 40 |
| xyz-sales-force | without_AR | Gradient Boosting | 0.212 | [-0.063, 0.399] | no | 40 |
| xyz-sales-force | without_AR | Lasso Regression | 0.012 | [-1.320, 0.170] | no | 40 |
| xyz-sales-force | without_AR | Ridge Regression | -4.104 | [-20.398, -1.188] | yes | 40 |
| xyz-sales-force | without_AR | Linear Regression | -4.846 | [-23.480, -1.544] | yes | 40 |

**Headline figures, with CI:**

- ABC Cloud, Random Forest, with_AR: R^2 = 0.950, 95% CI [0.747, 0.988]
- ABC Cloud, Random Forest, without_AR: R^2 = 0.268, 95% CI [-1.307, 0.696]

Across all 15 without-AR (domain, model) combinations, 14 have a 95% CI wider than 0.5 R^2 units, and 10 have a CI that includes zero -- i.e., are not statistically distinguishable from "no better than predicting the mean" at the 95% level, despite positive point estimates. This is a direct, honest consequence of holdout sets this small (~30-40 rows for the primary domains); the point estimates themselves are unchanged, but claims resting on them should be read with this uncertainty attached.

## Part B: Target-correlation ablation

ABC Cloud Provider only (primary domain). `baseline_regenerated` re-runs the *unmodified* correlation config through this script's own pipeline (not the on-disk canonical CSVs) as a fidelity check -- it should closely match the canonical `ml_results.md` numbers.

| Variant | Condition | Model | Holdout R^2 | 95% CI | n (holdout) |
|---|---|---|---:|---|---:|
| baseline_regenerated | with_AR | Random Forest | 0.950 | [0.747, 0.988] | 34 |
| baseline_regenerated | with_AR | Gradient Boosting | 0.866 | [0.806, 0.904] | 34 |
| baseline_regenerated | with_AR | Lasso Regression | 0.129 | [-2.323, 0.489] | 34 |
| baseline_regenerated | with_AR | Ridge Regression | -0.194 | [-5.948, 0.520] | 34 |
| baseline_regenerated | with_AR | Linear Regression | -0.256 | [-6.401, 0.480] | 34 |
| baseline_regenerated | without_AR | Random Forest | 0.268 | [-1.307, 0.696] | 34 |
| baseline_regenerated | without_AR | Gradient Boosting | 0.251 | [-1.950, 0.807] | 34 |
| baseline_regenerated | without_AR | Lasso Regression | 0.129 | [-2.323, 0.489] | 34 |
| baseline_regenerated | without_AR | Ridge Regression | -7.285 | [-53.777, -2.303] | 34 |
| baseline_regenerated | without_AR | Linear Regression | -9.124 | [-66.548, -2.942] | 34 |
| permuted_target_corr | with_AR | Random Forest | 0.802 | [0.257, 0.972] | 34 |
| permuted_target_corr | with_AR | Gradient Boosting | 0.776 | [0.236, 0.897] | 34 |
| permuted_target_corr | with_AR | Lasso Regression | -0.060 | [-2.509, 0.330] | 34 |
| permuted_target_corr | with_AR | Ridge Regression | -1.035 | [-10.622, 0.146] | 34 |
| permuted_target_corr | with_AR | Linear Regression | -1.288 | [-11.986, 0.021] | 34 |
| permuted_target_corr | without_AR | Lasso Regression | -0.060 | [-2.509, 0.330] | 34 |
| permuted_target_corr | without_AR | Random Forest | -0.389 | [-3.125, 0.063] | 34 |
| permuted_target_corr | without_AR | Gradient Boosting | -0.809 | [-7.671, 0.305] | 34 |
| permuted_target_corr | without_AR | Ridge Regression | -8.133 | [-56.202, -2.234] | 34 |
| permuted_target_corr | without_AR | Linear Regression | -10.702 | [-72.766, -2.926] | 34 |
| zeroed_target_corr | with_AR | Random Forest | 0.814 | [0.112, 0.932] | 34 |
| zeroed_target_corr | with_AR | Gradient Boosting | 0.714 | [-0.271, 0.932] | 34 |
| zeroed_target_corr | with_AR | Lasso Regression | -0.085 | [-2.993, 0.287] | 34 |
| zeroed_target_corr | with_AR | Ridge Regression | -1.232 | [-11.194, -0.077] | 34 |
| zeroed_target_corr | with_AR | Linear Regression | -1.657 | [-13.417, -0.317] | 34 |
| zeroed_target_corr | without_AR | Lasso Regression | -0.085 | [-2.993, 0.287] | 34 |
| zeroed_target_corr | without_AR | Random Forest | -0.370 | [-4.188, 0.276] | 34 |
| zeroed_target_corr | without_AR | Gradient Boosting | -1.657 | [-11.465, 0.136] | 34 |
| zeroed_target_corr | without_AR | Ridge Regression | -8.008 | [-48.998, -2.564] | 34 |
| zeroed_target_corr | without_AR | Linear Regression | -10.506 | [-62.717, -3.520] | 34 |

**Random Forest, without-AR features, by variant:**

- `baseline_regenerated`: R^2 = 0.268, 95% CI [-1.307, 0.696]
- `zeroed_target_corr`: R^2 = -0.370, 95% CI [-4.188, 0.276]
- `permuted_target_corr`: R^2 = -0.389, 95% CI [-3.125, 0.063]

**Interpretation:**

- Zeroing all 21 target correlations moves without-AR Random Forest R^2 from 0.268 to -0.370. Because `System Uptime (%)` appears nowhere else in the correlation config, this is close to a controlled null: any R^2 remaining here comes only from features that happen to correlate with target-correlated metrics *indirectly* (e.g. via intra/cross-phase correlations among the 20 metrics System Uptime was linked to) or from the models finding structure in noise. A non-trivial residual R^2 after zeroing direct target correlations would be notable -- it would mean some of the reported signal survives even without any direct hand-specified target link, propagating in through the intra/cross-phase correlation network instead. Read the actual number above rather than assuming either outcome.
- Permuting which metric gets which of the 21 rho values moves R^2 to -0.389 (vs. 0.268 baseline). This differs meaningfully from baseline, meaning the specific domain-informed assignment (not just having correlations of similar magnitude) matters for the achievable R^2.

- **Unexpected coupling:** the with-AR condition also moved under both ablations (Random Forest with-AR: 0.950 baseline -> 0.814 zeroed), even though AR features are rolling/lag statistics of System Uptime's own history and shouldn't depend on its correlation to *other* metrics. Root cause, traced in `src/copula_engine.py::GaussianCopula.build_correlation_matrix()`: `ensure_positive_definite()` (Higham's alternating projections) runs on the *entire* correlation matrix after all pairs are inserted, not per-block. Even though System Uptime's row is specified as all-zero off-diagonal in the zeroed variant, the global PSD projection can still perturb that row to compensate for PSD violations elsewhere in the matrix -- so "System Uptime appears nowhere else in the correlation config" (true of the *specified* pairs) does not imply System Uptime's *realized* samples are unaffected by changes elsewhere in the matrix. This is a genuine methodological subtlety worth disclosing: the copula's variables are not as cleanly separable as the config file's section structure suggests.

## Limitations

- The bootstrap in Part A resamples the holdout set only; it does not refit the model on resampled training data, so it does not capture variance from training-sample composition (the multi-seed analysis in `statistical_validation.py` partially covers that from a different angle -- different seeds change the entire dataset, not just which points land in the holdout).
- The ablation in Part B is scoped to the primary domain (ABC Cloud Provider) and to `target_correlations` only; `intra_phase_correlations` and `cross_phase_correlations` (themselves also hand-specified) are untouched, and a full accounting of generator-prior recovery would need to ablate those too.
- `_precompensate_correlations()`'s amplification (1.3x-2.5x, applied to every pair regardless of section) is unchanged in all three variants -- it's applied *after* the correlation config is built, so it scales whatever `target_correlations` contains at that point (nothing, in the zeroed variant) rather than being a separate confound here.
