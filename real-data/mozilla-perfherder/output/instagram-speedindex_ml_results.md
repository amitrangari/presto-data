# ML Pipeline Results: instagram-speedindex (Mozilla Perfherder, real data)

**Signature:** Instagram Perceptual Speed Index (ms), opt/fission/warm/webrender (signature_id=3870280)

## Dataset Characteristics

| Property | Value |
|---|---|
| Samples (pushes) | 3177 |
| Target-derived (AR) features | 24 |
| Process-side features (non-AR) | 5 |
| Target mean | 327.0966 |
| Target std | 49.6859 |

## Model Performance (WITH target-derived AR features)

| Model | CV R2 (mean +/- std) | Holdout R2 | Holdout MAE | Holdout RMSE |
|---|---|---|---|---|
| Ridge Regression | 0.0634 +/- 0.2187 | 0.9127 | 17.7526 | 28.1805 |
| Linear Regression | 0.0370 +/- 0.1665 | 0.8798 | 18.1993 | 33.0640 |
| Lasso Regression | 0.0150 +/- 0.2142 | 0.8267 | 26.4464 | 39.6957 |
| Random Forest | -0.0974 +/- 0.2695 | 0.0243 | 57.0659 | 94.1970 |
| Gradient Boosting | -0.1675 +/- 0.3132 | -0.0595 | 58.9820 | 98.1584 |

## Model Performance (WITHOUT target-derived features -- alert-history + push-gap only)

| Model | CV R2 (mean +/- std) | Holdout R2 | Holdout MAE | Holdout RMSE |
|---|---|---|---|---|
| Gradient Boosting | -0.3739 +/- 0.3066 | -0.3669 | 66.2926 | 111.4919 |
| Linear Regression | -0.3031 +/- 0.2693 | -0.3669 | 66.2546 | 111.4940 |
| Ridge Regression | -0.3031 +/- 0.2693 | -0.3669 | 66.2546 | 111.4940 |
| Lasso Regression | -0.3018 +/- 0.2665 | -0.3719 | 66.3597 | 111.6979 |
| Random Forest | -0.7407 +/- 0.4220 | -0.3741 | 67.2946 | 111.7871 |

## Notes

- Real Mozilla Perfherder data (CC-BY-4.0), not synthetic.
- Rolling/lag features use the corrected shift (see ../../code/synthetic_data_generator/R2_LAG_SHIFT_FIX_EVIDENCE.md) -- no same-row leakage.
- 'WITHOUT target-derived' features are alert-history + inter-push time gap only -- Perfherder has no SDLC process-metric analog to PRESTO's 241 synthetic features, so this is a much weaker non-AR feature set than the synthetic domains have.
- 80/20 temporal split, 5-fold (or fewer, data permitting) TimeSeriesSplit CV, StandardScaler fit on train only.
