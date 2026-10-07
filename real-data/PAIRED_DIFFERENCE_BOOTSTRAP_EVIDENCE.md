# Paired-Difference Bootstrap Confidence Intervals

Reviewer 2's round-2 comment: reporting two separate confidence intervals for "with feature X" and "without feature X" and eyeballing whether they look different is not the same as testing whether the DIFFERENCE is significant. This report computes a paired-difference bootstrap CI directly on R²(condition A) − R²(condition B): the same bootstrap indices are resampled jointly across both conditions on each of 2000 resamples (seed 20260810), and the 2.5/97.5 percentile CI is taken on the resulting distribution of differences. Random Forest throughout (same hyperparameters as `m11_block_bootstrap.py` / `bootstrap_real_world_ci.py`'s build_models()), held fixed across both conditions in every comparison so the difference reflects the feature-set change alone.

**Row-alignment correctness check:** for every comparison below, y_true was verified identical (same values, same order) between the two conditions before pairing (see script asserts). SQuaD's plain-vs-enriched comparison is the only one where this required an explicit check beyond simple column-set difference on a shared dataframe -- see its row in the table and the accompanying alignment note.

## B1a. Synthetic domains: with-AR vs. without-AR

| Case | n | With-AR R² | Without-AR R² | Diff (A − B) | 95% CI on diff | Excludes 0? | Interpretation |
|---|---:|---:|---:|---:|---|:---:|---|
| abc-cloud-provider | 34 | 0.1946 | 0.1065 | +0.0882 | [-0.0621, +0.4565] | no | noise-level (CI includes 0) |
| card-payment-processor | 30 | 0.4424 | 0.4752 | -0.0329 | [-0.2292, +0.0128] | no | noise-level (CI includes 0) |
| xyz-sales-force | 40 | 0.4948 | 0.4872 | +0.0075 | [-0.0380, +0.0519] | no | noise-level (CI includes 0) |

## B1b. Mozilla Perfherder: with-AR vs. without-AR (alert-history-only)

| Case | n | With-AR R² | Without-AR R² | Diff (A − B) | 95% CI on diff | Excludes 0? | Interpretation |
|---|---:|---:|---:|---:|---|:---:|---|
| espn-loadtime | 710 | 0.2353 | -3.2585 | +3.4939 | [+3.1495, +3.9344] | yes | significant gap |
| instagram-speedindex | 636 | 0.1527 | -0.3690 | +0.5217 | [+0.4948, +0.5528] | yes | significant gap |
| nytimes-speedindex | 645 | 0.1261 | -4.2762 | +4.4023 | [+3.9124, +5.0174] | yes | significant gap |

## B2. GHALogs: full-feature vs. mean_n_steps-ablated

| Case | n | Full R² | Ablated R² | Diff (A − B) | 95% CI on diff | Excludes 0? | Interpretation |
|---|---:|---:|---:|---:|---|:---:|---|
| all repos | 5689 | 0.0964 | -0.0440 | +0.1404 | [+0.0567, +0.4923] | yes | significant gap |

## B3. TravisTorrent: full vs. circular-feature-excluded (tr_log_testduration-derived)

| Case | n | Full R² | Excluded R² | Diff (A − B) | 95% CI on diff | Excludes 0? | Interpretation |
|---|---:|---:|---:|---:|---|:---:|---|
| DataDog/dd-agent | 28785 | -0.6226 | -1.0633 | +0.4407 | [+0.4211, +0.4606] | yes | significant gap |
| bundler/bundler | 16108 | -0.1514 | -0.2742 | +0.1227 | [+0.1051, +0.1423] | yes | significant gap |
| getsentry/sentry | 11178 | -0.1126 | -0.1020 | -0.0105 | [-0.0120, -0.0092] | yes | significant gap |
| gonum/matrix | 470 | 0.0052 | -0.0177 | +0.0229 | [+0.0095, +0.0387] | yes | significant gap |
| mongodb/mongoid | 7285 | -0.0857 | -0.0859 | +0.0002 | [+0.0000, +0.0005] | yes | significant gap |
| rg3/youtube-dl | 7252 | 0.3890 | -0.2515 | +0.6404 | [+0.6016, +0.6805] | yes | significant gap |
| rspec/rspec-core | 5993 | -0.2936 | -0.5281 | +0.2345 | [+0.1954, +0.2742] | yes | significant gap |

*Statistical vs. practical significance note:* getsentry/sentry (-0.0105), mongodb/mongoid (+0.0002) exclude zero (statistically significant, given large holdout n) but the point difference itself is negligible or even in the opposite direction from the other 5 projects (full-feature R² typically exceeding excluded-feature R² by a large margin). With n in the thousands, a paired-difference bootstrap CI can exclude zero for a difference too small to be practically meaningful -- read the point-difference magnitude alongside significance, not significance alone, for these rows.

## B4. SQuaD: static-analysis-enriched vs. plain defect-fix rate

| Case | n | Enriched R² | Plain R² | Diff (A − B) | 95% CI on diff | Excludes 0? | Interpretation |
|---|---:|---:|---:|---:|---|:---:|---|
| defect-fix rate (all projects) | 82 | 0.4844 | 0.4023 | +0.0822 | [-0.1049, +0.3271] | no | noise-level (CI includes 0) |

*Row alignment: naturally aligned (left join preserved base row order/count).*
