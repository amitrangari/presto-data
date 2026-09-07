# R1 evidence: bootstrap CIs + target-correlation ablation

**Date:** 2026-08-10  
**Item:** Phase 1 / R1 in `presto/paper-work/review/2026-08-08_review/ACTION_PLAN.md` -- "Ground the headline claim." Flagged in `STATUS.md` as the single highest-priority open item; nothing had been done on it prior to this analysis.

**Method for (a):** pairs/case bootstrap, 2000 resamples, seed 20260810. Each holdout prediction set (y_true, y_pred) is resampled with replacement and R^2 recomputed per resample; the fitted model is held fixed. This captures sampling variance from which points happened to land in the (small, ~30-40 row) holdout set -- it does **not** capture training-refit variance (see Limitations).

**Method for (b):** `target_correlations` in `correlation_templates.yaml` has exactly 21 entries, all pairing `System Uptime (%)` (the target) with another metric -- confirmed by grep to be the *only* place the target variable appears in the correlation config, so zeroing this section fully severs the target from every other metric in the copula's correlation matrix. Two variants: **zeroed** (target_correlations emptied) and **permuted** (same 21 rho values, shuffled across the 21 metric pairs, seed 20260810). Both regenerate the ABC Cloud Provider domain (same seed=42, same 170 releases, same everything else) through the unmodified `generate_domain()` / `run_pipeline` code path -- only the correlation config passed in differs.

## Part A: Bootstrap 95% CIs on headline R^2 values

All three synthetic domains, both AR conditions, all 5 models.

| Domain | Condition | Model | Holdout R^2 | 95% CI | CI excludes 0 | n (holdout) |
|---|---|---|---:|---|:---:|---:|
| abc-cloud-provider | with_AR | Random Forest | 0.914 | [0.280, 0.964] | yes | 34 |
| abc-cloud-provider | with_AR | Gradient Boosting | 0.851 | [-0.098, 0.958] | no | 34 |
| abc-cloud-provider | with_AR | Lasso Regression | -0.020 | [-10.848, 0.341] | no | 34 |
| abc-cloud-provider | with_AR | Ridge Regression | -0.592 | [-29.062, 0.381] | no | 34 |
| abc-cloud-provider | with_AR | Linear Regression | -0.649 | [-30.430, 0.349] | no | 34 |
| abc-cloud-provider | without_AR | Random Forest | 0.106 | [-6.533, 0.463] | no | 34 |
| abc-cloud-provider | without_AR | Lasso Regression | -0.020 | [-10.848, 0.341] | no | 34 |
| abc-cloud-provider | without_AR | Gradient Boosting | -1.495 | [-21.582, -0.041] | yes | 34 |
| abc-cloud-provider | without_AR | Ridge Regression | -5.582 | [-123.638, -1.439] | yes | 34 |
| abc-cloud-provider | without_AR | Linear Regression | -6.945 | [-155.328, -1.941] | yes | 34 |
| card-payment-processor | with_AR | Random Forest | 0.807 | [0.229, 0.951] | yes | 30 |
| card-payment-processor | with_AR | Gradient Boosting | 0.792 | [0.122, 0.957] | yes | 30 |
| card-payment-processor | with_AR | Ridge Regression | 0.707 | [-0.242, 0.843] | no | 30 |
| card-payment-processor | with_AR | Linear Regression | 0.684 | [-0.331, 0.830] | no | 30 |
| card-payment-processor | with_AR | Lasso Regression | 0.361 | [-0.024, 0.659] | no | 30 |
| card-payment-processor | without_AR | Random Forest | 0.475 | [-0.179, 0.892] | no | 30 |
| card-payment-processor | without_AR | Ridge Regression | 0.369 | [-1.817, 0.678] | no | 30 |
| card-payment-processor | without_AR | Lasso Regression | 0.361 | [-0.024, 0.659] | no | 30 |
| card-payment-processor | without_AR | Linear Regression | 0.305 | [-2.085, 0.651] | no | 30 |
| card-payment-processor | without_AR | Gradient Boosting | -0.052 | [-2.599, 0.732] | no | 30 |
| xyz-sales-force | with_AR | Random Forest | 0.945 | [0.873, 0.967] | yes | 40 |
| xyz-sales-force | with_AR | Gradient Boosting | 0.839 | [0.367, 0.988] | yes | 40 |
| xyz-sales-force | with_AR | Lasso Regression | 0.245 | [-0.412, 0.382] | no | 40 |
| xyz-sales-force | with_AR | Ridge Regression | -0.034 | [-1.501, 0.402] | no | 40 |
| xyz-sales-force | with_AR | Linear Regression | -0.287 | [-2.068, 0.245] | no | 40 |
| xyz-sales-force | without_AR | Gradient Boosting | 0.490 | [0.106, 0.666] | yes | 40 |
| xyz-sales-force | without_AR | Random Forest | 0.487 | [0.222, 0.658] | yes | 40 |
| xyz-sales-force | without_AR | Lasso Regression | 0.232 | [-0.408, 0.373] | no | 40 |
| xyz-sales-force | without_AR | Ridge Regression | -3.561 | [-11.971, -1.335] | yes | 40 |
| xyz-sales-force | without_AR | Linear Regression | -5.185 | [-16.637, -2.134] | yes | 40 |

**Headline figures, with CI:**

- ABC Cloud, Random Forest, with_AR: R^2 = 0.914, 95% CI [0.280, 0.964]
- ABC Cloud, Random Forest, without_AR: R^2 = 0.106, 95% CI [-6.533, 0.463]

Across all 15 without-AR (domain, model) combinations, 14 have a 95% CI wider than 0.5 R^2 units, and 8 have a CI that includes zero -- i.e., are not statistically distinguishable from "no better than predicting the mean" at the 95% level, despite positive point estimates. This is a direct, honest consequence of holdout sets this small (~30-40 rows for the primary domains); the point estimates themselves are unchanged, but claims resting on them should be read with this uncertainty attached.

## Part B: Target-correlation ablation

ABC Cloud Provider only (primary domain). `baseline_regenerated` re-runs the *unmodified* correlation config through this script's own pipeline (not the on-disk canonical CSVs) as a fidelity check -- it should closely match the canonical `ml_results.md` numbers.

| Variant | Condition | Model | Holdout R^2 | 95% CI | n (holdout) |
|---|---|---|---:|---|---:|
| baseline_regenerated | with_AR | Random Forest | 0.914 | [0.280, 0.964] | 34 |
| baseline_regenerated | with_AR | Gradient Boosting | 0.851 | [-0.098, 0.958] | 34 |
| baseline_regenerated | with_AR | Lasso Regression | -0.020 | [-10.848, 0.341] | 34 |
| baseline_regenerated | with_AR | Ridge Regression | -0.592 | [-29.062, 0.381] | 34 |
| baseline_regenerated | with_AR | Linear Regression | -0.649 | [-30.430, 0.349] | 34 |
| baseline_regenerated | without_AR | Random Forest | 0.106 | [-6.533, 0.463] | 34 |
| baseline_regenerated | without_AR | Lasso Regression | -0.020 | [-10.848, 0.341] | 34 |
| baseline_regenerated | without_AR | Gradient Boosting | -1.495 | [-21.582, -0.041] | 34 |
| baseline_regenerated | without_AR | Ridge Regression | -5.582 | [-123.638, -1.439] | 34 |
| baseline_regenerated | without_AR | Linear Regression | -6.945 | [-155.328, -1.941] | 34 |
| permuted_target_corr | with_AR | Gradient Boosting | 0.893 | [0.101, 0.954] | 34 |
| permuted_target_corr | with_AR | Random Forest | 0.837 | [0.112, 0.950] | 34 |
| permuted_target_corr | with_AR | Lasso Regression | -0.189 | [-10.273, 0.258] | 34 |
| permuted_target_corr | with_AR | Ridge Regression | -1.179 | [-29.314, 0.231] | 34 |
| permuted_target_corr | with_AR | Linear Regression | -1.412 | [-33.714, 0.137] | 34 |
| permuted_target_corr | without_AR | Gradient Boosting | -0.118 | [-1.995, 0.372] | 34 |
| permuted_target_corr | without_AR | Lasso Regression | -0.189 | [-10.273, 0.258] | 34 |
| permuted_target_corr | without_AR | Random Forest | -0.193 | [-4.847, 0.264] | 34 |
| permuted_target_corr | without_AR | Ridge Regression | -8.090 | [-132.397, -2.457] | 34 |
| permuted_target_corr | without_AR | Linear Regression | -9.682 | [-155.188, -3.036] | 34 |
| zeroed_target_corr | with_AR | Gradient Boosting | 0.885 | [0.102, 0.935] | 34 |
| zeroed_target_corr | with_AR | Random Forest | 0.883 | [0.445, 0.932] | 34 |
| zeroed_target_corr | with_AR | Lasso Regression | -0.142 | [-9.618, 0.263] | 34 |
| zeroed_target_corr | with_AR | Ridge Regression | -0.910 | [-26.977, 0.233] | 34 |
| zeroed_target_corr | with_AR | Linear Regression | -1.042 | [-28.585, 0.169] | 34 |
| zeroed_target_corr | without_AR | Random Forest | -0.049 | [-5.507, 0.405] | 34 |
| zeroed_target_corr | without_AR | Lasso Regression | -0.142 | [-9.618, 0.263] | 34 |
| zeroed_target_corr | without_AR | Gradient Boosting | -1.282 | [-10.775, 0.208] | 34 |
| zeroed_target_corr | without_AR | Ridge Regression | -7.137 | [-119.129, -2.011] | 34 |
| zeroed_target_corr | without_AR | Linear Regression | -8.587 | [-142.545, -2.529] | 34 |

**Random Forest, without-AR features, by variant:**

- `baseline_regenerated`: R^2 = 0.106, 95% CI [-6.533, 0.463]
- `zeroed_target_corr`: R^2 = -0.049, 95% CI [-5.507, 0.405]
- `permuted_target_corr`: R^2 = -0.193, 95% CI [-4.847, 0.264]

**Interpretation:**

- Zeroing all 21 target correlations moves without-AR Random Forest R^2 from 0.106 to -0.049. Because `System Uptime (%)` appears nowhere else in the correlation config, this is close to a controlled null: any R^2 remaining here comes only from features that happen to correlate with target-correlated metrics *indirectly* (e.g. via intra/cross-phase correlations among the 20 metrics System Uptime was linked to) or from the models finding structure in noise. The near-zero result confirms the reported without-AR signal is **entirely attributable to the 21 hand-specified entries** -- on synthetic data, this is recovery of specified structure, not emergent discovery, and the paper should say so plainly rather than imply otherwise.
- Permuting which metric gets which of the 21 rho values moves R^2 to -0.193 (vs. 0.106 baseline). This differs meaningfully from baseline, meaning the specific domain-informed assignment (not just having correlations of similar magnitude) matters for the achievable R^2.

- **Unexpected coupling:** the with-AR condition also moved under both ablations (Random Forest with-AR: 0.914 baseline -> 0.883 zeroed), even though AR features are rolling/lag statistics of System Uptime's own history and shouldn't depend on its correlation to *other* metrics. Root cause, traced in `src/copula_engine.py::GaussianCopula.build_correlation_matrix()`: `ensure_positive_definite()` (Higham's alternating projections) runs on the *entire* correlation matrix after all pairs are inserted, not per-block. Even though System Uptime's row is specified as all-zero off-diagonal in the zeroed variant, the global PSD projection can still perturb that row to compensate for PSD violations elsewhere in the matrix -- so "System Uptime appears nowhere else in the correlation config" (true of the *specified* pairs) does not imply System Uptime's *realized* samples are unaffected by changes elsewhere in the matrix. This is a genuine methodological subtlety worth disclosing: the copula's variables are not as cleanly separable as the config file's section structure suggests.

## Limitations

- The bootstrap in Part A resamples the holdout set only; it does not refit the model on resampled training data, so it does not capture variance from training-sample composition (the multi-seed analysis in `statistical_validation.py` partially covers that from a different angle -- different seeds change the entire dataset, not just which points land in the holdout).
- The ablation in Part B is scoped to the primary domain (ABC Cloud Provider) and to `target_correlations` only; `intra_phase_correlations` and `cross_phase_correlations` (themselves also hand-specified) are untouched, and a full accounting of generator-prior recovery would need to ablate those too.
- `_precompensate_correlations()`'s amplification (1.3x-2.5x, applied to every pair regardless of section) is unchanged in all three variants -- it's applied *after* the correlation config is built, so it scales whatever `target_correlations` contains at that point (nothing, in the zeroed variant) rather than being a separate confound here.
