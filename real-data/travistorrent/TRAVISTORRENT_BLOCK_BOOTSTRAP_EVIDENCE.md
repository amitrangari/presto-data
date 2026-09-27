# TravisTorrent — Moving-Block Bootstrap for Temporally-Ordered Holdouts

**Method:** moving-block bootstrap, 2000 resamples per project, seed 20260810. Identical procedure to `code/synthetic_data_generator/m11_block_bootstrap.py` (`block_size_for()`, `bootstrap_r2_ci_pairs()`, `bootstrap_r2_ci_moving_block()`, imported directly, not reimplemented), applied here to TravisTorrent's 7 within-project temporal holdouts, filling the follow-on scope flagged in `BLOCK_BOOTSTRAP_EVIDENCE.md`. Block length follows n^(1/3), rounded, floored at 2, reported per project since holdout size varies substantially (project sizes range from ~2K to ~144K builds). Ordering variable: `gh_build_started_at` per project, the same ordering `run_pipeline_travistorrent.py`'s 80/20 split already uses.

**Model:** Random Forest only, matching this evidence family's headline-model convention (`m11_block_bootstrap.py`, `BLOCK_BOOTSTRAP_EVIDENCE.md`) -- the paper's *fixed-hyperparameter, secondary/untuned-baseline* protocol, not the primary nested-CV-selected protocol introduced this revision (Section 3.2.5). Data loading (`load_all`, `engineer`, `remove_outliers`, `prepare_features`, `build_models`) reused directly from `run_pipeline_travistorrent.py` via importlib, following `real-data/bootstrap_real_world_ci.py`'s pattern -- not reimplemented.

| Project | n (test) | Block size | Point R² | Pairs-bootstrap 95% CI (width) | Block-bootstrap 95% CI (width) | Pairs excl. 0? | Block excl. 0? |
|---|---:|---:|---:|---|---|:---:|:---:|
| DataDog/dd-agent | 28785 | 31 | -0.623 | [-0.653, -0.592] (0.060) | [-0.798, -0.480] (0.318) | yes | yes |
| bundler/bundler | 16108 | 25 | -0.151 | [-0.194, -0.114] (0.079) | [-0.345, -0.023] (0.322) | yes | yes |
| getsentry/sentry | 11178 | 22 | -0.113 | [-0.131, -0.095] (0.036) | [-0.186, -0.059] (0.127) | yes | yes |
| gonum/matrix | 470 | 8 | 0.005 | [-0.282, 0.214] (0.496) | [-0.482, 0.312] (0.793) | no | no |
| mongodb/mongoid | 7285 | 19 | -0.086 | [-0.094, -0.077] (0.017) | [-0.127, -0.053] (0.073) | yes | yes |
| rg3/youtube-dl | 7252 | 19 | 0.389 | [0.361, 0.417] (0.057) | [0.308, 0.471] (0.163) | yes | yes |
| rspec/rspec-core | 5993 | 18 | -0.294 | [-0.375, -0.223] (0.152) | [-0.597, -0.055] (0.542) | yes | yes |

**Summary:** mean CI width change (block − pairs) across these 7 projects: +0.206 R² units. 0 of 7 project(s) change significance status (excludes-zero vs. not) between the two bootstrap methods.

**Interpretation.** None of TravisTorrent's 7 projects are part of this paper's confirmatory set (Section 4.1, opening note) -- all 7 are already reported as exploratory/diagnostic, and the per-project point R² values here are the same fixed-hyperparameter Random Forest results already in the manuscript's TravisTorrent Results subsection. This table adds the dependence-aware CI a reviewer asking for temporal-holdout bootstrap coverage would expect; it does not change which results are labeled confirmatory.
