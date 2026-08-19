# Downloading the TravisTorrent raw data

This folder ships only the adapter/analysis scripts and result docs. The raw dataset (~4GB) is
**not** bundled here — fetch it from the maintainers' canonical mirror:

- **Source:** Figshare, `doi:10.6084/m9.figshare.19314170` (CC-BY-4.0). This is TravisTorrent's own
  designated permanent mirror — the original `travistorrent.testroots.org` domain has expired.
- **File needed:** `final-2017-01-25.csv.gz` (~252MB compressed, 3,881,993 rows)

```bash
# From the Figshare record page (https://doi.org/10.6084/m9.figshare.19314170), download
# final-2017-01-25.csv.gz into this directory. Figshare's download links are per-file and
# change per version, so grab the URL from the record page rather than hardcoding one here.
gunzip -k final-2017-01-25.csv.gz   # -k keeps the .gz; only decompress if you need the plain CSV
```

## Reproducing `seven_projects.csv`

The pipeline (`run_pipeline_travistorrent.py`) reads a pre-filtered `seven_projects.csv` — the
same 7 projects the manuscript names: `DataDog/dd-agent`, `bundler/bundler`, `getsentry/sentry`,
`gonum/matrix`, `mongodb/mongoid`, `rg3/youtube-dl`, `rspec/rspec-core`. Regenerate it with:

```python
import pandas as pd

PROJECTS = ["DataDog/dd-agent", "bundler/bundler", "getsentry/sentry", "gonum/matrix",
            "mongodb/mongoid", "rg3/youtube-dl", "rspec/rspec-core"]

df = pd.read_csv("final-2017-01-25.csv.gz", compression="gzip", low_memory=False)
df[df["gh_project_name"].isin(PROJECTS)].to_csv("seven_projects.csv", index=False)
```

This should yield 393,924 rows. Then run `python run_pipeline_travistorrent.py` as normal.
