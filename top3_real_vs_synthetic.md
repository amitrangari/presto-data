# Top 3 real-data candidates vs. the 3 existing synthetic domains

**Purpose:** for further analysis / strengthening the PRESTO paper's external validity, pick the
3 real-world candidates worth pursuing next, and show how they'd sit alongside the 3 synthetic
domains already used in the manuscript. Selection criteria: how directly each closes the paper's
specific external-validity gap (per `../../presto/paper-work/review/2026-08-08_review/consolidated/CONSENSUS_REVIEW.md`
§7), not just dataset size or popularity.

None of the 25 candidates in `sdlc_metrics_data_catalog.md` have been downloaded yet — this is a
prioritized shortlist for acquisition, not a statement that the data is already in hand.

## The 3 existing synthetic domains (already used, `synthetic-data-projects/`)

| Domain | Releases | Span | SDLC phases | Target | Status |
|---|---|---|---|---|---|
| ABC Cloud Provider | 170 | 5 yr, 2021– | 8 (Req/Code/Build/Test/UAT/PerfTest/Chaos/Production) | System Uptime (%) | Restored copy is **stale** (pre-copula-rewrite); real copula-generated version must be regenerated |
| XYZ Sales Force | 200 (spec) / 97 (restored copy) | 5.5 yr, 2022– | same 8 | System Uptime (%) | Same caveat |
| Card Payment Processor | 150 | 4 yr, 2021– | same 8 | System Uptime (%) | Same caveat; restored copy has no release-data.csv at all |

All three are **fully synthetic** (Gaussian-copula generated, DORA-2024-calibrated marginals) —
strong on phase coverage and sample construction, zero real-world grounding. This is the gap the
paper's own reviewers (§2–§3 of the consensus review) most want closed.

## Top 3 real-data picks

Ranked by how directly each addresses the two biggest reviewer-identified weaknesses: (a) the
"no public dataset links SDLC process metrics to runtime outcomes" claim is falsifiable, and
(b) the only current real-world check (TravisTorrent) validates the wrong target (build duration,
not production availability/performance) and only 4 of 8 phases.

### #1 — Mozilla Performance Measurements and Alerts (ICPE 2025)

- **Zenodo:** `10.5281/zenodo.14642238` (concept DOI; v5 at `zenodo.org/records/15465568`), CC-BY-4.0
- **Real data confirmed present:** 5,655 performance time series, 17,989 expert-validated alerts, linked Bugzilla bugs. 561 MB.
- **Phases covered:** Build + Test + Performance Testing (via Treeherder job data, joinable) + a genuine runtime-performance target — the single closest match to what PRESTO's Performance Testing / Production phases claim to predict.
- **Why #1:** it is the only candidate that is simultaneously (a) verified to exist and be downloadable (direct_fetch, not a search summary), (b) CC-BY with no access barrier, and (c) pairs a real runtime signal with real process/build data at release/push granularity — the exact shape of PRESTO's prediction task, just not yet at all 8 phases.
- **Effort:** medium. Download + join against the public Treeherder API for job outcomes.

### #2 — SQuaD: The Software Quality Dataset (MSR 2026 submission)

- **Zenodo:** `zenodo.org/records/17566691`, 450 OSS projects, 63,586 releases, 700+ unified metrics (SonarQube, CK, RefactoringMiner, etc.)
- **Phases covered:** Requirements + Code, release-level, time-aware — the same temporal unit PRESTO uses.
- **Why #2:** no runtime target, so it cannot replace a validation study — but at 63,586 real releases it is the only candidate large enough to empirically check the 84 hand-specified copula correlation pairs in the synthetic generator against real inter-metric correlations. This is the concrete data source for the correlation-ablation the ESE reviewer requires (Priority-0 item R1 in the consensus review).
- **Effort:** low-medium. Verify peer-review status (arXiv Nov 2025) before citing as validated.

### #3 — GHALogs: Large-Scale Dataset of GitHub Actions Runs (MSR 2025)

- **Zenodo:** `10.5281/zenodo.10154920`, 116k workflows, 513k runs, 2.3M steps, ~1 GB metadata (skip the 142 GB log archive)
- **Phases covered:** Build + Test, with **per-step timing** (separates build vs. test vs. setup duration, unlike TravisTorrent's single `tr_duration`).
- **Why #3:** TravisTorrent (the paper's only current real-world validation) is 2017-vintage and Travis CI is no longer dominant. GHALogs is the direct modern replacement/complement — "results replicate across two independent CI platforms a decade apart" is a materially stronger external-validity statement than TravisTorrent alone. Directly answers Major-issue M2 in the consensus review roadmap.
- **Effort:** low. ~1 GB metadata download, license unconfirmed — verify on the Zenodo record before citing.

## Side-by-side

| | ABC Cloud (synthetic) | XYZ Sales (synthetic) | Card Payment (synthetic) | Mozilla Perfherder | SQuaD | GHALogs |
|---|---|---|---|---|---|---|
| Real or synthetic | Synthetic | Synthetic | Synthetic | **Real** | **Real** | **Real** |
| Scale | 170 releases | 200 releases | 150 releases | 5,655 series / 17,989 alerts | 63,586 releases | 513k runs |
| Runtime outcome target | Yes (by construction) | Yes (by construction) | Yes (by construction) | **Yes (measured)** | No | No (durations only) |
| SDLC phases | 8/8 (by construction) | 8/8 | 8/8 | ~3/8 (Build/Test/PerfTest) | ~2/8 (Req/Code) | ~2/8 (Build/Test) |
| Access | Already generated (needs regen, see caveat above) | Same | Same | CC-BY-4.0, direct download | Open, verify license | Open, verify license |
| Best use | Primary controlled experiment | Cross-domain generalization check | Cross-domain generalization check | Second, stronger real-world validation (runtime target) | Calibrate copula correlations against real data | Modern CI cohort alongside TravisTorrent |

## Recommendation

Pursue Mozilla Perfherder first — it is the only real candidate with a genuine runtime-performance
target, which is the paper's single biggest External Validity gap per every reviewer stream. SQuaD
and GHALogs are lower-effort, high-value additions that directly answer two other named Priority-0/
Major items (correlation calibration, modern CI replication) without requiring a new validation
study to be designed from scratch.
