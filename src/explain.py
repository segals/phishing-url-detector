"""Explainability for the URL detector.

Tree models are not linear, so (unlike the partner's logistic text model) exact
coefficient attribution isn't available -- we use SHAP (Lundberg & Lee, 2017) to get
faithful per-feature contributions, plus permutation importance as a cross-check.
The point of interest: SHAP shows the model leans on the collection-artifact features
(is_https, structural size), which is the interpretability side of the artifact story.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def shap_importance(model, X, max_n=2000, seed=42):
    """Mean |SHAP value| per feature (global importance) on a sample."""
    import shap
    Xs = X.sample(min(len(X), max_n), random_state=seed)
    sv = shap.TreeExplainer(model).shap_values(Xs)
    if isinstance(sv, list):            # [class0, class1]
        sv = sv[1]
    elif getattr(sv, "ndim", 2) == 3:   # (n, f, 2)
        sv = sv[:, :, 1]
    imp = pd.Series(np.abs(sv).mean(axis=0), index=X.columns).sort_values(ascending=False)
    return imp, Xs, sv
