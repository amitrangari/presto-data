# TravisTorrent Feature Importance, Excluding Test-Duration-Derived Features

Reruns permutation importance with every `tr_log_testduration`-derived feature (base feature + rolling/lag/diff variants) removed before fitting, to check whether the "Test-phase metrics lead 5 of 7 projects" claim survives once the definitionally-entangled feature (test duration is a component of the build-duration target) is excluded.

| Project | Best Model | Holdout R² | # excluded | Top feature (perm. importance) | Phase |
|---|---|---:|---:|---|---|
| DataDog/dd-agent | Gradient Boosting | -0.0430 | 29 | gh_team_size (32.5%) | Project |
| bundler/bundler | Random Forest | -0.2591 | 29 | tr_log_num_tests_failed (3.7%) | Test |
| getsentry/sentry | Gradient Boosting | -0.1047 | 29 | gh_asserts_cases_per_kloc (4.8%) | Test |
| gonum/matrix | Random Forest | -0.0180 | 29 | tr_log_num_tests_run (12.6%) | Test |
| mongodb/mongoid | Gradient Boosting | -0.0506 | 29 | gh_test_cases_per_kloc (0.3%) | Other |
| rg3/youtube-dl | Random Forest | -0.2801 | 29 | tr_log_num_tests_ok (2.2%) | Test |
| rspec/rspec-core | Gradient Boosting | -0.4026 | 29 | gh_asserts_cases_per_kloc (16.8%) | Test |

Leading-feature phase tally (excluding test-duration-derived features): Test 5/7, Project 1/7, Other 1/7

## Top 5 features per project (excluding test-duration-derived)

### DataDog/dd-agent (Gradient Boosting, R²=-0.0430)

| Rank | Feature | Importance | Phase |
|---:|---|---:|---|
| 1 | gh_team_size | 32.52% | Project |
| 2 | tr_log_bool_tests_ran | 23.76% | Other |
| 3 | gh_test_lines_per_kloc | 5.09% | Test |
| 4 | gh_asserts_cases_per_kloc | 4.24% | Test |
| 5 | gh_num_commits_on_files_touched | 2.17% | Project |

### bundler/bundler (Random Forest, R²=-0.2591)

| Rank | Feature | Importance | Phase |
|---:|---|---:|---|
| 1 | tr_log_num_tests_failed | 3.65% | Test |
| 2 | tr_log_bool_tests_failed | 3.46% | Other |
| 3 | gh_num_issue_comments | 1.43% | Other |
| 4 | tr_log_num_tests_ok | 0.87% | Test |
| 5 | tr_log_num_tests_run | 0.78% | Test |

### getsentry/sentry (Gradient Boosting, R²=-0.1047)

| Rank | Feature | Importance | Phase |
|---:|---|---:|---|
| 1 | gh_asserts_cases_per_kloc | 4.75% | Test |
| 2 | gh_test_lines_per_kloc | 1.56% | Test |
| 3 | gh_repo_num_commits | 0.94% | Project |
| 4 | tr_log_bool_tests_ran | 0.54% | Other |
| 5 | gh_num_commits_on_files_touched | 0.44% | Project |

### gonum/matrix (Random Forest, R²=-0.0180)

| Rank | Feature | Importance | Phase |
|---:|---|---:|---|
| 1 | tr_log_num_tests_run | 12.56% | Test |
| 2 | tr_log_num_tests_ok | 6.61% | Test |
| 3 | tr_log_setup_time_rolling_min_3 | 0.33% | Build |
| 4 | tr_log_setup_time_rolling_std_5 | 0.21% | Build |
| 5 | tr_log_setup_time_rolling_mean_7 | 0.20% | Build |

### mongodb/mongoid (Gradient Boosting, R²=-0.0506)

| Rank | Feature | Importance | Phase |
|---:|---|---:|---|
| 1 | gh_test_cases_per_kloc | 0.29% | Other |
| 2 | gh_repo_num_commits | 0.27% | Project |
| 3 | gh_num_commits_on_files_touched | 0.14% | Project |
| 4 | gh_diff_other_files | 0.13% | Other |
| 5 | gh_repo_age | 0.11% | Project |

### rg3/youtube-dl (Random Forest, R²=-0.2801)

| Rank | Feature | Importance | Phase |
|---:|---|---:|---|
| 1 | tr_log_num_tests_ok | 2.21% | Test |
| 2 | tr_log_num_tests_run | 1.29% | Test |
| 3 | gh_test_lines_per_kloc | 1.06% | Test |
| 4 | gh_num_commits_on_files_touched | 0.51% | Project |
| 5 | tr_log_setup_time_rolling_std_5 | 0.20% | Build |

### rspec/rspec-core (Gradient Boosting, R²=-0.4026)

| Rank | Feature | Importance | Phase |
|---:|---|---:|---|
| 1 | gh_asserts_cases_per_kloc | 16.77% | Test |
| 2 | tr_log_setup_time_rolling_max_10 | 15.22% | Build |
| 3 | gh_num_commits_on_files_touched | 9.22% | Project |
| 4 | gh_description_complexity | 9.21% | Other |
| 5 | gh_test_lines_per_kloc | 5.97% | Test |
