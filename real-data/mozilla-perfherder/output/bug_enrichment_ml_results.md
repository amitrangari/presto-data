# ML Pipeline Results: Bug-Metadata Enrichment (Mozilla Perfherder, real data)

**Question:** does enriching the non-AR ("WITHOUT target-derived features") condition from `run_pipeline_perfherder.py` with real Bugzilla triage metadata (severity, priority, comment_count from `bugs_data.csv`, joined via `alert_summary_bug_number`) improve on a bare alert-flag baseline?

Signature note: the three original AR-comparison signatures (espn-loadtime, instagram-speedindex, nytimes-speedindex) each have only 0-2 bug-linked alerts in the full alerts history -- too sparse for this question. Ran instead on the two signatures with the richest bug-linked alert history among downloaded timeseries data.

## installer-size-osx-cross (Installer size (bytes), osx-cross, autoland4)

Samples (pushes): 17217, bug-linked alert rows: 23

### Alert-flag-only baseline

| Model | CV R2 | Holdout R2 | Holdout MAE | Holdout RMSE |
|---|---|---|---|---|
| Ridge Regression | -58.4404+/-52.2164 | -56.0633 | 5957930.25 | 6011000.52 |
| Linear Regression | -58.4404+/-52.2164 | -56.0633 | 5957930.33 | 6011000.63 |
| Lasso Regression | -58.4404+/-52.2164 | -56.0633 | 5957930.44 | 6011000.72 |
| Gradient Boosting | -54.6005+/-45.4225 | -58.3404 | 6049591.21 | 6129763.10 |
| Random Forest | -58.6452+/-48.0874 | -60.8325 | 6065943.97 | 6257154.46 |

### Bug-metadata-enriched

| Model | CV R2 | Holdout R2 | Holdout MAE | Holdout RMSE |
|---|---|---|---|---|
| Lasso Regression | -11.4411+/-12.6768 | -2.5617 | 1183497.12 | 1501746.58 |
| Ridge Regression | -11.2728+/-12.7195 | -3.3428 | 1304588.27 | 1658255.69 |
| Linear Regression | -11.3099+/-12.8610 | -3.8093 | 1374029.68 | 1745049.75 |
| Random Forest | -3.5141+/-3.0085 | -4.3084 | 1615394.20 | 1833364.74 |
| Gradient Boosting | -4.0141+/-3.1827 | -4.3313 | 1626564.32 | 1837315.80 |

Best holdout R2: baseline=-56.0633 (Ridge Regression) vs. bug-enriched=-2.5617 (Lasso Regression); delta=+53.5016

## build-metric-osx-aarch64 (Build metric, osx-aarch64-shippable, autoland4)

Samples (pushes): 11119, bug-linked alert rows: 11

### Alert-flag-only baseline

| Model | CV R2 | Holdout R2 | Holdout MAE | Holdout RMSE |
|---|---|---|---|---|
| Lasso Regression | -34.7805+/-47.0722 | -41.3056 | 4767237.73 | 4826590.19 |
| Linear Regression | -34.7805+/-47.0722 | -41.3056 | 4767237.77 | 4826590.31 |
| Ridge Regression | -34.7803+/-47.0722 | -41.3056 | 4767238.47 | 4826590.69 |
| Gradient Boosting | -33.4790+/-41.8043 | -42.1504 | 4795556.09 | 4874541.75 |
| Random Forest | -50.4321+/-46.9167 | -44.7731 | 4819781.62 | 5020496.80 |

### Bug-metadata-enriched

| Model | CV R2 | Holdout R2 | Holdout MAE | Holdout RMSE |
|---|---|---|---|---|
| Lasso Regression | -6.9145+/-6.1988 | -1.5675 | 978305.19 | 1189044.44 |
| Ridge Regression | -6.9145+/-6.0631 | -1.5866 | 978573.91 | 1193452.98 |
| Linear Regression | -6.2349+/-6.3872 | -1.5990 | 978064.31 | 1196323.91 |
| Gradient Boosting | -7.1542+/-6.9770 | -19.2297 | 2940530.81 | 3337613.62 |
| Random Forest | -20.3394+/-32.9470 | -19.2488 | 2934778.10 | 3339186.29 |

Best holdout R2: baseline=-41.3056 (Lasso Regression) vs. bug-enriched=-1.5675 (Lasso Regression); delta=+39.7381

## Notes

- Real Mozilla Perfherder + Bugzilla data (CC-BY-4.0). Severity mapped S1=4..S4=1, priority P1=5..P5=1, unset/"--" = 0.
- All bug-metadata features are lagged or built from `.shift(1)`-then-cumulative history, so no row uses its own or a future push's bug outcome -- no look-ahead leakage.
- 80/20 temporal split, TimeSeriesSplit CV, StandardScaler fit on train only -- same protocol as `run_pipeline_perfherder.py`.
