"""Reproduce every table and figure, in order. Deterministic (seed 42).

Run:  python run_all.py

Each phase writes CSVs to results/tables/ and PNGs to results/figures/.

A note on loops: the loops that remain are the ones that cannot be vectorised —
per-URL string parsing, the Levenshtein dynamic program, and the cases where a whole
model is refitted (per attack, per feature group, per bootstrap resample) or where
SciPy only offers a per-column two-sample test. Column-wise statistics that SciPy and
pandas can compute in one call are computed that way.
"""
from __future__ import annotations

import time

import matplotlib
import numpy as np
import pandas as pd
from scipy import stats as ss
from sklearn.calibration import calibration_curve
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (accuracy_score, brier_score_loss, f1_score,
                             matthews_corrcoef, recall_score, roc_auc_score)
from sklearn.neighbors import LocalOutlierFactor

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  (backend must be set before pyplot)

from src import attacks, config, data, explain, features, models, normalize, stats

GREEN, RED, INK = "#2a9d8f", "#e76f51", "#264653"
plt.rcParams.update({"figure.dpi": 120, "axes.grid": True, "grid.alpha": 0.3,
                     "axes.spines.top": False, "axes.spines.right": False})


# --------------------------------------------------------------------------- data
def prepare():
    """Load PhiUSIIL, clean, build the URL features (cached), and split."""
    df = data.working_set(data.load_phiusiil())
    # NOTE ON DETERMINISM: a CSV round-trip loses float64 precision in the last bits, and
    # because tree models split on thresholds those bits can flip a few borderline samples.
    # To make results identical whether or not the cache already existed, the pipeline
    # ALWAYS consumes the persisted artifact: we write the cache, then read it back.
    cache = config.DATA_PROC / "url_features.csv"
    if not cache.exists():
        t = time.time()
        built = features.extract_frame(df["URL"])
        built.insert(0, "id", df["id"].values)
        built.to_csv(cache, index=False)
        print(f"  built {built.shape[1] - 1} URL features for {len(built)} rows "
              f"in {time.time() - t:.0f}s")
    feature_frame = pd.read_csv(cache).set_index("id")

    provided = [c for c in df.select_dtypes("number").columns if c not in ("label", "id")]
    tr, va, te = data.split(df)
    (config.TABLES / "data_hash.txt").write_text(
        f"rows={len(df)} phishing_rate={df.label.mean():.4f} "
        f"sha256={data.sha256_of(df[['URL', 'label']])}\n")
    return df, feature_frame, provided, tr, va, te


def X(feature_frame, rows, cols=None):
    """Feature rows for a split, optionally restricted to `cols`."""
    sub = feature_frame.loc[rows["id"].values]
    return sub if cols is None else sub[cols]


def _baseline_scores(y, yhat):
    """Accuracy / recall / F1 / MCC for a rule-based baseline."""
    return [round(accuracy_score(y, yhat), 4),
            round(recall_score(y, yhat, zero_division=0), 4),
            round(f1_score(y, yhat, zero_division=0), 4),
            round(matthews_corrcoef(y, yhat) if len(set(yhat)) > 1 else 0.0, 4)]


# --------------------------------------------------------------- Phase 1: the artifact
def phase1(df, feature_frame, provided, tr, te):
    print("Phase 1: where the near-perfect score comes from")
    ytr, yte = tr["label"].values, te["label"].values
    feat = features.FEATURE_NAMES

    # T1 dataset composition
    pd.DataFrame([{"dataset": "PhiUSIIL", "urls": len(df), "phishing": int(df.label.sum()),
                   "legitimate": int((df.label == 0).sum()),
                   "phishing_rate": round(df.label.mean(), 3)}]
                 ).to_csv(config.TABLES / "T1_dataset.csv", index=False)

    # T0 the decomposition: all provided -> single leaky feature -> honest lexical.
    # One model is fitted per representation, so this loop is a genuine refit loop.
    dfi = df.set_index("id")
    rows = []
    _, p_all = models.fit_predict(models.model_zoo()["random_forest"],
                                  dfi.loc[tr["id"], provided], ytr,
                                  dfi.loc[te["id"], provided])
    m_all = stats.metrics(yte, p_all)
    ci_all = stats.bootstrap_ci(yte, p_all, "f1")
    rows.append([f"all {len(provided)} provided features (RF)", round(m_all["f1"], 4),
                 round(m_all["auc"], 4), f"[{ci_all[1]:.3f}, {ci_all[2]:.3f}]"])

    for single in ["URLSimilarityIndex", "URLCharProb", "TLDLegitimateProb"]:
        _, p_one = models.fit_predict(models.model_zoo()["logreg"],
                                      dfi.loc[tr["id"], [single]], ytr,
                                      dfi.loc[te["id"], [single]])
        m_one = stats.metrics(yte, p_one)
        rows.append([f"single provided feature: {single}", round(m_one["f1"], 4),
                     round(m_one["auc"], 4), ""])

    _, p_lex = models.fit_predict(models.model_zoo()["random_forest"],
                                  X(feature_frame, tr, feat), ytr, X(feature_frame, te, feat))
    m_lex = stats.metrics(yte, p_lex)
    ci_lex = stats.bootstrap_ci(yte, p_lex, "f1")
    rows.append(["honest raw-URL lexical (40, RF)", round(m_lex["f1"], 4),
                 round(m_lex["auc"], 4), f"[{ci_lex[1]:.3f}, {ci_lex[2]:.3f}]"])
    pd.DataFrame(rows, columns=["representation", "f1", "auc", "f1_95ci"]).to_csv(
        config.TABLES / "T0_artifact_decomposition.csv", index=False)
    print("  T0:", rows[0][1], "(all) /", rows[1][1], "(1 feature) /",
          rows[-1][1], "(honest lexical)")

    # T1b trivial baselines (the accuracy paradox)
    not_https = (X(feature_frame, te, ["is_https"]).values.ravel() == 0).astype(float)
    has_cue = (X(feature_frame, te, ["n_cue_words"]).values.ravel() > 0).astype(float)
    base = [["majority class (predict legit)", *_baseline_scores(yte, np.zeros(len(yte)))],
            ["rule: not https -> phishing", *_baseline_scores(yte, not_https)],
            ["rule: has cue word -> phishing", *_baseline_scores(yte, has_cue)]]
    pd.DataFrame(base, columns=["baseline", "accuracy", "recall", "f1", "mcc"]).to_csv(
        config.TABLES / "T1b_baselines.csv", index=False)

    # T2 model comparison (+ bootstrap CIs, + McNemar against the best)
    preds, comp = {}, []
    for name, mdl in models.model_zoo().items():
        _, p_model = models.fit_predict(mdl, X(feature_frame, tr, feat), ytr,
                                        X(feature_frame, te, feat))
        preds[name] = p_model
        m_model = stats.metrics(yte, p_model)
        ci = stats.bootstrap_ci(yte, p_model, "f1")
        comp.append([name, round(m_model["f1"], 4), f"[{ci[1]:.3f}, {ci[2]:.3f}]",
                     round(m_model["recall"], 4), round(m_model["precision"], 4),
                     round(m_model["mcc"], 4), round(m_model["auc"], 4)])

    best = max(preds, key=lambda k: stats.metrics(yte, preds[k])["f1"])
    for row in comp:
        if row[0] == best:
            row.append("(best)")
        else:
            _, pval, _, _ = stats.mcnemar(yte, preds[best], preds[row[0]])
            row.append(f"p={pval:.1e}")
    pd.DataFrame(comp, columns=["model", "f1", "f1_95ci", "recall", "precision", "mcc",
                                "auc", "mcnemar_vs_best"]
                 ).to_csv(config.TABLES / "T2_model_comparison.csv", index=False)
    print(f"  T2 best model: {best}")

    _figures(df, feature_frame, tr, te)


def _figures(df, feature_frame, tr, te):
    """F1 (EDA) and F2 (random-forest impurity importance)."""
    fte = X(feature_frame, te, features.FEATURE_NAMES)
    yte = te["label"].values

    fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
    df.label.map({0: "legit", 1: "phishing"}).value_counts().plot.bar(
        ax=ax[0], color=[GREEN, RED], rot=0)
    ax[0].set_title("class balance")
    for axis, col, title in [(ax[1], "url_len", "URL length"),
                             (ax[2], "n_cue_words", "cue words in URL")]:
        cap = fte[col].quantile(.99)
        axis.hist(fte[col][yte == 0].clip(upper=cap), bins=30, alpha=.6,
                  color=GREEN, label="legit")
        axis.hist(fte[col][yte == 1].clip(upper=cap), bins=30, alpha=.6,
                  color=RED, label="phishing")
        axis.set_title(title)
        axis.legend()
    fig.tight_layout()
    fig.savefig(config.FIGURES / "F1_eda.png")
    plt.close(fig)

    rf = models.model_zoo()["random_forest"]
    rf.fit(X(feature_frame, tr, features.FEATURE_NAMES), tr["label"].values)
    imp = pd.Series(rf.feature_importances_,
                    index=features.FEATURE_NAMES).sort_values().tail(15)
    fig, ax = plt.subplots(figsize=(7, 5))
    imp.plot.barh(ax=ax, color=INK)
    ax.set_title("RF feature importance (honest lexical)")
    fig.tight_layout()
    fig.savefig(config.FIGURES / "F2_feature_importance.png")
    plt.close(fig)


# ----------------------------------------- Phase 2: deeper EDA (course statistics)
def phase2_eda(feature_frame, tr):
    print("Phase 2: deeper EDA -- distribution shape, correlation, non-parametric tests")
    feat = features.FEATURE_NAMES
    ftr = X(feature_frame, tr, feat)
    y = tr["label"].values

    # Distribution shape: many URL features are heavy-tailed, which is WHY we prefer
    # Spearman/median over Pearson/mean (course: robust statistics). SciPy computes
    # both statistics column-wise in one call.
    shape_cols = ["url_len", "host_len", "digit_ratio", "host_entropy",
                  "n_cue_words", "n_subdomain"]
    pd.DataFrame({"feature": shape_cols,
                  "skewness": np.round(ss.skew(ftr[shape_cols], axis=0), 2),
                  "excess_kurtosis": np.round(ss.kurtosis(ftr[shape_cols], axis=0), 2)}
                 ).to_csv(config.TABLES / "T6_eda_shape.csv", index=False)

    # Pearson (linear) vs Spearman (monotone) correlation with the label, both computed
    # for every feature at once with corrwith.
    label = pd.Series(y, index=ftr.index)
    corr = pd.DataFrame({
        "feature": feat,
        "pearson": ftr.corrwith(label).reindex(feat).round(3).values,
        "spearman": ftr.corrwith(label, method="spearman").reindex(feat).round(3).values,
    })
    ranked = corr.reindex(corr["spearman"].abs().sort_values(ascending=False).index)
    ranked.head(15).to_csv(config.TABLES / "T7_correlation.csv", index=False)

    # Mann-Whitney U (non-parametric, since the features are skewed). SciPy's two-sample
    # test needs the two class samples per feature, so this stays a loop.
    mw = []
    for col in ["url_len", "host_entropy", "digit_ratio", "n_cue_words", "is_https"]:
        _, pval = ss.mannwhitneyu(ftr[col][y == 1], ftr[col][y == 0],
                                  alternative="two-sided")
        mw.append([col, f"{pval:.1e}",
                   round(float(ftr[col][y == 1].median()), 3),
                   round(float(ftr[col][y == 0].median()), 3)])
    pd.DataFrame(mw, columns=["feature", "mannwhitney_p", "median_phishing", "median_legit"]
                 ).to_csv(config.TABLES / "T8_mannwhitney.csv", index=False)

    top = ranked.head(12)["feature"].tolist()
    matrix = ftr[top].corr(method="spearman")
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(matrix, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(top)))
    ax.set_xticklabels(top, rotation=90, fontsize=7)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top, fontsize=7)
    fig.colorbar(im, fraction=0.046)
    ax.set_title("Spearman correlation (top features)")
    fig.tight_layout()
    fig.savefig(config.FIGURES / "F6_correlation.png")
    plt.close(fig)


# ----------------------------------------------- Phase 3: URL-obfuscation arms race
def phase3(df, feature_frame, tr, te):
    print("Phase 3: the URL-obfuscation arms race")
    feat = features.FEATURE_NAMES
    feat_db = [c for c in feat if c != "is_https"]      # de-biased: drop the https crutch
    ytr = tr["label"].values

    mdl = models.model_zoo()["hist_gbm"].fit(X(feature_frame, tr, feat), ytr)
    mdl_db = models.model_zoo()["hist_gbm"].fit(X(feature_frame, tr, feat_db), ytr)

    # T3a: the dominant collection artifact -- HTTPS rate by class
    https_rate = df.groupby("label")["URL"].apply(lambda s: s.str.startswith("https").mean())
    pd.DataFrame({"class": ["legitimate", "phishing"],
                  "https_rate": [round(https_rate[0], 3), round(https_rate[1], 3)]}
                 ).to_csv(config.TABLES / "T3a_https_artifact.csv", index=False)

    phishing_urls = te.loc[te["label"] == 1, "URL"].tolist()   # the attacker perturbs these

    def recall(urls, model, cols):
        scored = features.extract_frame(urls)[cols]
        return float((model.predict_proba(scored)[:, 1] >= 0.5).mean())

    clean = recall(phishing_urls, mdl, feat)
    rows = [["(clean)", round(clean, 3), round(clean, 3),
             round(recall(phishing_urls, mdl_db, feat_db), 3)]]
    # One attack is generated and re-scored per family, so this loop is necessary.
    for kind in ["homoglyph", "typosquat", "https_upgrade", "homepage_mimicry"]:
        attacked = attacks.apply_attack(phishing_urls, kind, seed=0)
        rows.append([kind,
                     round(recall(attacked, mdl, feat), 3),
                     round(recall(normalize.normalize_many(attacked), mdl, feat), 3),
                     round(recall(attacked, mdl_db, feat_db), 3)])
    table = pd.DataFrame(rows, columns=["attack", "recall_attacked", "recall_+normalize",
                                        "recall_+debias(no https)"])
    table.to_csv(config.TABLES / "T3_arms_race.csv", index=False)
    print(f"  HTTPS artifact: legit {https_rate[0]:.2f} vs phishing {https_rate[1]:.2f}")
    print(table.to_string(index=False))

    fig, ax = plt.subplots(figsize=(9, 4.2))
    table.set_index("attack").plot.bar(ax=ax, color=[RED, GREEN, INK], rot=12)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("recall on phishing")
    ax.axhline(clean, ls="--", color="grey")
    ax.set_title("URL obfuscation: structural attacks are harmless, "
                 "but the HTTPS artifact is exploitable")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(config.FIGURES / "F3_arms_race.png")
    plt.close(fig)


# --------------------------- Phase 4: cross-dataset generalisation (independent source)
def phase4(feature_frame, tr, te):
    print("Phase 4: does the score survive a DIFFERENT, mixed-class dataset?")
    feat = features.FEATURE_NAMES
    feat_db = [c for c in feat if c != "is_https"]
    ytr = tr["label"].values
    mdl = models.model_zoo()["hist_gbm"].fit(X(feature_frame, tr, feat), ytr)
    mdl_db = models.model_zoo()["hist_gbm"].fit(X(feature_frame, tr, feat_db), ytr)
    p_id = mdl.predict_proba(X(feature_frame, te, feat))[:, 1]
    y_id = te["label"].values
    m_id = stats.metrics(y_id, p_id)

    # OOD: Kaggle Malicious-URLs (independent source), phishing vs benign, balanced
    kaggle = pd.read_csv(config.DATA_RAW / "malicious_urls" / "malicious_phish.csv")
    kaggle = kaggle[kaggle["type"].isin(["phishing", "benign"])].copy()
    kaggle["label"] = (kaggle["type"] == "phishing").astype(int)
    kaggle = kaggle.groupby("label", group_keys=False).sample(n=40000,
                                                              random_state=config.SEED)
    cache = config.DATA_PROC / "kaggle_features.csv"
    if not cache.exists():          # always consume the persisted artifact (see prepare())
        built = features.extract_frame(kaggle["url"])
        built["label"] = kaggle["label"].values
        built.to_csv(cache, index=False)
    fk = pd.read_csv(cache)
    yk = fk["label"].values

    p_ood = mdl.predict_proba(fk[feat])[:, 1]
    p_ood_db = mdl_db.predict_proba(fk[feat_db])[:, 1]
    m_ood = stats.metrics(yk, p_ood)
    m_ood_db = stats.metrics(yk, p_ood_db)
    best_t, _ = stats.cost_optimal_threshold(yk, p_ood, 1, 1)
    m_ood_rt = stats.metrics(yk, p_ood, best_t)

    # live modern phishing (OpenPhish), recall only
    openphish = pd.read_csv(config.DATA_RAW / "openphish.csv")
    scored = features.extract_frame(openphish["URL"])[feat]
    rec_oph = float((mdl.predict_proba(scored)[:, 1] >= .5).mean())

    table = pd.DataFrame([
        ["in-distribution (PhiUSIIL test)", m_id["f1"], m_id["recall"], m_id["auc"], 0.5],
        ["cross-dataset (Kaggle, full model)", m_ood["f1"], m_ood["recall"],
         m_ood["auc"], 0.5],
        ["cross-dataset (Kaggle, no is_https)", m_ood_db["f1"], m_ood_db["recall"],
         m_ood_db["auc"], 0.5],
        ["cross-dataset (Kaggle, re-thresholded)", m_ood_rt["f1"], m_ood_rt["recall"],
         m_ood["auc"], round(best_t, 2)],
        ["live OpenPhish (recall only)", float("nan"), rec_oph, float("nan"), 0.5],
    ], columns=["setting", "f1", "recall_phishing", "auc", "threshold"]).round(3)
    table.to_csv(config.TABLES / "T4_cross_dataset.csv", index=False)
    print(f"  in-dist F1 {m_id['f1']:.3f} -> cross-dataset F1 {m_ood['f1']:.3f} "
          f"(AUC {m_ood['auc']:.3f}); live OpenPhish recall {rec_oph:.3f}")
    print(table.to_string(index=False))

    # Unambiguous before/after: boxplots of the score distribution by TRUE class, for
    # in-distribution (separated) vs cross-dataset (collapsed). A histogram at this level
    # of saturation (both classes piled at ~1.0) is visually ambiguous; a boxplot is not.
    groups = [p_id[y_id == 0], p_id[y_id == 1], p_ood[yk == 0], p_ood[yk == 1]]
    labels = ["legit\n(in-dist.)", "phishing\n(in-dist.)",
              "legit\n(Kaggle)", "phishing\n(Kaggle)"]
    fig, ax = plt.subplots(figsize=(7.5, 4.3))
    box = ax.boxplot(groups, tick_labels=labels, patch_artist=True,
                     showfliers=False, widths=0.55)
    for patch, colour in zip(box["boxes"], [GREEN, RED, GREEN, RED]):
        patch.set_facecolor(colour)
        patch.set_alpha(0.75)
    ax.axhline(0.5, ls="--", color="grey", lw=1)
    ax.set_ylabel("P(phishing) from the PhiUSIIL-trained model")
    ax.set_ylim(-0.03, 1.03)
    ax.set_title("In-distribution the classes separate; on Kaggle both collapse to ~1.0")
    ax.axvline(2.5, color="grey", lw=0.8, ls=":")
    fig.tight_layout()
    fig.savefig(config.FIGURES / "F4_cross_dataset.png")
    plt.close(fig)


# ------------------------------------------------- Phase 5: explainability (SHAP)
def phase5(feature_frame, tr, te):
    print("Phase 5: what is the model actually using? (SHAP)")
    feat = features.FEATURE_NAMES
    rf = models.model_zoo()["random_forest"].fit(X(feature_frame, tr, feat),
                                                 tr["label"].values)
    imp, _, _ = explain.shap_importance(rf, X(feature_frame, te, feat), max_n=2000)
    imp.head(15).to_frame("mean_abs_shap").to_csv(
        config.TABLES / "T5_shap_importance.csv", index_label="feature")
    print("  top drivers:", list(imp.head(6).index))

    fig, ax = plt.subplots(figsize=(7, 5))
    imp.head(15)[::-1].plot.barh(ax=ax, color=INK)
    ax.set_title("SHAP global importance (honest URL features)")
    ax.set_xlabel("mean |SHAP|")
    fig.tight_layout()
    fig.savefig(config.FIGURES / "F5_shap.png")
    plt.close(fig)


# ------------------------------ Phase 6: quantify the domain shift (distance metrics)
def phase6_shift(feature_frame):
    print("Phase 6: measuring the domain shift with KS + Wasserstein "
          "(course: distance metrics)")
    feat = features.FEATURE_NAMES
    a = feature_frame[feat]
    b = pd.read_csv(config.DATA_PROC / "kaggle_features.csv")[feat]
    # Both are two-sample tests between a pair of columns, which SciPy only exposes
    # per column, so the loop is required.
    rows = []
    for col in feat:
        ks = ss.ks_2samp(a[col], b[col]).statistic
        emd = ss.wasserstein_distance(a[col], b[col]) / (a[col].std() or 1.0)
        rows.append([col, round(float(ks), 3), round(float(emd), 3)])
    table = pd.DataFrame(rows, columns=["feature", "ks_statistic", "wasserstein_norm"]
                         ).sort_values("ks_statistic", ascending=False)
    table.head(15).to_csv(config.TABLES / "T9_domain_shift.csv", index=False)
    print("  most-shifted features (KS):", table.head(5)["feature"].tolist())

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    table.head(12).set_index("feature")["ks_statistic"][::-1].plot.barh(ax=ax, color=RED)
    ax.set_title("Distribution shift PhiUSIIL -> Kaggle (KS)")
    ax.set_xlabel("KS statistic")
    fig.tight_layout()
    fig.savefig(config.FIGURES / "F7_domain_shift.png")
    plt.close(fig)


# --------------------------- Phase 7: unsupervised abnormality detection (course topic)
def phase7_anomaly(feature_frame, tr, te):
    print("Phase 7: unsupervised anomaly detection (Isolation Forest, LOF)")
    feat = features.FEATURE_NAMES
    xte = X(feature_frame, te, feat)
    yte = te["label"].values
    legit = X(feature_frame, tr, feat)[tr["label"].values == 0]

    iso = IsolationForest(n_estimators=200, random_state=config.SEED).fit(legit)
    lof = LocalOutlierFactor(n_neighbors=20, novelty=True).fit(
        legit.sample(min(15000, len(legit)), random_state=0))
    rows = [["IsolationForest", round(roc_auc_score(yte, -iso.score_samples(xte)), 3)],
            ["LocalOutlierFactor", round(roc_auc_score(yte, -lof.score_samples(xte)), 3)]]
    pd.DataFrame(rows, columns=["unsupervised_detector", "auc"]).to_csv(
        config.TABLES / "T10_anomaly.csv", index=False)
    print("  unsupervised AUC:", dict(rows))


# ----------------------------------------------- Phase 8: calibration (goodness of fit)
def phase8_calibration(feature_frame, tr, te):
    print("Phase 8: probability calibration (Brier + reliability curve)")
    feat = features.FEATURE_NAMES
    mdl = models.model_zoo()["hist_gbm"].fit(X(feature_frame, tr, feat),
                                             tr["label"].values)
    p = mdl.predict_proba(X(feature_frame, te, feat))[:, 1]
    y = te["label"].values
    brier = brier_score_loss(y, p)
    frac, mean_pred = calibration_curve(y, p, n_bins=10)
    pd.DataFrame({"mean_predicted": mean_pred.round(3),
                  "observed_freq": frac.round(3)}
                 ).to_csv(config.TABLES / "T11_calibration.csv", index=False)

    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    ax.plot([0, 1], [0, 1], "--", color="grey")
    ax.plot(mean_pred, frac, "o-", color=INK)
    ax.set_xlabel("mean predicted P(phishing)")
    ax.set_ylabel("observed frequency")
    ax.set_title(f"Reliability curve (Brier {brier:.4f})")
    fig.tight_layout()
    fig.savefig(config.FIGURES / "F8_calibration.png")
    plt.close(fig)
    print(f"  Brier {brier:.4f}")


# ------------------------------------------------- Phase 9: feature-group ablation
def phase9_ablation(feature_frame, tr, te):
    print("Phase 9: feature-group ablation")
    feat = features.FEATURE_NAMES
    ytr, yte = tr["label"].values, te["label"].values
    groups = {
        "length/counts": ["url_len", "host_len", "path_len", "n_dots", "n_hyphen",
                          "n_slash", "n_digit", "digit_ratio"],
        "host/domain": ["n_subdomain", "host_hyphen", "is_ip", "has_port", "core_len"],
        "tld": ["tld_len", "suspicious_tld"],
        "entropy": ["url_entropy", "host_entropy", "core_entropy"],
        "scheme/encoding": ["is_https", "has_punycode", "has_at_symbol",
                            "has_hex_encoding"],
        "brand/cue": ["brand_min_dist", "brand_lookalike", "brand_in_subdomain",
                      "is_shortener", "n_cue_words"],
    }
    # A separate model is fitted per group, so this loop is a genuine refit loop.
    rows = []
    for name, cols in groups.items():
        cols = [c for c in cols if c in feat]
        _, p = models.fit_predict(models.model_zoo()["hist_gbm"],
                                  X(feature_frame, tr, cols), ytr,
                                  X(feature_frame, te, cols))
        m = stats.metrics(yte, p)
        rows.append([name, len(cols), round(m["f1"], 3), round(m["auc"], 3)])
    pd.DataFrame(rows, columns=["feature_group", "n_features", "f1", "auc"]).to_csv(
        config.TABLES / "T12_ablation.csv", index=False)


# --------------------------------------------------------- Phase 10: error analysis
def phase10_error(feature_frame, tr, te):
    print("Phase 10: error analysis")
    feat = features.FEATURE_NAMES
    mdl = models.model_zoo()["hist_gbm"].fit(X(feature_frame, tr, feat),
                                             tr["label"].values)
    p = mdl.predict_proba(X(feature_frame, te, feat))[:, 1]
    scored = pd.DataFrame({"URL": te["URL"].values, "y": te["label"].values, "p": p})
    scored["pred"] = (scored["p"] >= .5).astype(int)
    fp = scored[(scored.pred == 1) & (scored.y == 0)]
    fn = scored[(scored.pred == 0) & (scored.y == 1)]

    pd.DataFrame([["false_positive", len(fp)], ["false_negative", len(fn)],
                  ["test_size", len(scored)]], columns=["item", "count"]
                 ).to_csv(config.TABLES / "T13_error_counts.csv", index=False)
    examples = pd.concat([fp.head(5).assign(type="FP"), fn.head(5).assign(type="FN")])
    examples[["type", "URL", "y", "p"]].round(3).to_csv(
        config.TABLES / "T13b_error_examples.csv", index=False)
    print(f"  false positives {len(fp)}, false negatives {len(fn)} of {len(scored)}")


if __name__ == "__main__":
    started = time.time()
    emails, url_features, provided_cols, train, val, test = prepare()
    phase1(emails, url_features, provided_cols, train, test)
    phase2_eda(url_features, train)
    phase3(emails, url_features, train, test)
    phase4(url_features, train, test)          # also caches Kaggle features for phase 6
    phase5(url_features, train, test)
    phase6_shift(url_features)
    phase7_anomaly(url_features, train, test)
    phase8_calibration(url_features, train, test)
    phase9_ablation(url_features, train, test)
    phase10_error(url_features, train, test)
    print(f"done in {time.time() - started:.0f}s")
