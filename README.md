# PRESTO — Research Compendium

Source data, code, and paper for:

> **PRESTO: A Machine Learning Framework for Predicting Software System Performance Using SDLC Metrics**
> Amit J. Rangari¹, Lalit Narayan Mishra², Biswaranjan Senapati³ (corresponding author)
> ¹ JPMorgan Chase, Atlanta, GA, USA · ² Lowe's Companies Inc., Mooresville, NC, USA · ³ Dept. of Computer Science, University of Arkansas at Little Rock (UALR), USA
> Target venue: MDPI (see `paper/main_mdpi_v3.tex`)

This repository is the single source of truth for everything used to produce the paper's numbers,
tables, and figures — the synthetic data generator, adapter scripts for four real-world validation
datasets, the analysis/ablation scripts, and the paper source itself. It's designed to be archived
by [Zenodo's GitHub integration](https://docs.github.com/en/repositories/archiving-a-github-repository/referencing-and-citing-content)
when a release is tagged, minting a DOI automatically. See `ZENODO_UPLOAD_GUIDE.md` for the
release/DOI procedure and `.zenodo.json` for prefilled deposit metadata.

**Total repo size: ~88MB.** Bulk third-party real-world datasets (Perfherder, GHALogs,
TravisTorrent — several GB each) are **not** re-hosted here; each has a `DOWNLOAD.md` in its
`real-data/<source>/` folder with the exact source DOI/URL and fetch commands. This keeps the
repository small enough to clone in seconds and clear of GitHub's 100MB per-file limit.

## Directory map

| Directory | Contents | Maps to paper |
|---|---|---|
| `paper/` | LaTeX source (`main_mdpi_v3.tex`), compiled `main_mdpi_v3.pdf`, bibliography, MDPI class files, all figures (`images/`) | The manuscript itself |
| `code/synthetic_data_generator/` | Gaussian-copula synthetic data generator (`src/`), the full analysis pipeline (`run_pipeline.py`), every ablation/robustness script (M3 nested-CV tuning, M8 Siegmund baseline, M9 System-Availability ablation, R1 bootstrap+target-correlation ablation, R2 lag-shift fix, PA-RFE reimplementation), and figure generation scripts | Sections 3–4 (methodology), Section 5 (results), all numbered ablations (M3/M8/M9/R1/R2), Figures 6–15 |
| `synthetic-data-projects/` | The three copula-generated synthetic domains actually used in the paper — ABC Cloud Provider, XYZ Sales Force, Card Payment Processor — each with per-phase CSVs, `generation_metadata.json`, `validation_report.{md,json}`, and `ml_results.md`. `archive-stale-pre-copula-rewrite/` holds the earlier, superseded generation (kept only for provenance — do not use for anything paper-related) | Section 4 (synthetic data), Table with per-domain R², headline `R²=0.26–0.36` result |
| `real-data/` | Four independent real-world validation datasets: `travistorrent/`, `mozilla-perfherder/`, `ghalogs/`, `squad/` — each with the adapter/pipeline script and the resulting `output_*_ml_results.md`. Bulk raw data is fetched via each folder's `DOWNLOAD.md`, not bundled — see `real-data/README.md` | Section 6 (real-world validation): TravisTorrent (R²=0.475 best-of-7), Mozilla Perfherder (R²=0.17–0.91), GHALogs (R²≈0.11, n=28,443), SQuaD (R²=0.402 defect-fix, 0.483 enriched; R²=0.245 CVE-count) |
| `samples/` | Small reference CSVs: DORA 2024 benchmark values used to calibrate the copula generator's marginals, a dataset index, and a release-cadence sanity check | Section 4 (DORA calibration) |
| `sdlc_metrics_data_catalog.md` | The candidate-dataset survey (25 candidates evaluated) that led to selecting the four real-world datasets above | Background/provenance for Section 6 dataset selection |
| `top3_real_vs_synthetic.md` | Side-by-side comparison of the 3 synthetic domains vs. the real-data picks, with the reasoning for prioritization | Same |

## Reproducing the paper's numbers

1. `code/synthetic_data_generator/requirements.txt` — Python environment (`.venv` not included;
   recreate locally with `python -m venv .venv && pip install -r requirements.txt`).
   `ENVIRONMENT.txt` in the same folder records the exact interpreter/OS this was last run under.
2. Regenerate the synthetic domains: `python generate.py` (seeds 42 / 123 / 456 — see
   `config/domain_profiles.yaml`), or use the pre-generated CSVs already in `synthetic-data-projects/`.
3. Run `python run_pipeline.py <domain>` for the 5-model training/evaluation that produces each
   domain's `ml_results.md`.
4. For each real-world dataset in `real-data/<source>/`: follow that folder's `DOWNLOAD.md` to
   fetch the raw data, then run its `run_pipeline_<source>.py` to reproduce
   `output_<source>_ml_results.md`. (SQuaD's required files are already included — no download
   step needed there.)
5. Ablations are standalone scripts in `code/synthetic_data_generator/`: `m3_nested_cv_tuning.py`,
   `m8_siegmund_baseline.py`, `m9_system_availability_ablation.py`, `r1_analysis.py`. Each has a
   companion `*_EVIDENCE.md` / `*_RESULTS.md` file documenting what it does and its output.
6. `generate_figures.py` and the `regenerate_fig*.py` scripts produce the paper's Figures 6–15 from
   the above outputs.

## What is intentionally excluded

See `real-data/README.md` for the full per-source breakdown of what's excluded and how to fetch
it. In short:

- **Bulk raw third-party data** for TravisTorrent, Mozilla Perfherder, and GHALogs (several GB
  each) — fetched via each folder's `DOWNLOAD.md`, not re-hosted.
- **`real-data/squad/RAW_DATA/{pmd,understand,ck,JaSoMe,sonarqube,codescene,rminer}.csv`** — raw,
  unaggregated per-file/per-method static-analysis tool output (~1.8TB total), reduced by
  `aggregate_raw_static_analysis.py` into the small aggregated files this paper actually uses
  (included, ~13MB).
- **`squad/commit_data.csv`, `squad/issue_data.csv`** — large optional extras, unused by any script.
- **`.venv/`, `__pycache__/`, `.DS_Store`** — regenerable/environment-specific.
- **`paper/author-photos/`** (in the original Overleaf project, not copied here) — MDPI-required
  headshots for the "Short Biography of Authors" section; no scientific/data value.
- **LaTeX build artifacts** (`.aux/.log/.out/.blg`) — regenerated on compile.

## Licensing

- **Data** (`real-data/`, `synthetic-data-projects/`, `samples/`): CC-BY-4.0, matching the license
  of the three re-hosted/re-derived third-party sources (Mozilla Perfherder CC-BY-4.0, GHALogs
  CC-BY-SA-4.0, SQuaD CC-BY-4.0; TravisTorrent CC-BY-4.0 via its Figshare mirror).
- **Code** (`code/`): MIT (see `code/LICENSE`).
- **Paper** (`paper/`): all rights reserved pending journal publication — do not redistribute the
  PDF beyond the preprint/Zenodo copy without checking the eventual MDPI copyright agreement.

These are defaults set for convenience — change them in `.zenodo.json` and `code/LICENSE` before
publishing if a different license is intended.

## Citing

Citation metadata (authors, ORCID, affiliations, abstract, keywords) is in `.zenodo.json`. Once
the paper has a DOI, add it to `.zenodo.json`'s `related_identifiers` and to this README.
