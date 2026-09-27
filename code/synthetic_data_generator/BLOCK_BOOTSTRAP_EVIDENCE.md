# M11 — Moving-Block Bootstrap for Temporally-Ordered Holdouts

**Method:** moving-block bootstrap, 2000 resamples per case, seed 20260810. Block length follows n^(1/3), rounded, floored at 2 (reported per case since holdout size varies). Resamples overlapping contiguous blocks of (y_true, y_pred) with replacement, concatenates to the original holdout length, recomputes R^2 per resample. Compared directly against the existing pairs/case bootstrap (`r1_analysis.py`'s method, 2000 resamples, identical seed) on the *same* fitted-model predictions, so any CI-width difference reflects the resampling scheme alone, not a different model fit.

**Scope:** the 3 synthetic domains only (temporally-ordered by construction), all 6 domain/condition combinations (with-AR and without-AR for each of the 3 domains). TravisTorrent and Mozilla Perfherder (also temporally ordered) receive this same treatment in their own adapter scripts -- see `real-data/travistorrent/TRAVISTORRENT_BLOCK_BOOTSTRAP_EVIDENCE.md` and `real-data/mozilla-perfherder/PERFHERDER_BLOCK_BOOTSTRAP_EVIDENCE.md`. GHALogs and SQuaD are cross-sectional (no temporal ordering within their holdouts), so the existing pairs bootstrap remains the statistically appropriate choice there and should NOT be replaced with a block bootstrap.

Random Forest only (the paper's headline model for every case below).

| Domain | Condition | n | Block size | Point R² | Pairs-bootstrap 95% CI (width) | Block-bootstrap 95% CI (width) | Pairs excl. 0? | Block excl. 0? |
|---|---|---:|---:|---:|---|---|:---:|:---:|
| abc-cloud-provider | with_AR | 34 | 3 | 0.195 | [-6.330, 0.570] (6.900) | [-2.615, 0.708] (3.323) | no | no |
| abc-cloud-provider | without_AR | 34 | 3 | 0.106 | [-6.533, 0.463] (6.996) | [-2.650, 0.575] (3.225) | no | no |
| card-payment-processor | with_AR | 30 | 3 | 0.442 | [-0.400, 0.881] (1.281) | [-0.620, 0.756] (1.376) | no | no |
| card-payment-processor | without_AR | 30 | 3 | 0.475 | [-0.179, 0.892] (1.071) | [-0.336, 0.803] (1.139) | no | no |
| xyz-sales-force | with_AR | 40 | 3 | 0.495 | [0.216, 0.671] (0.455) | [0.226, 0.698] (0.472) | yes | yes |
| xyz-sales-force | without_AR | 40 | 3 | 0.487 | [0.222, 0.658] (0.436) | [0.229, 0.686] (0.457) | yes | yes |

**Summary:** mean CI width change (block − pairs) across these 6 cases: -1.191 R² units. 0 of 6 case(s) change significance status (excludes-zero vs. not) between the two bootstrap methods.

**Interpretation.** A moving-block bootstrap that preserves local temporal dependence in the (error) sequence is expected to produce wider (or equal) CIs than a pairs bootstrap when residuals are positively autocorrelated, since blocks limit how much resampled variability the procedure can generate relative to treating every row as an independent draw. Whether that pattern holds here, and how large the practical effect is on any headline significance claim, should be read directly from the table above rather than assumed.
