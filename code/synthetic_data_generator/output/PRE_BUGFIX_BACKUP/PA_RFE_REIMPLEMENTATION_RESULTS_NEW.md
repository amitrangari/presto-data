# PA-RFE reimplementation results (R4/R7)

**Date:** 2026-08-11  
**Item:** ACTION_PLAN.md R4/R7 -- PA-RFE had no implementation anywhere in the deposited reproducibility package (confirmed by exhaustive search, see STATUS.md); these numbers are reimplemented from the algorithm pseudocode in `paper-work/overleaf/main.md` (Stage 6 / Algorithm alg:parfe) and rerun against the corrected (post-R2-fix) synthetic data. They supersede the unverified, carried-over-from-original-submission numbers previously in the paper.

**Method:** k_min=2 per SDLC phase (8 phases, floor 16), step s=5, Gradient Boosting, permutation importance (n_repeats=10) on a held-out validation split, 60/20/20 train/validation/test temporal split. `quality_score`/`stability_score` form a virtual cross-phase group with k_min=0. Standard RFE and SelectKBest baselines target the same final feature count PA-RFE converges to, for a fair comparison.

## Comparison table (test R^2, evaluated once)

| Domain | Features | PA-RFE | Std RFE | SelectKBest |
|---|---|---:|---:|---:|
| abc-cloud-provider | 241->76 | -3.026 | -1.159 | -1.400 |
| card-payment-processor | 241->86 | 0.313 | 0.201 | 0.239 |
| xyz-sales-force | 241->136 | 0.236 | -0.161 | -0.049 |

## Validation-set ablation curves

### abc-cloud-provider

| |F| | Validation R^2 |
|---:|---:|
| 241 | -3.1611 |
| 236 | -2.1245 |
| 231 | -2.6456 |
| 226 | -0.3620 |
| 221 | -0.3183 |
| 216 | -0.3444 |
| 211 | -0.3885 |
| 206 | -0.2764 |
| 201 | -0.0879 |
| 196 | 0.0075 |
| 191 | -0.0702 |
| 186 | -0.0984 |
| 181 | 0.0227 |
| 176 | 0.0174 |
| 171 | -0.0054 |
| 166 | 0.1280 |
| 161 | 0.0163 |
| 156 | 0.1567 |
| 151 | 0.1908 |
| 146 | 0.2008 |
| 141 | 0.1666 |
| 136 | 0.1821 |
| 131 | 0.2061 |
| 126 | 0.2587 |
| 121 | 0.2535 |
| 116 | 0.2594 |
| 111 | 0.1813 |
| 106 | 0.2333 |
| 101 | 0.1989 |
| 96 | 0.2108 |
| 91 | 0.2167 |
| 86 | 0.2500 |
| 81 | 0.2551 |
| 76 | 0.2708 |
| 71 | 0.1704 |
| 66 | 0.2323 |
| 61 | 0.2451 |
| 56 | 0.2194 |
| 51 | 0.2248 |
| 46 | 0.2534 |
| 41 | 0.2304 |
| 36 | 0.2247 |
| 31 | 0.2029 |
| 26 | 0.1412 |
| 21 | 0.2193 |
| 16 | 0.1405 |

### card-payment-processor

| |F| | Validation R^2 |
|---:|---:|
| 241 | 0.4627 |
| 236 | 0.4525 |
| 231 | 0.4509 |
| 226 | 0.5013 |
| 221 | 0.4630 |
| 216 | 0.4414 |
| 211 | 0.4716 |
| 206 | 0.4521 |
| 201 | 0.5030 |
| 196 | 0.5192 |
| 191 | 0.5022 |
| 186 | 0.4866 |
| 181 | 0.5116 |
| 176 | 0.5163 |
| 171 | 0.5252 |
| 166 | 0.5142 |
| 161 | 0.4898 |
| 156 | 0.5102 |
| 151 | 0.5191 |
| 146 | 0.5287 |
| 141 | 0.5273 |
| 136 | 0.5419 |
| 131 | 0.5294 |
| 126 | 0.5180 |
| 121 | 0.5156 |
| 116 | 0.5157 |
| 111 | 0.5118 |
| 106 | 0.5411 |
| 101 | 0.5183 |
| 96 | 0.5445 |
| 91 | 0.5336 |
| 86 | 0.5564 |
| 81 | 0.5165 |
| 76 | 0.5351 |
| 71 | 0.5147 |
| 66 | 0.5054 |
| 61 | 0.5434 |
| 56 | 0.5492 |
| 51 | 0.5317 |
| 46 | 0.5281 |
| 41 | 0.5470 |
| 36 | 0.5245 |
| 31 | 0.5037 |
| 26 | 0.5218 |
| 21 | 0.5334 |
| 16 | 0.5218 |

### xyz-sales-force

| |F| | Validation R^2 |
|---:|---:|
| 241 | -0.0583 |
| 236 | 0.2424 |
| 231 | 0.3788 |
| 226 | 0.3044 |
| 221 | 0.2897 |
| 216 | 0.3636 |
| 211 | 0.3445 |
| 206 | 0.3185 |
| 201 | 0.3736 |
| 196 | 0.4198 |
| 191 | 0.3929 |
| 186 | 0.4277 |
| 181 | 0.4609 |
| 176 | 0.5010 |
| 171 | 0.4858 |
| 166 | 0.4574 |
| 161 | 0.4763 |
| 156 | 0.5005 |
| 151 | 0.4991 |
| 146 | 0.5091 |
| 141 | 0.5127 |
| 136 | 0.5802 |
| 131 | 0.4970 |
| 126 | 0.5800 |
| 121 | 0.5281 |
| 116 | 0.5696 |
| 111 | 0.4291 |
| 106 | 0.4567 |
| 101 | 0.5160 |
| 96 | 0.4785 |
| 91 | 0.5136 |
| 86 | 0.5149 |
| 81 | 0.5191 |
| 76 | 0.5614 |
| 71 | 0.5179 |
| 66 | 0.5553 |
| 61 | 0.5069 |
| 56 | 0.5318 |
| 51 | 0.5652 |
| 46 | 0.5410 |
| 41 | 0.5755 |
| 36 | 0.5536 |
| 31 | 0.5516 |
| 26 | 0.5555 |
| 21 | 0.5230 |
| 16 | 0.4641 |

## Phase contribution at PA-RFE's optimal subset

### abc-cloud-provider (9 phase groups represented)

| Phase | % of permutation importance |
|---|---:|
| Test | 52.7% |
| Production | 38.9% |
| Requirements | 7.7% |
| Chaos | 0.2% |
| Build | 0.2% |
| UAT | 0.1% |
| Performance Test | 0.1% |
| cross_phase | 0.0% |
| Code | 0.0% |

### card-payment-processor (9 phase groups represented)

| Phase | % of permutation importance |
|---|---:|
| Performance Test | 64.8% |
| Production | 12.8% |
| Requirements | 9.3% |
| Build | 7.2% |
| Chaos | 3.4% |
| Code | 1.3% |
| Test | 0.9% |
| UAT | 0.4% |
| cross_phase | 0.0% |

### xyz-sales-force (9 phase groups represented)

| Phase | % of permutation importance |
|---|---:|
| Performance Test | 50.2% |
| Production | 20.0% |
| Build | 10.3% |
| UAT | 9.3% |
| Test | 4.1% |
| Code | 2.2% |
| Requirements | 2.0% |
| Chaos | 1.9% |
| cross_phase | 0.0% |

