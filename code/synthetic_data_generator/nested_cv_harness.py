#!/usr/bin/env python3
"""Shared nested-CV model-selection harness (v4 revision / Reviewer 2, round 3).

Generalizes `m3_nested_cv_tuning.py`'s existing pattern (nested TimeSeriesSplit CV for
Ridge/Lasso alpha only) to full ALGORITHM selection across all 5 candidate models (Linear,
Ridge, Lasso, Random Forest, Gradient Boosting), each tuned over its own hyperparameter grid,
nested inside the paper's existing 80/20 outer temporal split.

Why this exists: every "best model" claim in the paper (per domain, per AR-condition, per
real-world dataset) has so far been selected by picking whichever of the 5 candidates scores
highest on the SAME holdout partition the paper then reports that score on. The paper's own
Model-Selection Rule (Section 3.2.4) already discloses this as winner's-curse-biased. Reviewer
2's round-3 review rejected disclosure alone as insufficient and asked for the selection step
itself to be moved inside cross-validation, so the outer holdout is touched exactly once, by
the already-selected model, never used to choose among candidates.

Protocol:
  - Outer split: identical fixed 80/20 temporal split used throughout this paper (no shuffling;
    data is date-sorted).
  - Inner loop: for each of the 5 candidate algorithms, GridSearchCV with TimeSeriesSplit(5)
    *within the outer training set only* selects that algorithm's best hyperparameters and
    records its best inner-CV R^2. Linear Regression has no hyperparameters, so its "grid
    search" is a plain 5-fold TimeSeriesSplit CV score for comparability.
  - Selection: the algorithm+hyperparameters with the highest INNER-CV R^2 (never holdout R^2)
    is selected as "best."
  - The selected configuration is refit once on the full outer-training set and scored once on
    the untouched outer holdout -- that score is the only holdout R^2 that participates in any
    downstream claim.
  - For transparency, we also record what the OLD protocol (select directly by holdout R^2)
    would have picked, so the paper can show old-vs-new side by side rather than silently
    swapping numbers.

Hyperparameter grids (kept modest relative to ~136-170 total rows; a very large grid search
would itself risk overfitting the inner folds, some of which are as small as ~20-25 rows -- the
same small-fold problem the paper's existing CV-Holdout Discrepancy note already documents):
  - Ridge / Lasso: alpha, 19 log-spaced points in [1e-3, 1e6] (identical grid to
    `m3_nested_cv_tuning.py`, for direct comparability with that earlier analysis).
  - Random Forest: n_estimators in {50, 100, 200} x max_depth in {5, 10, None} x
    min_samples_split in {2, 5} (18 combinations); min_samples_leaf fixed at 2, matching the
    paper's existing fixed-hyperparameter RF elsewhere, to keep the grid a comparison of the
    dimensions most likely to matter rather than a full combinatorial sweep.
  - Gradient Boosting: n_estimators in {50, 100, 200} x max_depth in {3, 6, 9} x
    learning_rate in {0.05, 0.1, 0.2} (27 combinations).
  - Linear Regression: no hyperparameters.

Usage as a library:
    from nested_cv_harness import nested_select
    result = nested_select(X, y, verbose=True)
"""
from __future__ import annotations

import warnings
from typing import Dict

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

ALPHA_GRID = np.logspace(-3, 6, 19).tolist()  # identical to m3_nested_cv_tuning.py

RF_GRID = {
    "n_estimators": [50, 100, 200],
    "max_depth": [5, 10, None],
    "min_samples_split": [2, 5],
}
RF_FIXED = {"min_samples_leaf": 2, "random_state": 42}

GB_GRID = {
    "n_estimators": [50, 100, 200],
    "max_depth": [3, 6, 9],
    "learning_rate": [0.05, 0.1, 0.2],
}
GB_FIXED = {"min_samples_split": 5, "min_samples_leaf": 2, "random_state": 42}

CANDIDATES = {
    "Linear Regression": (LinearRegression, {}, {}),
    "Ridge Regression": (Ridge, {"alpha": ALPHA_GRID}, {}),
    "Lasso Regression": (Lasso, {"alpha": ALPHA_GRID}, {}),
    "Random Forest": (RandomForestRegressor, RF_GRID, RF_FIXED),
    "Gradient Boosting": (GradientBoostingRegressor, GB_GRID, GB_FIXED),
}

N_INNER_SPLITS = 5


def nested_select(
    X: pd.DataFrame,
    y: pd.Series,
    outer_split: float = 0.8,
    n_inner_splits: int = N_INNER_SPLITS,
    verbose: bool = False,
) -> Dict:
    """Nested model+hyperparameter selection across all 5 candidate algorithms.

    Returns a dict with per-candidate detail (inner CV R^2, selected hyperparameters, holdout
    R^2/MAE/RMSE for every candidate -- computed for transparency/comparison, not used for
    selection), plus the nested-selected winner and, separately, what the old fixed-holdout-
    selection protocol would have picked on the identical split.
    """
    split_idx = int(len(X) * outer_split)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    tscv = TimeSeriesSplit(n_splits=n_inner_splits)

    per_candidate: Dict[str, dict] = {}
    for name, (cls, grid, fixed_kwargs) in CANDIDATES.items():
        if grid:
            gs = GridSearchCV(cls(**fixed_kwargs), grid, cv=tscv, scoring="r2", n_jobs=1)
            gs.fit(X_train_s, y_train)
            best_params = gs.best_params_
            inner_cv_r2 = float(gs.best_score_)
        else:
            scores = []
            for tr_idx, val_idx in tscv.split(X_train_s):
                m = cls(**fixed_kwargs)
                m.fit(X_train_s[tr_idx], y_train.iloc[tr_idx])
                scores.append(r2_score(y_train.iloc[val_idx], m.predict(X_train_s[val_idx])))
            best_params = {}
            inner_cv_r2 = float(np.mean(scores))

        model = cls(**fixed_kwargs, **best_params)
        model.fit(X_train_s, y_train)
        y_pred = model.predict(X_test_s)
        holdout_r2 = float(r2_score(y_test, y_pred))
        holdout_mae = float(mean_absolute_error(y_test, y_pred))
        holdout_rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))

        per_candidate[name] = dict(
            best_params={**fixed_kwargs, **best_params},
            inner_cv_r2=inner_cv_r2,
            holdout_r2=holdout_r2,
            holdout_mae=holdout_mae,
            holdout_rmse=holdout_rmse,
        )
        if verbose:
            print(
                f"    {name:<20s} inner CV R2={inner_cv_r2:8.4f}  "
                f"holdout R2={holdout_r2:8.4f}  params={best_params}"
            )

    # Nested selection: by inner CV R^2 only. The outer holdout never participates here.
    selected_name = max(per_candidate, key=lambda k: per_candidate[k]["inner_cv_r2"])
    selected = per_candidate[selected_name]

    # For direct comparison: what the OLD protocol (select by holdout R^2 itself) would pick
    # on this identical split, using each candidate's already-computed holdout score above.
    old_protocol_name = max(per_candidate, key=lambda k: per_candidate[k]["holdout_r2"])

    return dict(
        per_candidate=per_candidate,
        selected_model=selected_name,
        selected_params=selected["best_params"],
        selected_inner_cv_r2=selected["inner_cv_r2"],
        selected_holdout_r2=selected["holdout_r2"],
        selected_holdout_mae=selected["holdout_mae"],
        selected_holdout_rmse=selected["holdout_rmse"],
        old_protocol_selected_model=old_protocol_name,
        old_protocol_holdout_r2=per_candidate[old_protocol_name]["holdout_r2"],
        n_train=len(X_train),
        n_test=len(X_test),
        n_features=X.shape[1],
    )
