# PRESTO methodology applied to real Mozilla Perfherder data

**Code:** `run_pipeline_perfherder.py`. **Results:** `output/<signature>_ml_results.md`.

## What this validates (and what it doesn't)

Perfherder gives one real thing PRESTO's synthetic domains can only simulate: a genuine
production-facing runtime performance measurement (page-load time / speed index) collected over
thousands of real pushes. It does **not** give the other half of PRESTO's story — there are no
upstream SDLC process metrics (requirements, code quality, build/test metrics) joined to these
pushes, only the performance value itself, test/platform metadata (constant per signature), and
sparse regression-alert flags. So this validation exercises the **feature-engineering + model-
comparison methodology** (same corrected shift logic, same 5 models, same evaluation protocol as
`run_pipeline.py`) against a real target, not the "SDLC metrics predict performance" claim itself.

## Data sources -> feature engineering -> model comparison -> results

1. **Data source:** 3 curated (alert-flagged, i.e. Mozilla's own performance sheriffs confirmed
   them as real signals) signatures, chosen for size and diversity: ESPN load time (3548 pushes),
   Instagram Perceptual Speed Index (3177), NYTimes Perceptual Speed Index (3225). All CC-BY-4.0.
2. **Feature engineering:** rolling stats (mean/std/min/max/cv, windows 3/5/7/10, shifted by 1 —
   the R2 fix) and lag features (steps 1/2/3/5) of the target's own history, plus lagged
   alert-history flags and inter-push time gap. **Deliberately excludes** `diff_k`/`pct_change_k`
   alongside `lag_k` — see the addendum in `../../code/synthetic_data_generator/R2_LAG_SHIFT_FIX_EVIDENCE.md`
   for why that combination is a second, distinct leakage mode (an exact algebraic identity) that
   surfaces here (n>>p) but stayed hidden in the synthetic pipeline (n<p).
3. **Model comparison:** same 5 algorithms (Linear, Ridge, Lasso, Random Forest, Gradient
   Boosting), 80/20 temporal split, TimeSeriesSplit CV, StandardScaler fit on train only.
4. **Results:**

| Signature | Best model (with AR features) | Holdout R² (with) | Holdout R² (without — alert-history/time-gap only) |
|---|---|---:|---:|
| ESPN load time | Ridge Regression | 0.5735 | -3.1908 |
| Instagram speed index | Ridge Regression | 0.9127 | -0.3669 |
| NYTimes speed index | Ridge Regression | 0.1666 | -3.5633 |

## Interpretation for the paper

- **Genuine autoregressive signal on real data, at a magnitude consistent with the synthetic
  pipeline's own findings**: real production performance metrics are strongly, though variably,
  predictable from their own recent history (R² 0.17–0.91 across 3 unrelated real signatures) —
  the same phenomenon PRESTO documents for System Uptime in the synthetic domains, now confirmed on
  real data with real noise, real regressions, and no copula-prior construction to fall back on.
- **Without historical values, there is nothing to predict from** — R² collapses to strongly
  negative across every model and every signature. This is *not* a failure of the methodology; it
  is the expected consequence of Perfherder having no SDLC process-metric analog to PRESTO's 241
  synthetic features. It sharpens (rather than undermines) the paper's own point: a full real
  8-phase dataset remains the missing piece, and this real-data check is offered as a partial,
  honest substitute — validating the *pipeline*, not yet the *SDLC-features claim*.
- Model ranking differs from the synthetic domains: Ridge (not Random Forest) wins here. Worth a
  sentence in Discussion — plausibly because with only 24 AR features and thousands of samples
  (n>>p, unlike the synthetic 273-feature/136-sample regime), linear models are well-conditioned
  and Random Forest/Gradient Boosting's advantage in high-dimensional, small-n, non-linear settings
  doesn't apply here.
