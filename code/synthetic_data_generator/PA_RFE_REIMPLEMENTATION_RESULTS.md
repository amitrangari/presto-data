# PA-RFE reimplementation results (R4/R7)

**Date:** 2026-08-11  
**Item:** ACTION_PLAN.md R4/R7 -- PA-RFE had no implementation anywhere in the deposited reproducibility package (confirmed by exhaustive search, see STATUS.md); these numbers are reimplemented from the algorithm pseudocode in `paper-work/overleaf/main.md` (Stage 6 / Algorithm alg:parfe) and rerun against the corrected (post-R2-fix) synthetic data. They supersede the unverified, carried-over-from-original-submission numbers previously in the paper.

**Method:** k_min=2 per SDLC phase (8 phases, floor 16), step s=5, Gradient Boosting, permutation importance (n_repeats=10) on a held-out validation split, 60/20/20 train/validation/test temporal split. `quality_score`/`stability_score` form a virtual cross-phase group with k_min=0. Standard RFE and SelectKBest baselines target the same final feature count PA-RFE converges to, for a fair comparison.

## Comparison table (test R^2, evaluated once)

| Domain | Features | PA-RFE | Std RFE | SelectKBest |
|---|---|---:|---:|---:|
| abc-cloud-provider | 241->81 | -0.279 | 0.355 | 0.404 |
| card-payment-processor | 241->26 | 0.092 | -0.083 | 0.316 |
| xyz-sales-force | 241->51 | -0.026 | -0.049 | -0.028 |

## Validation-set ablation curves

### abc-cloud-provider

| |F| | Validation R^2 |
|---:|---:|
| 241 | 0.3295 |
| 236 | 0.5187 |
| 231 | 0.6243 |
| 226 | 0.6163 |
| 221 | 0.6575 |
| 216 | 0.6339 |
| 211 | 0.6423 |
| 206 | 0.6948 |
| 201 | 0.6910 |
| 196 | 0.7251 |
| 191 | 0.6974 |
| 186 | 0.6811 |
| 181 | 0.7153 |
| 176 | 0.7268 |
| 171 | 0.7059 |
| 166 | 0.7274 |
| 161 | 0.6743 |
| 156 | 0.7263 |
| 151 | 0.7196 |
| 146 | 0.5418 |
| 141 | 0.6910 |
| 136 | 0.7449 |
| 131 | 0.7881 |
| 126 | 0.7603 |
| 121 | 0.8052 |
| 116 | 0.7656 |
| 111 | 0.7640 |
| 106 | 0.7663 |
| 101 | 0.8092 |
| 96 | 0.8114 |
| 91 | 0.8103 |
| 86 | 0.7972 |
| 81 | 0.8241 |
| 76 | 0.8215 |
| 71 | 0.8025 |
| 66 | 0.7942 |
| 61 | 0.7844 |
| 56 | 0.7918 |
| 51 | 0.8025 |
| 46 | 0.7836 |
| 41 | 0.7828 |
| 36 | 0.7905 |
| 31 | 0.8163 |
| 26 | 0.7911 |
| 21 | 0.8036 |
| 16 | 0.5798 |

### card-payment-processor

| |F| | Validation R^2 |
|---:|---:|
| 241 | 0.1138 |
| 236 | 0.1804 |
| 231 | 0.1414 |
| 226 | 0.1710 |
| 221 | 0.2370 |
| 216 | 0.1797 |
| 211 | 0.1818 |
| 206 | 0.2649 |
| 201 | 0.2515 |
| 196 | 0.2453 |
| 191 | 0.1817 |
| 186 | 0.2279 |
| 181 | 0.2684 |
| 176 | 0.2026 |
| 171 | 0.2166 |
| 166 | 0.2300 |
| 161 | 0.2261 |
| 156 | 0.1939 |
| 151 | 0.2828 |
| 146 | 0.2356 |
| 141 | 0.2449 |
| 136 | 0.2712 |
| 131 | 0.2061 |
| 126 | 0.2866 |
| 121 | 0.2168 |
| 116 | 0.2596 |
| 111 | 0.2449 |
| 106 | 0.2541 |
| 101 | 0.2983 |
| 96 | 0.2970 |
| 91 | 0.2637 |
| 86 | 0.2282 |
| 81 | 0.2905 |
| 76 | 0.2872 |
| 71 | 0.2845 |
| 66 | 0.2880 |
| 61 | 0.2954 |
| 56 | 0.2515 |
| 51 | 0.2189 |
| 46 | 0.2912 |
| 41 | 0.2533 |
| 36 | 0.2904 |
| 31 | 0.2388 |
| 26 | 0.3064 |
| 21 | 0.2380 |
| 16 | 0.2153 |

### xyz-sales-force

| |F| | Validation R^2 |
|---:|---:|
| 241 | 0.6546 |
| 236 | 0.6445 |
| 231 | 0.6875 |
| 226 | 0.7064 |
| 221 | 0.6773 |
| 216 | 0.7088 |
| 211 | 0.7396 |
| 206 | 0.7329 |
| 201 | 0.7467 |
| 196 | 0.7254 |
| 191 | 0.7469 |
| 186 | 0.7497 |
| 181 | 0.7503 |
| 176 | 0.7628 |
| 171 | 0.7360 |
| 166 | 0.7609 |
| 161 | 0.7525 |
| 156 | 0.7595 |
| 151 | 0.7641 |
| 146 | 0.7629 |
| 141 | 0.7556 |
| 136 | 0.7464 |
| 131 | 0.7493 |
| 126 | 0.7449 |
| 121 | 0.7594 |
| 116 | 0.7160 |
| 111 | 0.7389 |
| 106 | 0.7209 |
| 101 | 0.7218 |
| 96 | 0.6944 |
| 91 | 0.7036 |
| 86 | 0.7510 |
| 81 | 0.7638 |
| 76 | 0.7689 |
| 71 | 0.7654 |
| 66 | 0.7567 |
| 61 | 0.7852 |
| 56 | 0.7843 |
| 51 | 0.7994 |
| 46 | 0.7762 |
| 41 | 0.7782 |
| 36 | 0.7850 |
| 31 | 0.7591 |
| 26 | 0.7480 |
| 21 | 0.7065 |
| 16 | 0.7349 |

## Phase contribution at PA-RFE's optimal subset

### abc-cloud-provider (8 phase groups represented)

| Phase | % of permutation importance |
|---|---:|
| Performance Test | 35.4% |
| Requirements | 29.0% |
| Test | 19.2% |
| UAT | 8.9% |
| Production | 5.9% |
| Chaos | 0.8% |
| Build | 0.7% |
| Code | 0.2% |

### card-payment-processor (8 phase groups represented)

| Phase | % of permutation importance |
|---|---:|
| Performance Test | 65.7% |
| Production | 23.7% |
| Requirements | 2.9% |
| Chaos | 2.5% |
| Build | 2.0% |
| Code | 2.0% |
| Test | 1.0% |
| UAT | 0.2% |

### xyz-sales-force (8 phase groups represented)

| Phase | % of permutation importance |
|---|---:|
| Performance Test | 46.7% |
| UAT | 25.7% |
| Production | 18.6% |
| Test | 5.1% |
| Chaos | 1.5% |
| Build | 1.1% |
| Requirements | 0.9% |
| Code | 0.3% |

