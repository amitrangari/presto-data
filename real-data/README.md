# Real-data sources for PRESTO external validity

Four independent real-world datasets used to validate PRESTO alongside the 3 fully-synthetic
domains in `../synthetic-data-projects/`. To keep this repository small and clonable, **bulk
third-party raw data is not re-hosted here** — each source folder ships the adapter/pipeline
script, the paper's own small derived outputs, and a `DOWNLOAD.md` with exact instructions
(source DOI/URL + fetch commands or script) to retrieve the raw data yourself.

| Source | What's here | What you fetch | Raw size | License |
|---|---|---|---|---|
| `travistorrent/` | Pipeline + feature-importance scripts, result docs, `DOWNLOAD.md` | `final-2017-01-25.csv.gz` from Figshare `10.6084/m9.figshare.19314170` | ~252MB (gz) | CC-BY-4.0 |
| `mozilla-perfherder/` | Pipeline scripts, original extraction tooling (`scripts/`), result docs, `DOWNLOAD.md` | Timeseries + alerts + bugs data from Zenodo `10.5281/zenodo.14642238` or re-extracted via Treeherder API | ~4.8GB | CC-BY-4.0 |
| `ghalogs/` | Pipeline + feature-extraction script, result docs, `DOWNLOAD.md` | `runs.json.gz` + `repositories.json.gz` from Zenodo `10.5281/zenodo.10154920` | ~1.1GB | CC-BY-SA-4.0 |
| `squad/` | Adapter scripts, the paper's own aggregated static-analysis outputs (`RAW_DATA/aggregated/`, ~13MB), **and** the 9 required raw CSVs (~54MB, small enough to ship directly) | Nothing — already included. `ACCESS_NOTES.md` documents provenance (Fairdata portal, manual browser step) if you need to re-fetch or verify | ~54MB (included) | CC-BY-4.0 |

## Why SQuaD's required files are included but the other three aren't

SQuaD's 9 required files total ~54MB (largest single file 19MB) — small enough to ship directly
without threatening repo size, and re-fetching them requires a manual browser step through
Fairdata's JS-driven download portal (see `squad/ACCESS_NOTES.md`) that can't be scripted. The
other three sources are multi-GB bulk downloads available via a stable, scriptable URL (Figshare/
Zenodo direct file links or a documented API), so re-hosting them here would only add bulk without
adding reproducibility — `DOWNLOAD.md` in each folder gets you the exact same data.

## What is intentionally excluded everywhere

- **`squad/RAW_DATA/{pmd,understand,ck,JaSoMe,sonarqube,codescene,rminer}.csv`** — raw,
  unaggregated per-file/per-method static-analysis tool output (~1.8TB total). Reduced by
  `squad/RAW_DATA/aggregate_raw_static_analysis.py` into the small, release-level-aggregated files
  actually used by the paper (`squad/RAW_DATA/aggregated/*.csv`, ~13MB — included). Regenerable
  from the original SQuaD release artifacts (`squad/zenodo-msr-dataset.zip`,
  `10.5281/zenodo.17566691`) by rerunning that script.
- **`squad/commit_data.csv`, `squad/issue_data.csv`** (and their `RAW_DATA/` duplicates) — large
  (16GB / 3.3GB) optional extras fetched alongside the required files but not used by any script
  in this paper.
- **TravisTorrent's `final-2017-01-25.csv.gz`, `final-2017-01-25.csv`, `seven_projects.csv`** —
  see `travistorrent/DOWNLOAD.md`. Note `final-2017-01-25.csv` was a redundant uncompressed copy
  of the `.gz` (byte-identical after decompression) — only the `.gz` is ever needed.
- **GHALogs' `runs.json.gz`, `repositories.json.gz`, `run_features.csv`** — see
  `ghalogs/DOWNLOAD.md`. The 142GB `github_run_logs.zip` full log archive was never downloaded —
  not needed for release-level build/test timing analysis.
- **Perfherder's `timeseries-data/`, `alerts_data.csv`, `bugs_data.csv`** — see
  `mozilla-perfherder/DOWNLOAD.md`.
- **`.venv/`, `__pycache__/`, `.DS_Store`** — regenerable/environment-specific.

## Reproducing the real-world results

1. Pick a source folder, follow its `DOWNLOAD.md` to fetch the raw data into that folder.
2. Run its `run_pipeline_<source>.py` — reproduces `output_<source>_ml_results.md`.
3. `bootstrap_real_world_ci.py` (this directory) computes the bootstrap confidence intervals
   reported across all four sources — see `REAL_WORLD_BOOTSTRAP_CI_EVIDENCE_{fast,slow}.md`.
