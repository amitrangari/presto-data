# PRESTO — Research Compendium

Source data, code, and paper for:

> **PRESTO: A Framework for Predicting Software System Performance from SDLC Metrics (Design and Proof-of-Concept Evaluation)**
> Amit J. Rangari¹, Lalit Narayan Mishra², Biswaranjan Senapati³ (corresponding author)
> ¹ JPMorgan Chase, Atlanta, GA, USA · ² Lowe's Companies Inc., Mooresville, NC, USA · ³ Dept. of Computer Science, University of Arkansas at Little Rock (UALR), USA
> Under review at MDPI *Technologies* (round-3 / v6 revision; see `paper/main_mdpi_v6.tex`)

**Release v2.0.0 matches the v6 manuscript.** Earlier releases v1.0.0/v1.0.1
(DOI [10.5281/zenodo.22005439](https://doi.org/10.5281/zenodo.22005439)) archive the initial
August 2026 snapshot (v3 manuscript) and do not contain the nested-CV, AR-leakage-fix, or
block/paired-bootstrap analyses the current paper reports. To always resolve to the latest
version, cite the concept DOI [10.5281/zenodo.22005438](https://doi.org/10.5281/zenodo.22005438).

This repository is the single source of truth for everything used to produce the paper's numbers,
tables, and figures — the synthetic data generator, adapter scripts for four real-world validation
datasets, the analysis/ablation scripts, and the paper source itself. It is archived by
[Zenodo's GitHub integration](https://docs.github.com/en/repositories/archiving-a-github-repository/referencing-and-citing-content)
when a release is tagged, minting a DOI automatically. See `ZENODO_UPLOAD_GUIDE.md` for the
release/DOI procedure, `.zenodo.json` for deposit metadata, and `CITATION.cff` for citation metadata.

Bulk third-party real-world datasets (Perfherder, GHALogs, TravisTorrent — several GB each) are
**not** re-hosted here; each has a `DOWNLOAD.md` in its `real-data/<source>/` folder with the
exact source DOI/URL and fetch commands. This keeps the repository small enough to clone in
seconds and clear of GitHub's 100MB per-file limit.

## Directory map

| Directory | Contents | Maps to paper |
|---|---|---|
| `paper/` | LaTeX source (`main_mdpi_v6.tex`), compiled `main_mdpi_v6.pdf`, Markdown mirror, bibliography, `Supplementary-Materials-v6.{md,pdf}`, MDPI class files, all figures (`images/`) | The manuscript itself |
| `code/synthetic_data_generator/` | Gaussian-copula synthetic data generator (`src/`), the analysis pipeline (`run_pipeline.py`), the shared nested-CV harness (`nested_cv_harness.py`), every ablation/robustness script, and figure-generation scripts | Section 3 (methodology), Section 4 (results), all data figures |
| `synthetic-data-projects/` | The three regenerated copula domains used in the paper — ABC Cloud Provider, XYZ Sales Force, Card Payment Processor (170 / 200 / 150 releases) — each with per-phase CSVs, `generation_metadata.json`, `validation_report.{md,json}`, and `ml_results.md`. `archive-stale-pre-copula-rewrite/` holds an earlier, superseded generation (kept only for provenance — do not use for anything paper-related) | Section 3.1.4 (synthetic data), synthetic-domain results |
| `real-data/` | Four independent real-world validation datasets: `travistorrent/`, `mozilla-perfherder/`, `ghalogs/`, `squad/` — each with adapter/pipeline scripts, nested-selection and bootstrap reruns, and result/evidence files — plus the cross-dataset `bootstrap_real_world_ci.py` and `paired_difference_bootstrap.py`. Bulk raw data is fetched via each folder's `DOWNLOAD.md` — see `real-data/README.md` | Section 4 (real-world validation) |
| `samples/` | Small reference CSVs: DORA 2024 benchmark values used to calibrate the copula generator's marginals, a dataset index, and a release-cadence sanity check | Section 3.1.4 (DORA calibration) |
| `sdlc_metrics_data_catalog.md` | The candidate-dataset survey (25 candidates evaluated) that led to selecting the four real-world datasets | Background/provenance for dataset selection |
| `top3_real_vs_synthetic.md` | Side-by-side comparison of the 3 synthetic domains vs. the real-data picks | Same |

## Headline results (v6 manuscript)

PRESTO is evaluated as a proof of concept, not a validated prediction method.

- **Synthetic domains** (nested CV, non-autoregressive SDLC features): R² = 0.108–0.620; a
  target-correlation ablation shows this is largely recovery of the generator's specified structure.
- **Mozilla Perfherder** (primary): autoregressive persistence on a real production-performance
  signal, R² = 0.17–0.92.
- **SQuaD** (primary): CVE-count R² = 0.23; static-analysis-enriched defect-fix R² = 0.50.
- **GHALogs**: R² = 0.113 (Gradient Boosting, 95% CI [0.050, 0.356]), n = 28,443 repositories.
- **TravisTorrent**: build-duration target, per-project chronological split, nested-CV selection;
  see `real-data/travistorrent/TRAVISTORRENT_NESTED_SELECTION_EVIDENCE.md`.

Confidence intervals are wide throughout, and most remaining comparisons include zero.

## Evidence files

Each reported result is documented by a per-analysis evidence file (the list cited in the
manuscript's Data Availability Statement):

| File | Location |
|---|---|
| `AR_ACF_DIAGNOSTICS_EVIDENCE.md` | `code/synthetic_data_generator/` |
| `BLOCK_BOOTSTRAP_EVIDENCE.md` | `code/synthetic_data_generator/` |
| `GHALOGS_ABLATION_EVIDENCE.md` | `code/synthetic_data_generator/` |
| `M3_NESTED_CV_TUNING_EVIDENCE.md` | `code/synthetic_data_generator/` |
| `M8_SIEGMUND_BASELINE_RESULTS.md` | `code/synthetic_data_generator/` |
| `M9_SYSTEM_AVAILABILITY_ABLATION_EVIDENCE.md` | `code/synthetic_data_generator/` |
| `NESTED_MODEL_SELECTION_EVIDENCE.md` | `code/synthetic_data_generator/` |
| `PA_RFE_NESTED_SELECTION_EVIDENCE.md` | `code/synthetic_data_generator/` |
| `R1_BOOTSTRAP_AND_ABLATION_EVIDENCE.md` | `code/synthetic_data_generator/` |
| `R2_LAG_SHIFT_FIX_EVIDENCE.md` | `code/synthetic_data_generator/` |
| `PAIRED_DIFFERENCE_BOOTSTRAP_EVIDENCE.md` | `real-data/` |
| `PERFHERDER_BLOCK_BOOTSTRAP_EVIDENCE.md` | `real-data/mozilla-perfherder/` |
| `PERFHERDER_NESTED_SELECTION_EVIDENCE.md` | `real-data/mozilla-perfherder/` |
| `SQUAD_NESTED_SELECTION_EVIDENCE.md` | `real-data/squad/` |
| `TRAVISTORRENT_BLOCK_BOOTSTRAP_EVIDENCE.md` | `real-data/travistorrent/` |
| `TRAVISTORRENT_NESTED_SELECTION_EVIDENCE.md` | `real-data/travistorrent/` |

## Reproducing the paper's numbers

1. `code/synthetic_data_generator/requirements.txt` — Python environment (`.venv` not included;
   recreate locally with `python -m venv .venv && pip install -r requirements.txt`).
   `ENVIRONMENT.txt` in the same folder records the pinned versions (Python 3.14.5,
   scikit-learn 1.9.0, pandas 3.0.5, numpy 2.5.2, scipy 1.18.0). Random seed 42 throughout.
2. Regenerate the synthetic domains: `python generate.py` (see `config/domain_profiles.yaml`),
   or use the pre-generated CSVs already in `synthetic-data-projects/`.
3. Run `python run_pipeline.py <domain>` for the model training/evaluation that produces each
   domain's `ml_results.md`.
4. Nested-CV model selection and robustness analyses (all in `code/synthetic_data_generator/`):
   `m10_nested_model_selection.py` (shared harness: `nested_cv_harness.py`),
   `m11_block_bootstrap.py`, `m12_ar_acf_diagnostics.py`, `m13_pa_rfe_nested.py`,
   `m3_nested_cv_tuning.py`, `m8_siegmund_baseline.py`, `m9_system_availability_ablation.py`,
   `r1_analysis.py`. Each has a companion evidence file (table above).
5. For each real-world dataset in `real-data/<source>/`: follow that folder's `DOWNLOAD.md` to
   fetch the raw data, then run its `run_pipeline_<source>.py`, followed by its
   `*_nested_selection.py` / `*_block_bootstrap.py` scripts where present. (SQuaD's required files
   are already included — no download step needed there.) Then run
   `real-data/bootstrap_real_world_ci.py` and `real-data/paired_difference_bootstrap.py`.
6. Figures: `generate_figures_v6.py` and `generate_figures_v6_from_tables.py` produce the v6
   manuscript figures into `paper/images/` (override with `PRESTO_FIG_DIR=<dir>`).
   `generate_figures.py`, `generate_figures_v4.py`, and the `regenerate_fig*.py` scripts are kept
   for provenance of earlier revisions.

**Known limitation:** several analysis scripts still contain absolute paths from the authors'
machine (`/Volumes/4TB/...`); adjust the path constants at the top of each script to your clone
location before running.

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
- **`paper/author-photos/`** — MDPI-required headshots for the "Short Biography of Authors"
  section; no scientific/data value (the LaTeX source references them, so add your own or comment
  those lines out to compile).
- **Response-to-reviewer letters** — part of the confidential review process, not the compendium.
- **LaTeX build artifacts** (`.aux/.log/.out/.blg`) — regenerated on compile.

## Licensing

- **Data** (`real-data/`, `synthetic-data-projects/`, `samples/`): CC-BY-4.0, matching the license
  of the re-derived third-party sources (Mozilla Perfherder CC-BY-4.0, GHALogs CC-BY-SA-4.0,
  SQuaD CC-BY-4.0; TravisTorrent CC-BY-4.0 via its Figshare mirror).
- **Code** (`code/`): MIT (see `code/LICENSE`).
- **Paper** (`paper/`): all rights reserved pending journal publication — do not redistribute the
  PDF beyond the preprint/Zenodo copy without checking the eventual MDPI copyright agreement.

## Citing

See `CITATION.cff` (GitHub renders a "Cite this repository" button from it). Concept DOI for all
versions: [10.5281/zenodo.22005438](https://doi.org/10.5281/zenodo.22005438). Once the paper has
a DOI, add it to `.zenodo.json`'s `related_identifiers` (relation `isSupplementTo`), to
`CITATION.cff`'s `preferred-citation`, and to this README.
