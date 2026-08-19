# Downloading the Mozilla Perfherder raw data

This folder ships only the pipeline scripts, the original replication package's own
extraction/transform tooling (`scripts/`), and result docs. The raw dataset (~4.8GB: 5,655
per-signature timeseries CSVs plus alerts/bugs tables) is **not** bundled here.

- **Source:** Zenodo, `doi:10.5281/zenodo.14642238` — the original Perfherder replication
  package this paper's real-world validation is derived from. License: CC-BY-4.0.
- **Files needed:** `alerts_data.csv`, `bugs_data.csv`, and the `timeseries-data/` tree (one CSV
  per performance signature, organized by repository — see `scripts/README.md` for the exact
  layout).

## Two ways to get the data

1. **Download the static snapshot** from the Zenodo record above (matches what this paper used,
   extracted May 2023 – May 2024).
2. **Re-extract fresh data** using the original authors' own tooling in `scripts/` (pulls
   directly from Mozilla's [Treeherder API](https://treeherder.mozilla.org/docs/)):
   ```bash
   cd scripts
   pip install -r requirements.txt
   python extract-alerts.py        # -> alerts_data.csv
   python extract-bugs-api.py      # -> bugs_data.csv (run after alerts)
   python extract-timeseries.py    # -> timeseries-data/ (run back-to-back with step 1, see scripts/README.md)
   ```
   Re-extracting gets you *current* data, not the exact snapshot this paper's numbers were
   computed from — use the Zenodo snapshot if you need to reproduce the paper's exact results.

Once `alerts_data.csv`, `bugs_data.csv`, and `timeseries-data/` are in place, run
`python run_pipeline_perfherder.py` (and `run_pipeline_perfherder_bugs.py` for the bug-enrichment
variant) to reproduce `output/*_ml_results.md`.
