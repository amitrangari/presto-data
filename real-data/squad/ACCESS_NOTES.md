# SQuaD access notes (archived 2026-08-10 — resolved)

This documents how the SQuaD data was obtained, kept for reproducibility provenance. The blocker
described below is resolved; this file is historical, not a live task.

## Original blocker (2026-08-09)

The Zenodo record (`zenodo.org/records/17566691`) is a redirect-only package (10 files, 3MB: just
figures, licenses, and a README) — **not** the actual dataset (still sitting at `../squad/zenodo-msr-dataset.zip`
for reference). The real data lives on Finland's IDA/Fairdata research-data service:
`https://etsin.fairdata.fi/dataset/2209b041-b35b-4863-8798-3204186b6b11` (CSV format).

- **Total dataset size: 1.94 TB** — dominated by 7 per-tool static-analysis dumps at method/file
  granularity (`pmd.csv` 678GB, `understand.csv` 389GB, `ck.csv` 337GB, `JaSoMe.csv` 195GB,
  `sonarqube.csv` 179GB, `codescene.csv` 84GB, `rminer.csv` 58GB). None of these were needed.
- IDA's file listing is reachable via the public Metax v3 API
  (`https://metax.fairdata.fi/v3/datasets/<id>/files`), but the actual per-file download goes
  through Fairdata's Download service, a JS-driven selection/packaging flow (`etsin.fairdata.fi` UI
  → `download.fairdata.fi` API) that could not be reverse-engineered from outside a browser session
  — guessed REST endpoints (`/api/dataset/{id}/authorize`, `/api/requests`) both 404'd.

## Resolution (2026-08-10)

The user visited the Etsin dataset page in a browser, selected the required files in the
download-package UI, and passed the resulting signed `download.fairdata.fi` URLs (JWT-token-bearing,
time-limited) back for retrieval. All 9 required `RAW_DATA/` files were fetched via `curl` into
`../squad/`:

`process_metrics.csv`, `release_data.csv`, `github_metrics.csv`, `projects_data.csv`,
`PRJ_ITS_VLN_LINKAGE.csv`, `cve_data.csv`, `cwe_data.csv`, `pp_rminer.csv`, `pyref.csv`
(~54MB total, verified as valid CSVs with correct headers, not error pages).

Two optional extras not required for the copula-correlation validation (`commit_data.csv`, ~16GB;
`issue_data.csv`, ~3.3GB) were also fetched by the same route, at the user's request.

## Still open

The adapter/pipeline script for SQuaD does not exist yet — the other two real-data sources
(`mozilla-perfherder/`, `ghalogs/`) each have a `run_pipeline_<source>.py`; SQuaD's equivalent still
needs to be written before this data can feed into the paper's copula-correlation ablation
(see `../../code/synthetic_data_generator/r1_analysis.py` for the related target-correlation
ablation this would extend with real calibration data).
