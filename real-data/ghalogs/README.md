# GHALogs — GitHub Actions CI/CD runs dataset

**Source:** Zenodo `10.5281/zenodo.10154920`, "GHALogs: Large-Scale Dataset of GitHub Actions Runs"
(MSR 2025). License: **CC-BY-SA-4.0** (attribution + share-alike — any derived dataset we publish
from this must also be CC-BY-SA-4.0).

**Downloaded:** `runs.json.gz` (1.06GB) and `repositories.json.gz` (69MB). The 142GB
`github_run_logs.zip` full log archive was intentionally skipped — not needed for release-level
build/test timing analysis, per `../../top3_real_vs_synthetic.md`.

**Scale:** 116k workflows, 513k runs, 2.3M steps, across 25k public repos, 20 languages.

**Why it matters for PRESTO:** modern (2024/2025-vintage) CI cohort, complementing the paper's only
current real-world validation (TravisTorrent, 2017-vintage, Travis CI). GHALogs provides per-step
timing (build vs. test vs. setup duration separated), unlike TravisTorrent's single `tr_duration`
field. Directly answers Major-issue M2 in the consensus review roadmap: "results replicate across
two independent CI platforms a decade apart" is a stronger claim than TravisTorrent alone.

**Status:** downloaded, not yet parsed/joined into a PRESTO-format feature table. `runs.json.gz`
and `repositories.json.gz` need to be decompressed and inspected for schema before any pipeline
work can use them.
