# Downloading the GHALogs raw data

This folder ships only the pipeline/feature-extraction scripts and result docs. The raw dataset
is **not** bundled here — fetch it from the original Zenodo deposit:

- **Source:** Zenodo, `doi:10.5281/zenodo.10154920` — "GHALogs: Large-Scale Dataset of GitHub
  Actions Runs" (MSR 2025). License: **CC-BY-SA-4.0** (attribution + share-alike — any dataset
  derived from this and republished must also be CC-BY-SA-4.0).
- **Files needed:** `runs.json.gz` (~1.06GB) and `repositories.json.gz` (~69MB). The dataset also
  offers a `github_run_logs.zip` (~142GB) full log archive — **not needed** for the release-level
  build/test timing analysis this paper uses; skip it.

```bash
# From the record page (https://zenodo.org/records/10154920), download runs.json.gz and
# repositories.json.gz into this directory. Zenodo file URLs are stable and follow the pattern:
curl -L -o runs.json.gz "https://zenodo.org/records/10154920/files/runs.json.gz?download=1"
curl -L -o repositories.json.gz "https://zenodo.org/records/10154920/files/repositories.json.gz?download=1"
```

Then regenerate the feature table the pipeline actually reads:

```bash
python extract_run_features.py   # produces run_features.csv from runs.json.gz
python run_pipeline_ghalogs.py   # reproduces output_ghalogs_ml_results.md
```

**Scale:** 116k workflows, 513k runs, 2.3M steps, across 25k public repos, 20 languages.
