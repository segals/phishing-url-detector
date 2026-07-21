"""Metrics and statistical validity helpers.

We never claim a win from a point estimate: every headline metric gets a bootstrap
95% CI, and every paired model comparison gets a McNemar test.
"""
from __future__ import annotations
import numpy as np
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             fbeta_score, matthews_corrcoef, roc_auc_score)
from . import config


def metrics(y, p, thr: float = 0.5) -> dict:
    """Standard suite. F2 weights recall higher (a missed phish costs more)."""
    y = np.asarray(y)
    yhat = (np.asarray(p) >= thr).astype(int)
    out = dict(
        accuracy=accuracy_score(y, yhat),
        precision=precision_score(y, yhat, zero_division=0),
        recall=recall_score(y, yhat, zero_division=0),
        f1=f1_score(y, yhat, zero_division=0),
        f2=fbeta_score(y, yhat, beta=2, zero_division=0),
        mcc=matthews_corrcoef(y, yhat) if len(set(y)) > 1 else 0.0,
    )
    try:
        out["auc"] = roc_auc_score(y, p)
    except ValueError:
        out["auc"] = float("nan")
    return out


def bootstrap_ci(y, p, metric="f1", thr=0.5, n=config.BOOTSTRAP_N, seed=config.SEED):
    """Percentile bootstrap 95% CI for one metric over test-set resamples."""
    y, p = np.asarray(y), np.asarray(p)
    rng = np.random.default_rng(seed)
    idx = np.arange(len(y))
    vals = []
    for _ in range(n):
        s = rng.choice(idx, size=len(idx), replace=True)
        if len(set(y[s])) < 2:
            continue
        vals.append(metrics(y[s], p[s], thr)[metric])
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return float(np.mean(vals)), float(lo), float(hi)


def mcnemar(y, p1, p2, thr=0.5):
    """McNemar's paired test on two classifiers' correctness (same test set).

    Returns (statistic, p_value, b, c) where b/c are the discordant counts.
    """
    from scipy.stats import chi2
    y = np.asarray(y)
    c1 = (np.asarray(p1) >= thr).astype(int) == y
    c2 = (np.asarray(p2) >= thr).astype(int) == y
    b = int(np.sum(c1 & ~c2))    # model1 right, model2 wrong
    c = int(np.sum(~c1 & c2))    # model1 wrong, model2 right
    if b + c == 0:
        return 0.0, 1.0, b, c
    stat = (abs(b - c) - 1) ** 2 / (b + c)     # with continuity correction
    return float(stat), float(chi2.sf(stat, 1)), b, c


def cost_optimal_threshold(y, p, c_fp=config.COST_FP, c_fn=config.COST_FN):
    """Threshold minimizing c_fp*FP + c_fn*FN (FN is the expensive error)."""
    y, p = np.asarray(y), np.asarray(p)
    best_t, best_cost = 0.5, float("inf")
    for t in np.linspace(0.01, 0.99, 99):
        yhat = (p >= t).astype(int)
        fp = int(np.sum((yhat == 1) & (y == 0)))
        fn = int(np.sum((yhat == 0) & (y == 1)))
        cost = c_fp * fp + c_fn * fn
        if cost < best_cost:
            best_cost, best_t = cost, t
    return float(best_t), float(best_cost)
