# M12 — AR-Feature ACF Diagnostics and Algebraic-Recoverability Audit

Addresses Reviewer 2's round-3 request to reconcile System Uptime's weak realized lag-1 autocorrelation with the paper's ~88% AR-persistence claim, and to audit the 32 target-derived (AR) features for algebraic recoverability of the current target, the same check already applied to Perfherder and TravisTorrent.

## Part A: Target's own lag-1 ACF vs. AR-derived feature correlations

| Domain | Target lag-1 ACF |
|---|---:|
| abc-cloud-provider | 0.0309 |
| card-payment-processor | -0.0510 |
| xyz-sales-force | -0.0281 |

Per-feature detail (lag-1 autocorrelation of the feature itself, and its Pearson correlation with the CURRENT-row target) for all 32 AR-derived features, all 3 domains:

| Domain | Family | Feature | Feature's own lag-1 ACF | Corr. with current target |
|---|---|---|---:|---:|
| abc-cloud-provider | diff | System Uptime (%)_diff_1 | -0.338 | 0.510 |
| abc-cloud-provider | diff | System Uptime (%)_diff_2 | 0.190 | 0.526 |
| abc-cloud-provider | diff | System Uptime (%)_diff_3 | 0.198 | 0.545 |
| abc-cloud-provider | diff | System Uptime (%)_diff_5 | 0.079 | 0.592 |
| abc-cloud-provider | lag | System Uptime (%)_lag_1 | 0.143 | 0.144 |
| abc-cloud-provider | lag | System Uptime (%)_lag_2 | 0.231 | 0.075 |
| abc-cloud-provider | lag | System Uptime (%)_lag_3 | 0.302 | 0.006 |
| abc-cloud-provider | lag | System Uptime (%)_lag_5 | 0.409 | 0.150 |
| abc-cloud-provider | pct_change | System Uptime (%)_pct_change_1 | -0.327 | 0.487 |
| abc-cloud-provider | pct_change | System Uptime (%)_pct_change_2 | 0.198 | 0.502 |
| abc-cloud-provider | pct_change | System Uptime (%)_pct_change_3 | 0.208 | 0.522 |
| abc-cloud-provider | pct_change | System Uptime (%)_pct_change_5 | 0.075 | 0.575 |
| abc-cloud-provider | rolling | System Uptime (%)_rolling_cv_10 | 0.964 | -0.217 |
| abc-cloud-provider | rolling | System Uptime (%)_rolling_cv_3 | 0.643 | -0.028 |
| abc-cloud-provider | rolling | System Uptime (%)_rolling_cv_5 | 0.854 | -0.128 |
| abc-cloud-provider | rolling | System Uptime (%)_rolling_cv_7 | 0.876 | -0.069 |
| abc-cloud-provider | rolling | System Uptime (%)_rolling_max_10 | 0.705 | 0.231 |
| abc-cloud-provider | rolling | System Uptime (%)_rolling_max_3 | 0.608 | 0.212 |
| abc-cloud-provider | rolling | System Uptime (%)_rolling_max_5 | 0.705 | 0.231 |
| abc-cloud-provider | rolling | System Uptime (%)_rolling_max_7 | 0.705 | 0.231 |
| abc-cloud-provider | rolling | System Uptime (%)_rolling_mean_10 | 0.925 | 0.230 |
| abc-cloud-provider | rolling | System Uptime (%)_rolling_mean_3 | 0.748 | 0.108 |
| abc-cloud-provider | rolling | System Uptime (%)_rolling_mean_5 | 0.875 | 0.176 |
| abc-cloud-provider | rolling | System Uptime (%)_rolling_mean_7 | 0.895 | 0.142 |
| abc-cloud-provider | rolling | System Uptime (%)_rolling_min_10 | 0.956 | 0.204 |
| abc-cloud-provider | rolling | System Uptime (%)_rolling_min_3 | 0.638 | 0.006 |
| abc-cloud-provider | rolling | System Uptime (%)_rolling_min_5 | 0.830 | 0.102 |
| abc-cloud-provider | rolling | System Uptime (%)_rolling_min_7 | 0.835 | 0.027 |
| abc-cloud-provider | rolling | System Uptime (%)_rolling_std_10 | 0.964 | -0.217 |
| abc-cloud-provider | rolling | System Uptime (%)_rolling_std_3 | 0.640 | -0.026 |
| abc-cloud-provider | rolling | System Uptime (%)_rolling_std_5 | 0.852 | -0.127 |
| abc-cloud-provider | rolling | System Uptime (%)_rolling_std_7 | 0.874 | -0.067 |
| card-payment-processor | diff | System Uptime (%)_diff_1 | -0.419 | 0.550 |
| card-payment-processor | diff | System Uptime (%)_diff_2 | 0.099 | 0.500 |
| card-payment-processor | diff | System Uptime (%)_diff_3 | -0.009 | 0.610 |
| card-payment-processor | diff | System Uptime (%)_diff_5 | 0.285 | 0.371 |
| card-payment-processor | lag | System Uptime (%)_lag_1 | 0.071 | 0.072 |
| card-payment-processor | lag | System Uptime (%)_lag_2 | 0.166 | 0.120 |
| card-payment-processor | lag | System Uptime (%)_lag_3 | 0.242 | 0.125 |
| card-payment-processor | lag | System Uptime (%)_lag_5 | 0.365 | 0.143 |
| card-payment-processor | pct_change | System Uptime (%)_pct_change_1 | -0.403 | 0.523 |
| card-payment-processor | pct_change | System Uptime (%)_pct_change_2 | 0.112 | 0.473 |
| card-payment-processor | pct_change | System Uptime (%)_pct_change_3 | -0.008 | 0.591 |
| card-payment-processor | pct_change | System Uptime (%)_pct_change_5 | 0.311 | 0.341 |
| card-payment-processor | rolling | System Uptime (%)_rolling_cv_10 | 0.894 | -0.055 |
| card-payment-processor | rolling | System Uptime (%)_rolling_cv_3 | 0.706 | -0.125 |
| card-payment-processor | rolling | System Uptime (%)_rolling_cv_5 | 0.833 | -0.102 |
| card-payment-processor | rolling | System Uptime (%)_rolling_cv_7 | 0.870 | -0.076 |
| card-payment-processor | rolling | System Uptime (%)_rolling_max_10 | 0.745 | 0.241 |
| card-payment-processor | rolling | System Uptime (%)_rolling_max_3 | 0.743 | 0.239 |
| card-payment-processor | rolling | System Uptime (%)_rolling_max_5 | 0.745 | 0.241 |
| card-payment-processor | rolling | System Uptime (%)_rolling_max_7 | 0.745 | 0.241 |
| card-payment-processor | rolling | System Uptime (%)_rolling_mean_10 | 0.927 | 0.181 |
| card-payment-processor | rolling | System Uptime (%)_rolling_mean_3 | 0.769 | 0.161 |
| card-payment-processor | rolling | System Uptime (%)_rolling_mean_5 | 0.870 | 0.159 |
| card-payment-processor | rolling | System Uptime (%)_rolling_mean_7 | 0.905 | 0.174 |
| card-payment-processor | rolling | System Uptime (%)_rolling_min_10 | 0.808 | -0.069 |
| card-payment-processor | rolling | System Uptime (%)_rolling_min_3 | 0.691 | 0.109 |
| card-payment-processor | rolling | System Uptime (%)_rolling_min_5 | 0.794 | 0.066 |
| card-payment-processor | rolling | System Uptime (%)_rolling_min_7 | 0.814 | 0.008 |
| card-payment-processor | rolling | System Uptime (%)_rolling_std_10 | 0.889 | -0.048 |
| card-payment-processor | rolling | System Uptime (%)_rolling_std_3 | 0.701 | -0.123 |
| card-payment-processor | rolling | System Uptime (%)_rolling_std_5 | 0.830 | -0.100 |
| card-payment-processor | rolling | System Uptime (%)_rolling_std_7 | 0.865 | -0.071 |
| xyz-sales-force | diff | System Uptime (%)_diff_1 | -0.490 | 0.617 |
| xyz-sales-force | diff | System Uptime (%)_diff_2 | -0.013 | 0.634 |
| xyz-sales-force | diff | System Uptime (%)_diff_3 | 0.082 | 0.500 |
| xyz-sales-force | diff | System Uptime (%)_diff_5 | 0.099 | 0.510 |
| xyz-sales-force | lag | System Uptime (%)_lag_1 | 0.037 | 0.038 |
| xyz-sales-force | lag | System Uptime (%)_lag_2 | 0.095 | 0.148 |
| xyz-sales-force | lag | System Uptime (%)_lag_3 | 0.149 | 0.116 |
| xyz-sales-force | lag | System Uptime (%)_lag_5 | 0.232 | 0.064 |
| xyz-sales-force | pct_change | System Uptime (%)_pct_change_1 | -0.482 | 0.597 |
| xyz-sales-force | pct_change | System Uptime (%)_pct_change_2 | -0.010 | 0.619 |
| xyz-sales-force | pct_change | System Uptime (%)_pct_change_3 | 0.094 | 0.477 |
| xyz-sales-force | pct_change | System Uptime (%)_pct_change_5 | 0.113 | 0.488 |
| xyz-sales-force | rolling | System Uptime (%)_rolling_cv_10 | 0.915 | -0.111 |
| xyz-sales-force | rolling | System Uptime (%)_rolling_cv_3 | 0.692 | -0.124 |
| xyz-sales-force | rolling | System Uptime (%)_rolling_cv_5 | 0.838 | -0.142 |
| xyz-sales-force | rolling | System Uptime (%)_rolling_cv_7 | 0.893 | -0.140 |
| xyz-sales-force | rolling | System Uptime (%)_rolling_max_10 | 0.705 | 0.158 |
| xyz-sales-force | rolling | System Uptime (%)_rolling_max_3 | 0.703 | 0.159 |
| xyz-sales-force | rolling | System Uptime (%)_rolling_max_5 | 0.704 | 0.157 |
| xyz-sales-force | rolling | System Uptime (%)_rolling_max_7 | 0.705 | 0.159 |
| xyz-sales-force | rolling | System Uptime (%)_rolling_mean_10 | 0.921 | 0.143 |
| xyz-sales-force | rolling | System Uptime (%)_rolling_mean_3 | 0.742 | 0.138 |
| xyz-sales-force | rolling | System Uptime (%)_rolling_mean_5 | 0.854 | 0.142 |
| xyz-sales-force | rolling | System Uptime (%)_rolling_mean_7 | 0.895 | 0.159 |
| xyz-sales-force | rolling | System Uptime (%)_rolling_min_10 | 0.851 | 0.018 |
| xyz-sales-force | rolling | System Uptime (%)_rolling_min_3 | 0.677 | 0.093 |
| xyz-sales-force | rolling | System Uptime (%)_rolling_min_5 | 0.801 | 0.094 |
| xyz-sales-force | rolling | System Uptime (%)_rolling_min_7 | 0.852 | 0.082 |
| xyz-sales-force | rolling | System Uptime (%)_rolling_std_10 | 0.912 | -0.109 |
| xyz-sales-force | rolling | System Uptime (%)_rolling_std_3 | 0.687 | -0.123 |
| xyz-sales-force | rolling | System Uptime (%)_rolling_std_5 | 0.834 | -0.141 |
| xyz-sales-force | rolling | System Uptime (%)_rolling_std_7 | 0.890 | -0.138 |

## Part B: Algebraic-recoverability audit (diff_k / pct_change_k)

`add_lag_features()` computes `diff_k = df[metric] - df[metric].shift(k)` and `pct_change_k = df[metric].pct_change(k)` directly on the CURRENT, unshifted target column (only `lag_k = df[metric].shift(k)` is a pure, correctly-shifted prior value). Algebraically this means `target_t = diff_k + lag_k` and `target_t = lag_k * (1 + pct_change_k)` EXACTLY, for every row where all three terms are defined (i.e. every row except the first `k` rows of each domain, which are NaN-filled by `engineer_features()`'s ffill/bfill/mean-fill step and so do not satisfy the identity). This is tested directly below, not assumed:

| Domain | Lag | n rows | diff_k+lag_k == target (exact rows) | lag_k*(1+pct_change_k) == target (exact rows) |
|---|---:|---:|---|---|
| abc-cloud-provider | 1 | 170 | 169/170 (99.4%) | 169/170 (99.4%) |
| abc-cloud-provider | 2 | 170 | 169/170 (99.4%) | 169/170 (99.4%) |
| abc-cloud-provider | 3 | 170 | 169/170 (99.4%) | 169/170 (99.4%) |
| abc-cloud-provider | 5 | 170 | 165/170 (97.1%) | 165/170 (97.1%) |
| card-payment-processor | 1 | 150 | 149/150 (99.3%) | 149/150 (99.3%) |
| card-payment-processor | 2 | 150 | 148/150 (98.7%) | 148/150 (98.7%) |
| card-payment-processor | 3 | 150 | 147/150 (98.0%) | 147/150 (98.0%) |
| card-payment-processor | 5 | 150 | 147/150 (98.0%) | 147/150 (98.0%) |
| xyz-sales-force | 1 | 200 | 199/200 (99.5%) | 199/200 (99.5%) |
| xyz-sales-force | 2 | 200 | 199/200 (99.5%) | 199/200 (99.5%) |
| xyz-sales-force | 3 | 200 | 198/200 (99.0%) | 198/200 (99.0%) |
| xyz-sales-force | 5 | 200 | 198/200 (99.0%) | 198/200 (99.0%) |

**Finding: this identity holds essentially exactly (99%+ of rows; the only exceptions are the handful of originally-NaN first rows each lag step fills), in all 3 domains, at all 4 lag steps.** `diff_k` and `pct_change_k` are therefore same-row target leakage in the same sense as the already-fixed rolling-window bug (`R2_LAG_SHIFT_FIX_EVIDENCE.md`) and the already-documented Perfherder/TravisTorrent additive-identity cases -- a model given `lag_k` (legitimate) and `diff_k` or `pct_change_k` (both derived from the CURRENT row's own target) can reconstruct `target_t` algebraically, not merely predict it. **This directly contradicts the paper's current Section 4.1.1 statement that all 12 lag/diff/pct-change features "were already correctly shifted": `lag_k` was; `diff_k` and `pct_change_k` (8 of the 12) were not.** Only `rolling_*` (20 features, computed on a pre-shifted copy per `add_rolling_features`'s own docstring) and `lag_k` (4 features) are genuinely prior-period; `diff_k` and `pct_change_k` (8 features) are not.

## Part C: Ablation — how much of the with-AR R² gain is this identity?

Random Forest holdout R², same 80/20 split as everywhere else in this paper, comparing the existing without-AR baseline (0 AR features) against with-AR using only the 24 features NOT implicated above (20 `rolling_*` + 4 `lag_k`) against the existing full with-AR condition (all 32 features, including the 8 implicated `diff_k`/`pct_change_k`).

| Domain | Without-AR R² | With-AR minus identity-implicated (24 feat.) R² | With-AR full (32 feat.) R² | Gain, full | Gain, minus-identity | % of full gain from implicated features |
|---|---:|---:|---:|---:|---:|---:|
| abc-cloud-provider | 0.1065 | 0.1243 | 0.9141 | +0.8076 | +0.0179 | 97.8% |
| card-payment-processor | 0.4752 | 0.4615 | 0.8073 | +0.3321 | -0.0137 | 104.1% |
| xyz-sales-force | 0.4872 | 0.4766 | 0.9448 | +0.4575 | -0.0107 | 102.3% |

**Reconciliation of the ~88% AR-persistence claim (primary domain).** Removing just the 8 identity-implicated features (of 32 AR features total) changes the with-AR holdout R² from 0.9141 to 0.1243 against a without-AR baseline of 0.1065 -- i.e. 97.8% of the full with-AR gain over the without-AR baseline is attributable to features that are algebraically, not just statistically, tied to the current-row target. This resolves the apparent puzzle Reviewer 2 raised (weak 0.031 raw target ACF vs. large 88% AR-attributed gain): a meaningful share of that gain was never persistence in the ACF sense at all, it was two features whose sum/product exactly reconstructs the target. The genuinely-autoregressive remainder (rolling_* and lag_k features, still capturing real if weaker persistence, consistent with the low raw target ACF) accounts for the rest of the gain, which is smaller than the paper's current 88% figure implies.

**Recommended fix, not implemented by this script:** `add_lag_features()` should compute `diff_k`/`pct_change_k` against the SAME pre-shifted series `add_rolling_features` already uses (`df_out[metric].shift(1)`), not against the raw, current-row `df_out[metric]`, so that `diff_k` becomes `target_{t-1} - target_{t-1-k}` (a genuinely prior-period quantity) rather than `target_t - target_{t-k}`. This is a generator/feature-engineering code fix with the same shape as the already-fixed R2 rolling-window bug, affects all three synthetic domains and any real-data adapter reusing `add_lag_features`, and should be scoped and applied before the with-AR headline number is finalized for v4, not papered over by excluding the two families post hoc.
