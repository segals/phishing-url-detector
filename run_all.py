"""Reproduce every table and figure, in order. Deterministic (seed 42).

Run:  python run_all.py
Phases are added incrementally; each saves CSVs to results/tables/ and PNGs to
results/figures/.
"""
from __future__ import annotations
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src import config, data, features, models, stats

GREEN, RED, INK = "#2a9d8f", "#e76f51", "#264653"
plt.rcParams.update({"figure.dpi": 120, "axes.grid": True, "grid.alpha": 0.3,
                     "axes.spines.top": False, "axes.spines.right": False})


# --------------------------------------------------------------------------- data
def prepare():
    """Load PhiUSIIL, clean, build honest URL features (cached), split."""
    df = data.working_set(data.load_phiusiil())
    cache = config.DATA_PROC / "url_features.csv"
    if cache.exists():
        F = pd.read_csv(cache)
    else:
        t = time.time()
        F = features.extract_frame(df["URL"])
        F.insert(0, "id", df["id"].values)
        F.to_csv(cache, index=False)
        print(f"  built {F.shape[1]-1} URL features for {len(F)} rows in {time.time()-t:.0f}s")
    F = F.set_index("id")
    provided = [c for c in df.select_dtypes("number").columns if c not in ("label", "id")]
    tr, va, te = data.split(df)
    (config.TABLES / "data_hash.txt").write_text(
        f"rows={len(df)} phishing_rate={df.label.mean():.4f} sha256={data.sha256_of(df[['URL','label']])}\n")
    return df, F, provided, tr, va, te


def X(F, rows, cols=None):
    sub = F.loc[rows["id"].values]
    return sub if cols is None else sub[cols]


# --------------------------------------------------------------- Phase 1: the artifact
def phase1(df, F, provided, tr, va, te):
    print("Phase 1: where the near-perfect score comes from")
    ytr, yte = tr["label"].values, te["label"].values
    feat_cols = features.FEATURE_NAMES

    # T1 dataset composition
    pd.DataFrame([{"dataset": "PhiUSIIL", "urls": len(df), "phishing": int(df.label.sum()),
                   "legitimate": int((df.label == 0).sum()), "phishing_rate": round(df.label.mean(), 3)}]
                 ).to_csv(config.TABLES / "T1_dataset.csv", index=False)

    # T0 the decomposition: all provided -> single leaky feature -> honest lexical
    rows = []
    dfi = df.set_index("id")
    _, p = models.fit_predict(models.model_zoo()["random_forest"],
                              dfi.loc[tr["id"], provided], ytr, dfi.loc[te["id"], provided])
    m = stats.metrics(yte, p); f1c = stats.bootstrap_ci(yte, p, "f1")
    rows.append([f"all {len(provided)} provided features (RF)", round(m["f1"], 4), round(m["auc"], 4), f"[{f1c[1]:.3f}, {f1c[2]:.3f}]"])

    for feat in ["URLSimilarityIndex", "URLCharProb", "TLDLegitimateProb"]:
        _, pp = models.fit_predict(models.model_zoo()["logreg"],
                                   dfi.loc[tr["id"], [feat]], ytr, dfi.loc[te["id"], [feat]])
        mm = stats.metrics(yte, pp)
        rows.append([f"single provided feature: {feat}", round(mm["f1"], 4), round(mm["auc"], 4), ""])

    _, p3 = models.fit_predict(models.model_zoo()["random_forest"], X(F, tr, feat_cols), ytr, X(F, te, feat_cols))
    m3 = stats.metrics(yte, p3); f1c3 = stats.bootstrap_ci(yte, p3, "f1")
    rows.append(["honest raw-URL lexical (40, RF)", round(m3["f1"], 4), round(m3["auc"], 4), f"[{f1c3[1]:.3f}, {f1c3[2]:.3f}]"])
    pd.DataFrame(rows, columns=["representation", "f1", "auc", "f1_95ci"]).to_csv(
        config.TABLES / "T0_artifact_decomposition.csv", index=False)
    print("  T0:", rows[0][1], "(all) /", rows[1][1], "(1 feature) /", rows[-1][1], "(honest lexical)")

    # T1b trivial baselines (accuracy paradox)
    base = []
    maj = np.zeros(len(yte))
    base.append(["majority class (predict legit)", *_bl(yte, maj)])
    not_https = (X(F, te, ["is_https"]).values.ravel() == 0).astype(float)
    base.append(["rule: not https -> phishing", *_bl(yte, not_https)])
    cue = (X(F, te, ["n_cue_words"]).values.ravel() > 0).astype(float)
    base.append(["rule: has cue word -> phishing", *_bl(yte, cue)])
    pd.DataFrame(base, columns=["baseline", "accuracy", "recall", "f1", "mcc"]).to_csv(
        config.TABLES / "T1b_baselines.csv", index=False)

    # T2 model comparison on honest lexical (+CIs, +McNemar vs best)
    preds, comp = {}, []
    for name, mdl in models.model_zoo().items():
        _, pv = models.fit_predict(mdl, X(F, tr, feat_cols), ytr, X(F, te, feat_cols))
        preds[name] = pv
        mm = stats.metrics(yte, pv); ci = stats.bootstrap_ci(yte, pv, "f1")
        comp.append([name, round(mm["f1"], 4), f"[{ci[1]:.3f}, {ci[2]:.3f}]",
                     round(mm["recall"], 4), round(mm["precision"], 4), round(mm["mcc"], 4), round(mm["auc"], 4)])
    best = max(preds, key=lambda k: stats.metrics(yte, preds[k])["f1"])
    for r in comp:
        if r[0] == best:
            r.append("(best)")
        else:
            _, pval, _, _ = stats.mcnemar(yte, preds[best], preds[r[0]])
            r.append(f"p={pval:.1e}")
    pd.DataFrame(comp, columns=["model", "f1", "f1_95ci", "recall", "precision", "mcc", "auc", "mcnemar_vs_best"]
                 ).to_csv(config.TABLES / "T2_model_comparison.csv", index=False)
    print(f"  T2 best model: {best}")

    _figures(df, F, tr, te)
    return preds, best


def _bl(y, yhat):
    from sklearn.metrics import accuracy_score, recall_score, f1_score, matthews_corrcoef
    return [round(accuracy_score(y, yhat), 4), round(recall_score(y, yhat, zero_division=0), 4),
            round(f1_score(y, yhat, zero_division=0), 4),
            round(matthews_corrcoef(y, yhat) if len(set(yhat)) > 1 else 0.0, 4)]


def _figures(df, F, tr, te):
    # F1 EDA: class balance + a few feature distributions by class
    Fte = X(F, te, features.FEATURE_NAMES); yte = te["label"].values
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
    df.label.map({0: "legit", 1: "phishing"}).value_counts().plot.bar(ax=ax[0], color=[GREEN, RED], rot=0)
    ax[0].set_title("class balance")
    for a, feat, t in [(ax[1], "url_len", "URL length"), (ax[2], "n_cue_words", "cue words in URL")]:
        a.hist(Fte[feat][yte == 0].clip(upper=Fte[feat].quantile(.99)), bins=30, alpha=.6, color=GREEN, label="legit")
        a.hist(Fte[feat][yte == 1].clip(upper=Fte[feat].quantile(.99)), bins=30, alpha=.6, color=RED, label="phishing")
        a.set_title(t); a.legend()
    fig.tight_layout(); fig.savefig(config.FIGURES / "F1_eda.png"); plt.close(fig)

    # F2 feature importance (RF on honest lexical)
    rf = models.model_zoo()["random_forest"]
    rf.fit(X(F, tr, features.FEATURE_NAMES), tr["label"].values)
    imp = pd.Series(rf.feature_importances_, index=features.FEATURE_NAMES).sort_values().tail(15)
    fig, ax = plt.subplots(figsize=(7, 5))
    imp.plot.barh(ax=ax, color=INK); ax.set_title("RF feature importance (honest lexical)")
    fig.tight_layout(); fig.savefig(config.FIGURES / "F2_feature_importance.png"); plt.close(fig)


if __name__ == "__main__":
    t0 = time.time()
    df, F, provided, tr, va, te = prepare()
    phase1(df, F, provided, tr, va, te)
    print(f"done in {time.time()-t0:.0f}s")
