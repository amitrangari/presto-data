# R2 fix evidence: rolling-window same-row leakage in `add_rolling_features()`

**Date:** 2026-08-09
**Item:** Phase 1 / R2 in `presto/paper-work/review/2026-08-08_review/ACTION_PLAN.md` — "Resolve the
lag-shift ambiguity first."

## The bug

`run_pipeline.py::add_rolling_features()` computed rolling statistics directly on the raw series:

```python
roll = df_out[metric].rolling(window=window, min_periods=1)   # BEFORE (buggy)
```

Pandas' `.rolling()` is trailing and **inclusive of the current row** by default. For
`System Uptime (%)` — simultaneously the regression target and one of `ROLLING_METRICS` — this
means `System Uptime (%)_rolling_mean_3` at release *i* was `mean(uptime[i-2], uptime[i-1],
uptime[i])`: it literally contained the value being predicted at that same row. This is same-row
data leakage, not temporal autocorrelation, and is a categorically different (and more severe)
problem than the lag features, which were already correct:

```python
df_out[f"{metric}_lag_{lag}"] = df_out[metric].shift(lag)      # already correct, lag >= 1
```

Of the paper's "32 target-derived features," **20 were the broken unshifted rolling stats**
(mean/std/min/max/cv × windows {3,5,7,10}) and **12 were the correctly-shifted lag/diff/pct_change
features** (steps {1,2,3,5}).

## The fix

```python
shifted = df_out[metric].shift(1)                               # AFTER (fixed)
for window in ROLLING_WINDOWS:
    roll = shifted.rolling(window=window, min_periods=1)
```

Rolling stats are now computed on the series shifted by 1 period first, so every `rolling_*`
feature summarizes only strictly-prior releases. (A second, unrelated fix was needed to even run
this on current pandas: `fillna(method="ffill")` → `.ffill()`, since `method=` was removed in
pandas 3.x.)

## Controlled before/after comparison

Same freshly-generated copula data (seeds unchanged: 42/ABC Cloud, 123/XYZ Sales, 456/Card
Payment), same train/test split, only the rolling-window shift changed. "WITH target-derived
features" condition (273 features), holdout R²:

| Domain | Model | Buggy (unshifted) | Fixed (shifted) | Δ |
|---|---|---:|---:|---:|
| ABC Cloud Provider | Linear Regression | 0.2825 | -0.2559 | -0.5384 |
| ABC Cloud Provider | Ridge Regression | 0.3199 | -0.1937 | -0.5136 |
| ABC Cloud Provider | Lasso Regression | 0.1288 | 0.1288 | 0.0000 |
| ABC Cloud Provider | **Random Forest** | **0.9448** | **0.9501** | **+0.0053** |
| ABC Cloud Provider | Gradient Boosting | 0.8498 | 0.8655 | +0.0157 |
| Card Payment Processor | Linear Regression | 0.7618 | 0.4277 | -0.3341 |
| Card Payment Processor | Ridge Regression | 0.7784 | 0.4935 | -0.2849 |
| Card Payment Processor | Lasso Regression | 0.3696 | 0.3615 | -0.0081 |
| Card Payment Processor | Random Forest | 0.8421 | 0.7867 | -0.0554 |
| Card Payment Processor | Gradient Boosting | 0.7244 | 0.6518 | -0.0726 |
| XYZ Sales Force | Linear Regression | 0.6508 | -1.0283 | -1.6791 |
| XYZ Sales Force | Ridge Regression | 0.7037 | -0.7381 | -1.4418 |
| XYZ Sales Force | Lasso Regression | 0.0421 | 0.0121 | -0.0300 |
| XYZ Sales Force | Random Forest | 0.9745 | 0.9707 | -0.0038 |
| XYZ Sales Force | Gradient Boosting | 0.2935 | 0.0449 | -0.2486 |

## Interpretation

1. **The paper's headline number (Random Forest, ABC Cloud Provider, R²=0.946) was not primarily an
   artifact of the leakage bug.** Buggy 0.9448 vs. fixed 0.9501 — the fix barely moves it, and moves
   it *up*, not down. Random Forest's reliance on the properly-shifted lag features alone is enough
   to reproduce the original headline figure. This validates (rather than undermines) the paper's
   core claim that System Uptime carries strong short-term persistence.
2. **Linear/Ridge/Gradient Boosting are far more sensitive to the bug**, and the direction is
   domain-dependent — XYZ Sales Force's Linear/Ridge results flip from strongly positive
   (R²≈0.65–0.70) to strongly negative (R²≈ -0.74 to -1.03) once same-row leakage is removed. This
   means any claim that used a non-Random-Forest model's "with-leakage" R² (or that used
   best-of-5-models selection under the buggy condition) was potentially reporting an artifact.
3. **Practical implication for the manuscript:** the "target leakage" framing for the shifted lag
   features (12 of 32) should be relabeled "autoregressive (AR) features" — they are legitimate,
   not leakage, per the consensus review's requested renaming. The unshifted rolling features (20 of
   32) were genuine leakage and are now fixed; their corrected contribution is reflected in the
   updated `ml_results.md` per domain (this directory's sibling `output/<domain>/ml_results.md` and
   the canonical copies in `research-data/presto/synthetic-data-projects/<domain>/ml_results.md`).
4. All "WITHOUT target-derived features" (241-feature, no leakage) numbers were already computed
   correctly in both versions — they exclude all 32 target-derived columns regardless of how those
   columns were computed, so `prepare_features(exclude_leakage=True)` output is unaffected by this
   bug. Only the "WITH" condition and any table/figure/CI that includes target-derived features
   changes.

## Updated corrected headline numbers (fixed code, final, cross-domain)

| Domain | Best model (with target features) | Holdout R² (with) | Best model (without) | Holdout R² (without) |
|---|---|---:|---|---:|
| ABC Cloud Provider | Random Forest | 0.9501 | Random Forest | 0.2683 |
| Card Payment Processor | Random Forest | 0.7867 | Lasso Regression | 0.3615 |
| XYZ Sales Force | Random Forest | 0.9707 | Random Forest | 0.2546 |

Full per-model, per-domain tables (CV R², holdout R²/MAE/RMSE, feature importances) are in
`../../synthetic-data-projects/<domain>/ml_results.md`.

## Not yet done

- Manuscript text (`presto/paper-work/overleaf/main_mdpi.tex`) still contains the old
  pre-fix numbers (0.946/0.269, 71%/54%) throughout the Abstract, §4.10, RQ1/RQ4 conclusions, and
  Tables 4/5/7/9/10/11. These need a full pass once real-data results are also available, so the
  manuscript is updated once rather than twice.
- The bootstrap 95% CIs and target-correlation ablation requested by R1 have not been run yet —
  R1 is next in the dependency order per the consensus review.

## Addendum (2026-08-09): a second, distinct leakage mode found via real-data validation

While building the Perfherder real-data adapter (`../../real-data/mozilla-perfherder/run_pipeline_perfherder.py`),
running the *same* lag-feature construction (`value_lag_k`, `value_diff_k`, `value_pct_change_k`)
against a real signature with n=3548 >> p=32 (well-determined, unlike the synthetic pipeline's
n≈136 < p=273 regime) produced **Holdout R²=1.0000 exactly** for Linear/Ridge Regression.

**Cause:** `value_diff_k = value - value_lag_k` is an exact algebraic identity, so
`value = value_lag_k + value_diff_k`. Including both `lag_k` and `diff_k` as separate features
lets any linear model reconstruct the target with zero error by setting coef=1 on each — not a
statistical fit, a tautology. This is a distinct, more fundamental issue than the rolling-window
shift bug fixed above.

**Why this didn't surface in the synthetic pipeline's reported numbers:** there, n<p (rank
deficient), so `LinearRegression`'s minimum-norm least-squares solution does not converge to the
clean identity solution — it spreads weight across many collinear columns instead, which is
unstable and generalizes poorly (this is exactly what the manuscript's own text already attributes
the linear models' catastrophic failure to: "OLS selects the minimum-norm solution, which
extrapolates wildly on test data"). So the synthetic numbers are not invalidated by this, but the
same latent redundancy is a contributing factor to that instability, and the same construction
(`add_lag_features` in `run_pipeline.py`) would produce a trivial R²=1.0 if ever run with n>p (e.g.,
a bigger synthetic dataset, or an isolated "AR-features-only" ablation with enough samples).

**Fix applied (real-data adapter only, so far):** dropped `diff_k` and `pct_change_k`, keeping only
`lag_k` (+ rolling stats, which are not exactly invertible to the current value the way diff is).
Corrected real-data results: Holdout R² 0.17–0.91 across 3 signatures (genuine, not tautological).

**Not yet done:** the original `run_pipeline.py` (synthetic pipeline) still computes
`diff_k`/`pct_change_k` alongside `lag_k`. It should get the same fix as part of the R1 ablation
work (Priority-0, not yet started), since R1's bootstrap-CI and correlation-ablation work will
likely include isolated-feature-subset evaluations where this redundancy could resurface.

## Addendum 2 (2026-08-09): regeneration environment differs from the paper's stated Methods

The 2026-08-09 regeneration (this fix + fresh synthetic data + real-data validation work) ran under
Python 3.14.5 / numpy 2.5.1 / scipy 1.18.0 / pandas 3.0.5 / scikit-learn 1.9.0 (see `ENVIRONMENT.txt`
in this directory for the full pinned list). The manuscript's Methods section states
Python 3.10.12 / scikit-learn 1.3.0 — a substantial version gap, and the exact original numpy/scipy
versions were never recorded anywhere (this is itself R7's flagged inconsistency).

**Consequence:** even with `RandomForestRegressor`/`GradientBoostingRegressor` hyperparameters
explicitly pinned in code (n_estimators, max_depth, etc. are NOT left at version-drifted defaults),
the copula generator's `scipy.stats` sampling calls are not guaranteed bit-identical across scipy
major versions for the same seed — internal sampling algorithms change between releases. This
regeneration's "WITHOUT target-derived features" numbers (which are provably unaffected by the R2
rolling-window fix — see above) still differ non-trivially from the manuscript's original figures
(e.g., ABC Cloud Provider's best without-AR-features model was originally reported as Gradient
Boosting R²=0.387; this regeneration gets Random Forest R²=0.2683, Gradient Boosting R²=0.2509).
This is not a new bug — it is direct empirical evidence for why R7 requires the reproducibility
package to pin *exact* library versions, not just Python and scikit-learn. Treat this regeneration's
numbers as the new authoritative baseline going forward (deposited alongside `ENVIRONMENT.txt`), not
as a patch on top of the original submitted numbers, which can no longer be exactly reproduced
without the original (never-recorded) numpy/scipy versions.
