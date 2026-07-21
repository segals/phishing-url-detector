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


# ----------------------------------------------- Phase 3: URL-obfuscation arms race
def phase3(df, F, tr, te):
    print("Phase 3: the URL-obfuscation arms race")
    from src import attacks, normalize
    feat = features.FEATURE_NAMES
    feat_db = [c for c in feat if c != "is_https"]      # de-biased: drop the https crutch
    ytr = tr["label"].values

    mdl = models.model_zoo()["hist_gbm"].fit(X(F, tr, feat), ytr)
    mdl_db = models.model_zoo()["hist_gbm"].fit(X(F, tr, feat_db), ytr)

    # T3a: the dominant collection artifact -- HTTPS rate by class
    hr = df.groupby("label")["URL"].apply(lambda s: s.str.startswith("https").mean())
    pd.DataFrame({"class": ["legitimate", "phishing"],
                  "https_rate": [round(hr[0], 3), round(hr[1], 3)]}
                 ).to_csv(config.TABLES / "T3a_https_artifact.csv", index=False)

    ph = te.loc[te["label"] == 1, "URL"].tolist()       # attacker perturbs phishing

    def recall(urls, model, cols):
        Fx = features.extract_frame(urls)[cols]
        return float((model.predict_proba(Fx)[:, 1] >= 0.5).mean())

    clean = recall(ph, mdl, feat)
    rows = [["(clean)", round(clean, 3), round(clean, 3), round(recall(ph, mdl_db, feat_db), 3)]]
    for k in ["homoglyph", "typosquat", "https_upgrade", "homepage_mimicry"]:
        att = attacks.apply_attack(ph, k, seed=0)
        rows.append([k, round(recall(att, mdl, feat), 3),
                     round(recall(normalize.normalize_many(att), mdl, feat), 3),
                     round(recall(att, mdl_db, feat_db), 3)])
    T3 = pd.DataFrame(rows, columns=["attack", "recall_attacked",
                                     "recall_+normalize", "recall_+debias(no https)"])
    T3.to_csv(config.TABLES / "T3_arms_race.csv", index=False)
    print(f"  HTTPS artifact: legit {hr[0]:.2f} vs phishing {hr[1]:.2f}")
    print(T3.to_string(index=False))

    fig, ax = plt.subplots(figsize=(9, 4.2))
    T3.set_index("attack").plot.bar(ax=ax, color=[RED, GREEN, INK], rot=12)
    ax.set_ylim(0, 1.05); ax.set_ylabel("recall on phishing"); ax.axhline(clean, ls="--", color="grey")
    ax.set_title("URL obfuscation: structural attacks are harmless, but the HTTPS artifact is exploitable")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(config.FIGURES / "F3_arms_race.png"); plt.close(fig)


# --------------------------------- Phase 4: cross-dataset generalization (independent source)
def phase4(df, F, tr, te):
    print("Phase 4: does the score survive a DIFFERENT, mixed-class dataset?")
    feat = features.FEATURE_NAMES
    feat_db = [c for c in feat if c != "is_https"]
    ytr = tr["label"].values
    mdl = models.model_zoo()["hist_gbm"].fit(X(F, tr, feat), ytr)
    mdl_db = models.model_zoo()["hist_gbm"].fit(X(F, tr, feat_db), ytr)
    m_id = stats.metrics(te["label"].values, mdl.predict_proba(X(F, te, feat))[:, 1])

    # OOD: Kaggle Malicious-URLs (independent source), phishing vs benign, balanced sample
    k = pd.read_csv(config.DATA_RAW / "malicious_urls" / "malicious_phish.csv")
    k = k[k["type"].isin(["phishing", "benign"])].copy()
    k["label"] = (k["type"] == "phishing").astype(int)
    k = k.groupby("label", group_keys=False).sample(n=40000, random_state=config.SEED)
    cache = config.DATA_PROC / "kaggle_features.csv"
    if cache.exists():
        Fk = pd.read_csv(cache)
    else:
        Fk = features.extract_frame(k["url"]); Fk["label"] = k["label"].values
        Fk.to_csv(cache, index=False)
    yk = Fk["label"].values
    p_ood = mdl.predict_proba(Fk[feat])[:, 1]
    p_ood_db = mdl_db.predict_proba(Fk[feat_db])[:, 1]
    m_ood, m_ood_db = stats.metrics(yk, p_ood), stats.metrics(yk, p_ood_db)
    best_t, _ = stats.cost_optimal_threshold(yk, p_ood, 1, 1)
    m_ood_rt = stats.metrics(yk, p_ood, best_t)

    # live modern phishing (OpenPhish), recall only
    oph = pd.read_csv(config.DATA_RAW / "openphish.csv")
    rec_oph = float((mdl.predict_proba(features.extract_frame(oph["URL"])[feat])[:, 1] >= .5).mean())

    T4 = pd.DataFrame([
        ["in-distribution (PhiUSIIL test)", m_id["f1"], m_id["recall"], m_id["auc"], 0.5],
        ["cross-dataset (Kaggle, full model)", m_ood["f1"], m_ood["recall"], m_ood["auc"], 0.5],
        ["cross-dataset (Kaggle, no is_https)", m_ood_db["f1"], m_ood_db["recall"], m_ood_db["auc"], 0.5],
        ["cross-dataset (Kaggle, re-thresholded)", m_ood_rt["f1"], m_ood_rt["recall"], m_ood["auc"], round(best_t, 2)],
        ["live OpenPhish (recall only)", float("nan"), rec_oph, float("nan"), 0.5],
    ], columns=["setting", "f1", "recall_phishing", "auc", "threshold"]).round(3)
    T4.to_csv(config.TABLES / "T4_cross_dataset.csv", index=False)
    print(f"  in-dist F1 {m_id['f1']:.3f} -> cross-dataset F1 {m_ood['f1']:.3f} (AUC {m_ood['auc']:.3f}); live OpenPhish recall {rec_oph:.3f}")
    print(T4.to_string(index=False))

    fig, ax = plt.subplots(figsize=(7.5, 4))
    ax.hist(p_ood[yk == 1], bins=30, alpha=.6, color=RED, label="phishing (Kaggle)")
    ax.hist(p_ood[yk == 0], bins=30, alpha=.6, color=GREEN, label="benign (Kaggle)")
    ax.axvline(0.5, ls="--", color="grey"); ax.set_xlabel("P(phishing) from the PhiUSIIL-trained model")
    ax.set_title("Cross-dataset: scores on an independent source"); ax.legend()
    fig.tight_layout(); fig.savefig(config.FIGURES / "F4_cross_dataset.png"); plt.close(fig)


# ------------------------------------------------- Phase 5: explainability (SHAP)
def phase5(df, F, tr, te):
    print("Phase 5: what is the model actually using? (SHAP)")
    from src import explain
    feat = features.FEATURE_NAMES
    rf = models.model_zoo()["random_forest"].fit(X(F, tr, feat), tr["label"].values)
    imp, _, _ = explain.shap_importance(rf, X(F, te, feat), max_n=2000)
    imp.head(15).to_frame("mean_abs_shap").to_csv(config.TABLES / "T5_shap_importance.csv")
    print("  top drivers:", list(imp.head(6).index))

    fig, ax = plt.subplots(figsize=(7, 5))
    imp.head(15)[::-1].plot.barh(ax=ax, color=INK)
    ax.set_title("SHAP global importance (honest URL features)"); ax.set_xlabel("mean |SHAP|")
    fig.tight_layout(); fig.savefig(config.FIGURES / "F5_shap.png"); plt.close(fig)


if __name__ == "__main__":
    t0 = time.time()
    df, F, provided, tr, va, te = prepare()
    phase1(df, F, provided, tr, va, te)
    phase3(df, F, tr, te)
    phase4(df, F, tr, te)
    phase5(df, F, tr, te)
    print(f"done in {time.time()-t0:.0f}s")
