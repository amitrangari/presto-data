# ML Pipeline Results: nytimes-speedindex (Mozilla Perfherder, real data)

**Signature:** NYTimes Perceptual Speed Index (ms), opt/fission/warm/webrender (signature_id=3778095)

## Dataset Characteristics

| Property | Value |
|---|---|
| Samples (pushes) | 3225 |
| Target-derived (AR) features | 24 |
| Process-side features (non-AR) | 5 |
| Target mean | 361.2882 |
| Target std | 19.3880 |

## Model Performance (WITH target-derived AR features)

| Model | CV R2 (mean +/- std) | Holdout R2 | Holdout MAE | Holdout RMSE |
|---|---|---|---|---|
| Ridge Regression | 0.2122 +/- 0.2517 | 0.1666 | 5.8633 | 7.9557 |
| Linear Regression | 0.2057 +/- 0.2558 | 0.1659 | 5.8782 | 7.9590 |
| Lasso Regression | 0.1006 +/- 0.1473 | 0.1576 | 5.8113 | 7.9985 |
| Gradient Boosting | -0.6654 +/- 1.0291 | 0.1338 | 5.9805 | 8.1109 |
| Random Forest | -0.5647 +/- 0.8501 | 0.1128 | 6.1426 | 8.2085 |

## Model Performance (WITHOUT target-derived features -- alert-history + push-gap only)

| Model | CV R2 (mean +/- std) | Holdout R2 | Holdout MAE | Holdout RMSE |
|---|---|---|---|---|
| Lasso Regression | -13.9622 +/- 7.5158 | -3.5130 | 16.3873 | 18.5130 |
| Ridge Regression | -14.0751 +/- 7.6539 | -3.5633 | 16.4885 | 18.6160 |
| Linear Regression | -14.0753 +/- 7.6541 | -3.5633 | 16.4886 | 18.6160 |
| Gradient Boosting | -14.4033 +/- 8.0267 | -4.0480 | 17.1524 | 19.5797 |
| Random Forest | -18.4191 +/- 9.5921 | -6.7661 | 18.8211 | 24.2856 |

## Notes

- Real Mozilla Perfherder data (CC-BY-4.0), not synthetic.
- Rolling/lag features use the corrected shift (see ../../code/synthetic_data_generator/R2_LAG_SHIFT_FIX_EVIDENCE.md) -- no same-row leakage.
- 'WITHOUT target-derived' features are alert-history + inter-push time gap only -- Perfherder has no SDLC process-metric analog to PRESTO's 241 synthetic features, so this is a much weaker non-AR feature set than the synthetic domains have.
- 80/20 temporal split, 5-fold (or fewer, data permitting) TimeSeriesSplit CV, StandardScaler fit on train only.
