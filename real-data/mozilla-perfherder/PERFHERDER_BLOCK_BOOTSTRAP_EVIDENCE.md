# Mozilla Perfherder — Moving-Block Bootstrap for Temporally-Ordered Holdouts

**Method:** moving-block bootstrap, 2000 resamples per signature, seed 20260810. Identical procedure to `code/synthetic_data_generator/m11_block_bootstrap.py` (`block_size_for()`, `bootstrap_r2_ci_pairs()`, `bootstrap_r2_ci_moving_block()`, imported directly, not reimplemented), applied here to Perfherder's 3 within-signature temporal holdouts, with-AR (target-derived-features-included) condition, matching `real-data/bootstrap_real_world_ci.py`'s `run_perfherder()` scope. Filling the follow-on scope flagged in `BLOCK_BOOTSTRAP_EVIDENCE.md`. Block length follows n^(1/3), rounded, floored at 2, reported per signature. Ordering variable: `push_timestamp` per signature, the same ordering `run_pipeline_perfherder.py`'s 80/20 split already uses.

**Model:** Random Forest only, matching this evidence family's headline-model convention (`m11_block_bootstrap.py`, `BLOCK_BOOTSTRAP_EVIDENCE.md`) -- the paper's *fixed-hyperparameter, secondary/untuned-baseline* protocol, not the primary nested-CV-selected protocol introduced this revision (Section 3.2.5). Data loading (`load_alerts_lookup`, `load_signature_series`, `engineer_features`, `prepare_features`) reused directly from `run_pipeline_perfherder.py` via importlib -- not reimplemented. Scope: with-AR condition only, matching `bootstrap_real_world_ci.py`'s `run_perfherder()`, since Perfherder's with-AR results are part of this paper's confirmatory set (Section 4.1 opening note); the without-AR (alert-history-only) condition is covered separately in the paired-difference bootstrap (`PAIRED_DIFFERENCE_BOOTSTRAP_EVIDENCE.md`, comparison B1), not here.

| Signature | n (test) | Block size | Point R² | Pairs-bootstrap 95% CI (width) | Block-bootstrap 95% CI (width) | Pairs excl. 0? | Block excl. 0? |
|---|---:|---:|---:|---|---|:---:|:---:|
| espn-loadtime | 710 | 9 | 0.235 | [0.147, 0.311] (0.164) | [0.044, 0.367] (0.323) | yes | yes |
| instagram-speedindex | 636 | 9 | 0.153 | [0.108, 0.191] (0.083) | [0.011, 0.253] (0.241) | yes | yes |
| nytimes-speedindex | 645 | 9 | 0.126 | [0.039, 0.200] (0.162) | [0.020, 0.215] (0.195) | yes | yes |

**Summary:** mean CI width change (block − pairs) across these 3 signatures: +0.117 R² units. 0 of 3 signature(s) change significance status (excludes-zero vs. not) between the two bootstrap methods.

**Interpretation.** Perfherder's with-AR results are part of this paper's confirmatory set. A significance-status flip here (pairs says significant, block does not, or vice versa) would directly affect that designation and should be read from the table above, not assumed from the synthetic-domain pattern.
