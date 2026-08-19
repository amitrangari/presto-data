# TravisTorrent Feature Importance (Permutation, Winning Model Per Project)

Closes the gap flagged in STATUS.md's R7 row: the reimplemented adapter (`run_pipeline_travistorrent.py`) reports per-model R2/MAE/RMSE only. This script adds permutation importance (n_repeats=10, on the holdout test set) for each project's own winning model, so the original submission's "repository age is the most consistently predictive feature" claim can be checked directly against the reimplemented pipeline.

| Project | Best Model | Holdout R² | Top feature (perm. importance) | `gh_repo_age` rank |
|---|---|---:|---|---|
| DataDog/dd-agent | Gradient Boosting | 0.0179 | gh_team_size (37.7%) | #132 (-0.1%) |
| bundler/bundler | Random Forest | -0.1514 | tr_log_testduration_rolling_min_10 (20.0%) | #20 (0.0%) |
| getsentry/sentry | Gradient Boosting | 0.0497 | tr_log_testduration (6.0%) | #18 (0.2%) |
| gonum/matrix | Random Forest | 0.0052 | tr_log_num_tests_run (10.6%) | #90 (0.0%) |
| mongodb/mongoid | Gradient Boosting | -0.0396 | gh_repo_num_commits (0.2%) | #2 (0.2%) |
| rg3/youtube-dl | Linear Regression | 0.4753 | tr_log_testduration (503100.9%) | #31 (2.1%) |
| rspec/rspec-core | Random Forest | -0.2936 | gh_asserts_cases_per_kloc (18.4%) | #7 (0.5%) |

`gh_repo_age` is the #1 feature in 0/7 projects, and top-5 in 1/7 projects.

## Top 5 features per project

### DataDog/dd-agent (Gradient Boosting, R²=0.0179)

| Rank | Feature | Importance |
|---:|---|---:|
| 1 | gh_team_size | 37.69% |
| 2 | tr_log_bool_tests_ran | 10.89% |
| 3 | gh_test_lines_per_kloc | 5.54% |
| 4 | gh_test_cases_per_kloc | 4.93% |
| 5 | gh_asserts_cases_per_kloc | 4.49% |

### bundler/bundler (Random Forest, R²=-0.1514)

| Rank | Feature | Importance |
|---:|---|---:|
| 1 | tr_log_testduration_rolling_min_10 | 20.00% |
| 2 | gh_num_issue_comments | 1.39% |
| 3 | gh_num_pr_comments | 0.87% |
| 4 | gh_repo_num_commits | 0.33% |
| 5 | tr_log_testduration_rolling_min_3 | 0.26% |

### getsentry/sentry (Gradient Boosting, R²=0.0497)

| Rank | Feature | Importance |
|---:|---|---:|
| 1 | tr_log_testduration | 5.97% |
| 2 | tr_log_num_tests_run | 2.23% |
| 3 | tr_log_testduration_rolling_min_5 | 2.17% |
| 4 | tr_log_testduration_rolling_max_7 | 1.99% |
| 5 | tr_log_testduration_rolling_max_3 | 1.72% |

### gonum/matrix (Random Forest, R²=0.0052)

| Rank | Feature | Importance |
|---:|---|---:|
| 1 | tr_log_num_tests_run | 10.62% |
| 2 | tr_log_num_tests_ok | 9.26% |
| 3 | tr_log_testduration_lag_1 | 0.83% |
| 4 | tr_log_setup_time_rolling_min_3 | 0.32% |
| 5 | tr_log_setup_time_rolling_mean_7 | 0.13% |

### mongodb/mongoid (Gradient Boosting, R²=-0.0396)

| Rank | Feature | Importance |
|---:|---|---:|
| 1 | gh_repo_num_commits | 0.22% |
| 2 | gh_repo_age | 0.20% |
| 3 | gh_test_cases_per_kloc | 0.14% |
| 4 | gh_diff_other_files | 0.11% |
| 5 | tr_log_num_tests_ok | 0.06% |

### rg3/youtube-dl (Linear Regression, R²=0.4753)

| Rank | Feature | Importance |
|---:|---|---:|
| 1 | tr_log_testduration | 503100.86% |
| 2 | tr_log_testduration_lag_3 | 444039.63% |
| 3 | tr_log_testduration_diff_2 | 432691.84% |
| 4 | tr_log_testduration_diff_1 | 401622.75% |
| 5 | tr_log_testduration_diff_3 | 374539.28% |

### rspec/rspec-core (Random Forest, R²=-0.2936)

| Rank | Feature | Importance |
|---:|---|---:|
| 1 | gh_asserts_cases_per_kloc | 18.36% |
| 2 | gh_description_complexity | 14.80% |
| 3 | gh_team_size | 5.38% |
| 4 | gh_test_cases_per_kloc | 5.20% |
| 5 | gh_test_lines_per_kloc | 1.15% |
