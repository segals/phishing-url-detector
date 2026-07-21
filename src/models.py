"""Model zoo for the URL detector.

Linear (interpretable) and tree ensembles (accuracy). Logistic regression is wrapped
in a scaler because the URL features live on very different scales; the trees are
scale-invariant so they are used bare.
"""
from __future__ import annotations
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from . import config


def model_zoo() -> dict:
    """The candidate models, keyed by short name."""
    return {
        "logreg": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=2000, C=1.0, random_state=config.SEED),
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=300, n_jobs=-1, random_state=config.SEED,
        ),
        "hist_gbm": HistGradientBoostingClassifier(
            max_iter=400, learning_rate=0.08, random_state=config.SEED,
        ),
    }


def fit_predict(model, Xtr, ytr, Xte):
    """Fit and return P(phishing) on Xte."""
    model.fit(Xtr, ytr)
    return model, model.predict_proba(Xte)[:, 1]
