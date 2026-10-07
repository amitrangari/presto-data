# GHALogs mean_n_steps Ablation (PRESTO v4 revision)

**Reviewer comment addressed:** MDPI round-3 review, Reviewer 2: "the most influential feature is mean_n_steps, accounting for approximately 48.6% of Random Forest importance, ... largely definitional ... analogous to the circularity problem subsequently identified for TravisTorrent."

**Method.** Identical pipeline to `real-data/ghalogs/run_pipeline_ghalogs.py` (chronological 80/20 split, TimeSeriesSplit(5) CV, StandardScaler fit on train only, same 5 models), with `mean_n_steps` removed from the feature matrix before fitting. A pairs/case bootstrap 95% CI (2000 resamples, seed 20260919) was added, matching the procedure already used in `bootstrap_real_world_ci.py` for the full-feature GHALogs result, so the two tables are directly comparable.

Full feature set: 23 features. Ablated: 22 (dropped: mean_n_steps). n=28443 repositories (unchanged from the full-feature result).

## Ablated Model Performance (mean_n_steps excluded)

| Model | CV R2 (mean +/- std) | Holdout R2 | 95% Bootstrap CI | Significant? | MAE | RMSE |
|---|---|---|---|:---:|---|---|
| Lasso Regression | -0.0182 +/- 0.0513 | 0.0069 | [-0.0024, 0.0401] | no | 1673.70 | 7229.76 |
| Ridge Regression | -0.0261 +/- 0.0631 | 0.0068 | [-0.0025, 0.0399] | no | 1674.14 | 7230.04 |
| Linear Regression | -0.0270 +/- 0.0641 | 0.0068 | [-0.0025, 0.0399] | no | 1674.15 | 7230.05 |
| Random Forest | -0.0871 +/- 0.0820 | -0.0440 | [-0.2944, 0.0115] | no | 1815.27 | 7412.62 |
| Gradient Boosting | -0.3499 +/- 0.2060 | -0.0685 | [-0.4039, 0.0005] | no | 1822.66 | 7499.26 |

## Full-Feature Result, For Comparison (from output_ghalogs_ml_results.md)

| Model | Holdout R2 | 95% Bootstrap CI (paper Table, Sec 4.2.3) |
|---|---|---|
| Gradient Boosting | 0.1130 | [0.050, 0.356] |
| Lasso Regression | 0.1000 | [0.062, 0.267] |
| Ridge Regression | 0.1000 | [0.062, 0.267] |
| Linear Regression | 0.1000 | [0.062, 0.267] |
| Random Forest | 0.0960 | [0.021, 0.299] |

## Top 15 Feature Importances After Ablation (Random Forest)

| Rank | Feature | Importance |
|---|---|---|
| 1 | commentLines | 0.1166 |
| 2 | totalPullRequests | 0.0954 |
| 3 | repo_age_days | 0.0831 |
| 4 | success_rate | 0.0734 |
| 5 | size | 0.0693 |
| 6 | blankLines | 0.0566 |
| 7 | commits | 0.0529 |
| 8 | branches | 0.0508 |
| 9 | codeLines | 0.0500 |
| 10 | comment_density | 0.0458 |
| 11 | releases | 0.0441 |
| 12 | pr_resolution_rate | 0.0416 |
| 13 | stargazers | 0.0359 |
| 14 | issue_resolution_rate | 0.0323 |
| 15 | openIssues | 0.0312 |

## Interpretation

With `mean_n_steps` removed, the best model's holdout R2 is 0.0069 (Lasso Regression), versus 0.1000-0.1130 in the full-feature result, and **none of the five models' 95% bootstrap CIs exclude zero** (the two closest, Lasso/Ridge at [-0.0024, 0.0401] and [-0.0025, 0.0399], still straddle zero; Random Forest and Gradient Boosting are now point-estimate negative). GHALogs' significance claim does **not** survive removing the definitionally-circular feature: this is the same fate as the TravisTorrent robustness check (Section 4.2.1), where excluding `tr_log_testduration` also collapsed every project's holdout R2 to negative. The paper's Section 4.2.3 "cleanest real-data test of PRESTO's headline claim" framing and the "significant for all five models" claim (repeated in the Abstract) must be revised: GHALogs' full-feature result was itself substantially carried by a near-tautological feature, not independent process/popularity signal as previously characterized. The remaining ~51-54% of importance (commentLines, totalPullRequests, repo_age_days, success_rate, size, etc.) does not, on its own, produce a statistically significant holdout result. This changes GHALogs from "zero-leakage, clean confirmatory evidence" to "directionally suggestive but not independently significant once the duration-adjacent feature is removed" -- structurally the same downgrade already applied to TravisTorrent, and it means the paper's "SDLC/process signals carry genuine, transferable predictive value" claim now rests more heavily on SQuaD's CVE-count result (Section 4.2.3.1), which has no analogous circularity concern (CVE count is not arithmetically related to any process-metric feature the way workflow duration is to step count).
