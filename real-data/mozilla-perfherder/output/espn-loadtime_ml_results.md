# ML Pipeline Results: espn-loadtime (Mozilla Perfherder, real data)

**Signature:** ESPN.com page load time (ms), opt/fission/warm/webrender (signature_id=3777843)

## Dataset Characteristics

| Property | Value |
|---|---|
| Samples (pushes) | 3548 |
| Target-derived (AR) features | 24 |
| Process-side features (non-AR) | 5 |
| Target mean | 723.6688 |
| Target std | 31.8592 |

## Model Performance (WITH target-derived AR features)

| Model | CV R2 (mean +/- std) | Holdout R2 | Holdout MAE | Holdout RMSE |
|---|---|---|---|---|
| Ridge Regression | 0.0075 +/- 0.1868 | 0.5735 | 12.0060 | 16.7535 |
| Linear Regression | -0.0294 +/- 0.2312 | 0.5719 | 12.0376 | 16.7840 |
| Lasso Regression | -0.1006 +/- 0.3491 | 0.5719 | 12.1100 | 16.7841 |
| Random Forest | -1.2880 +/- 1.7817 | 0.1971 | 17.8232 | 22.9860 |
| Gradient Boosting | -2.0212 +/- 3.1031 | 0.1516 | 17.9138 | 23.6287 |

## Model Performance (WITHOUT target-derived features -- alert-history + push-gap only)

| Model | CV R2 (mean +/- std) | Holdout R2 | Holdout MAE | Holdout RMSE |
|---|---|---|---|---|
| Linear Regression | -4.0893 +/- 3.0521 | -3.1908 | 46.3074 | 52.5147 |
| Ridge Regression | -4.0893 +/- 3.0521 | -3.1908 | 46.3074 | 52.5147 |
| Lasso Regression | -4.0905 +/- 3.0557 | -3.1973 | 46.3456 | 52.5555 |
| Gradient Boosting | -4.1700 +/- 3.0282 | -3.2209 | 46.4609 | 52.7030 |
| Random Forest | -5.3025 +/- 2.7235 | -3.6466 | 47.9240 | 55.2968 |

## Notes

- Real Mozilla Perfherder data (CC-BY-4.0), not synthetic.
- Rolling/lag features use the corrected shift (see ../../code/synthetic_data_generator/R2_LAG_SHIFT_FIX_EVIDENCE.md) -- no same-row leakage.
- 'WITHOUT target-derived' features are alert-history + inter-push time gap only -- Perfherder has no SDLC process-metric analog to PRESTO's 241 synthetic features, so this is a much weaker non-AR feature set than the synthetic domains have.
- 80/20 temporal split, 5-fold (or fewer, data permitting) TimeSeriesSplit CV, StandardScaler fit on train only.
