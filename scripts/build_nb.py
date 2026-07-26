"""Assemble the presentation notebook from the computed results.

The heavy analysis lives in run_all.py (the reproducible engine); this notebook is the
narrative: it shows the key code inline, displays every result table/figure, and
interprets each one, grounded in the course concepts. Run run_all.py first, then:
    python scripts/build_nb.py   ->   notebooks/url_detector.ipynb
"""
import nbformat as nbf

def md(s): return nbf.v4.new_markdown_cell(s.strip("\n"))
def code(s): return nbf.v4.new_code_cell(s.strip("\n"))

c = []

c.append(md(r"""
# Catching phishing from the link alone
### and why "99% accuracy" in URL phishing detection is mostly an illusion

*Data Science & Cyber course project. This is the **URL / link detector** — one half of a two-part
system (my partner built the text/content detector). It reads only the URL and decides phishing vs.
legitimate, and then I spend most of the effort showing that its near-perfect score is fragile.*

**The one-line story:** a simple model scores **F1 ≈ 1.0** on a modern public URL dataset — but that
number is a *collection artifact*. It comes from a single leaked feature and from HTTP-vs-HTTPS, it can
be evaded by trivially dressing a phishing URL up as a clean home-page, and on an **independent** dataset
it collapses to **AUC 0.43 — worse than a coin flip**. Structure alone is not a generalizable phishing
signal, which is exactly the argument for fusing it with the content channel.

Every number below is produced by `run_all.py` (deterministic, seed 42) and reloaded here.
"""))

c.append(code(r"""
import sys

import numpy as np
import pandas as pd
from IPython.display import Image, display

sys.path.insert(0, "..")            # import the project's src package
from src import attacks, data, features

pd.set_option("display.max_colwidth", 70)


def T(name):
    # load a result table
    return pd.read_csv(f"../results/tables/{name}.csv")


def F(name):
    # show a result figure
    display(Image(f"../results/figures/{name}.png"))


print("helpers ready")
"""))

c.append(md(r"""
## 1. The data

**PhiUSIIL** (Prasad & Chandra, 2024; UCI ML Repository id 967) — **235,795 real URLs**, 134,850
legitimate and 100,945 phishing, each with the raw URL string. It is one of the largest and most recent
public URL datasets, which is exactly why its near-perfect benchmark scores are worth interrogating.

*Course link — EDA:* before any model, look at balance, shape, and the obvious signals.
"""))
c.append(code(r"""
df = data.working_set(data.load_phiusiil())
print(len(df), "unique URLs |", f"{df.label.mean():.1%} phishing")
display(T("T1_dataset"))
F("F1_eda")
"""))
c.append(md(r"""
Already a red flag in the EDA figure: the two classes separate almost perfectly on trivial structural
quantities. That is *too* easy — real phishing and real legitimate URLs are not this cleanly divided.
"""))

c.append(md(r"""
## 2. Feature engineering — 40 signals from the URL string alone

*Course link — feature engineering, information theory, edit distance.* I compute everything from the
URL string (no network fetch), so the detector is fast, private and reproducible. Two features carry
real theory:

- **Shannon entropy** of the host, $H(s)=-\sum_i p_i\log_2 p_i$ — random-looking (algorithmically
  generated) domains score high.
- **Brand look-alike** = the **Levenshtein edit distance** from a domain label to a known brand
  (`paypa1`, `arnazon`), the classic typo-squat signal (Ma et al. 2009; Garera et al. 2007).
"""))
c.append(code(r"""
for u in ["https://www.google.com",
          "http://paypa1-secure.account-verify.tk/login.php?id=1",
          "http://192.168.0.1/webscr/confirm"]:
    f = features.extract(u)
    print(u)
    print(f"   is_https={f['is_https']} host_entropy={f['host_entropy']:.2f} "
          f"brand_lookalike={f['brand_lookalike']} n_cue_words={f['n_cue_words']} url_len={f['url_len']}\n")
print(f"{len(features.FEATURE_NAMES)} features:", features.FEATURE_NAMES)
"""))

c.append(md(r"""
## 3. The near-perfect score is an artifact

*Course link — the accuracy paradox; "a good model can't fix bad data".* Train on the provided features
and you reproduce the published ~perfect result. But decompose it:
"""))
c.append(code('display(T("T0_artifact_decomposition"))'))
c.append(md(r"""
- **All features → F1 1.0.**
- **One feature (`URLSimilarityIndex`) → 0.995** — it is essentially a copy of the label (leakage).
- **Even my honest hand-built lexical features → 0.997** — because in this dataset legitimate URLs are
  clean HTTPS home-pages and phishing URLs are messy. The model is learning *how the dataset was built*,
  not *what makes a URL dangerous*.

The trivial baselines make the point quantitative (a single rule already looks "good"):
"""))
c.append(code('display(T("T1b_baselines"))'))
c.append(md(r"""
The majority-class baseline gets 57% accuracy with **0% recall** — the textbook accuracy paradox — and a
one-line *"not HTTPS → phishing"* rule scores F1 0.68. That single artifact (below) is doing most of the
work.
"""))

c.append(md(r"""
## 4. Deeper EDA — distribution shape, correlation, and a proper test

*Course link — distributions, skewness/kurtosis, robust statistics, Pearson vs Spearman, non-parametric
tests.* URL features are heavy-tailed, so I lead with Spearman (monotone) and medians, not Pearson/means,
and I test class differences with the non-parametric **Mann–Whitney U**.
"""))
c.append(code("""
print("distribution shape (skewness / excess kurtosis):")
display(T("T6_eda_shape"))
print("correlation with the label (Pearson vs Spearman):")
display(T("T7_correlation"))
print("Mann-Whitney U — do the classes differ?")
display(T("T8_mannwhitney"))
F("F6_correlation")
"""))
c.append(md(r"""
Every key feature differs between classes at $p \ll 0.001$ — but that significance is exactly the
artifact: `is_https` has a near-perfect monotone correlation with the label, which no real-world phishing
signal should.
"""))

c.append(md(r"""
## 5. Models and *honest* evaluation

*Course link — train/val/test, the metric zoo, statistical validity.* Logistic regression, random forest
and histogram gradient boosting, chosen on validation F1. I never trust a point estimate: every headline
metric gets a **bootstrap 95% CI**, and every pairwise comparison a **McNemar test**. I report **MCC**
and **F2** (a missed phishing costs more than a false alarm), not just accuracy.
"""))
c.append(code('display(T("T2_model_comparison"))'))
c.append(md("The models are statistically indistinguishable and all near-perfect — again, "
            "because the task is artificially easy in-distribution."))

c.append(md(r"""
## 6. What is the model actually using? (SHAP)

*Course link — explainability.* Tree models aren't linear, so I use **SHAP** (Lundberg & Lee, 2017) for
faithful per-feature attribution.
"""))
c.append(code("""
display(T("T5_shap_importance").head(8))
F("F5_shap")
"""))
c.append(md(r"""
The #1 driver is **`is_https`** by a factor of ~3, followed by path/structure features. The model is a
thin veneer over the collection artifact — which is precisely why the attacks in the next section work.
"""))

c.append(md(r"""
## 7. The arms race — attack the detector, then defend it

*Course link — adversarial ML: evasion, perturbation, homoglyphs, transferability, adversarial training.*
The attacker keeps the URL usable but shifts its surface toward "legitimate".
"""))
c.append(code(r"""
rng = np.random.default_rng(0)
u = "http://paypal-verify.account-login.tk/webscr?cmd=login"
for k, fn in attacks.ATTACKS.items():
    print(f"{k:16s} {fn(u, rng)}")
print("\nrecall on phishing under each attack / defense:")
display(T("T3_arms_race"))
F("F3_arms_race")
"""))
c.append(md(r"""
Two honest findings:
- **Structural attacks (homoglyph, typosquat) barely dent it** (0.99) — a *structural* URL detector is
  robust to the character tricks that *break* my partner's text model. A nice complementarity.
- **The artifact is the hole:** flipping HTTP→HTTPS drops recall to 0.67; full home-page mimicry drops
  it to **0.00**. Normalization (the homoglyph defense) correctly does nothing here, and dropping
  `is_https` barely helps — the bias is diffuse. There is no URL-only fix; the answer is a second signal.
"""))

c.append(md(r"""
## 8. An unsupervised angle — anomaly detection

*Course link — abnormality detection: Isolation Forest, Local Outlier Factor.* If phishing is "unusual",
can we catch it *without labels*, training only on legitimate URLs?
"""))
c.append(code('display(T("T10_anomaly"))'))
c.append(md(r"""
Isolation Forest reaches AUC 0.83 and LOF 0.94 with **no phishing labels at all** — respectable, but well
below the supervised model, and still riding the same structural artifacts.
"""))

c.append(md(r"""
## 9. Are the probabilities trustworthy? (calibration)

*Course link — goodness of fit / calibration.*
"""))
c.append(code("""
display(T("T11_calibration"))
F("F8_calibration")
"""))
c.append(md("In-distribution the model is very well calibrated (low Brier) — but as the next "
            "section shows, that calibration does **not** survive a change of dataset."))

c.append(md(r"""
## 10. The reality check — cross-dataset generalization

*Course link — domain shift / concept drift, and distance metrics (KS, Wasserstein).* The real question:
does the score survive a **different** dataset? I test on the independent **Kaggle Malicious-URLs** set
(Siddhartha 2021, 651k URLs; phishing vs. benign), and on the **live OpenPhish** feed.
"""))
c.append(code("""
display(T("T4_cross_dataset"))
F("F4_cross_dataset")
"""))
c.append(md(r"""
The near-perfect model (in-dist F1 0.997, AUC 0.999) collapses to **F1 0.67 / AUC 0.43 — worse than
random**. The boxplot shows why: in-distribution the two classes are cleanly separated (legit near 0,
phishing near 1), but on the Kaggle set **both classes collapse to the same saturated region near 1.0**
(mean score 1.000 for benign, 0.999 for phishing — the model isn't just less confident, it can no longer
tell the classes apart at all). AUC < 0.5 means that within that saturated band, benign URLs score
*fractionally higher* than phishing on average — a true inversion, not just noise. Yet it still catches
**100% of live OpenPhish phishing**, because today's real phishing is *still* structurally messy.

*Why* does it invert? Distance metrics make it concrete — the most-shifted features between the two
datasets are exactly the ones the model relies on:
"""))
c.append(code("""
display(T("T9_domain_shift").head(8))
F("F7_domain_shift")
"""))
c.append(md(r"""
`is_https`, `path_len`, `n_subdomain` — the top SHAP drivers — are also the top KS-shifted features. The
model built its decision on the least transferable signals. This is the URL analogue of my partner's
cross-corpus collapse, but more severe (AUC below 0.5 vs her 0.78).
"""))

c.append(md(r"""
## 11. Feature ablation and error analysis
"""))
c.append(code("""
print("which feature groups carry the (in-distribution) signal:")
display(T("T12_ablation"))
print("errors on the clean test set:")
display(T("T13_error_counts"))
display(T("T13b_error_examples"))
"""))
c.append(md(r"""
The `scheme/encoding` group (which is basically `is_https`) alone nearly matches the full model — the
ablation confirms the artifact. On clean data the model makes very few errors, all borderline; the danger
is not clean-data mistakes but the obfuscation and domain-shift failures above.
"""))

c.append(md(r"""
## 12. Conclusions

**What I built:** a fast, interpretable, URL-only phishing detector, and an honest audit of it.

**What I found:**
1. The near-perfect public benchmark (F1 1.0) is a **collection artifact** — one leaked feature, and
   HTTP-vs-HTTPS. SHAP and the ablation both pin it on `is_https`.
2. A structural detector is **robust to homoglyph/typo tricks** (unlike a text model) but is **evaded by
   home-page mimicry** (recall → 0).
3. It **does not generalize**: on an independent dataset it drops to **AUC 0.43**, and distance metrics
   show why — the features it trusts are the ones that shift most.
4. It still catches **current** real phishing (OpenPhish recall 1.0), so it is useful *today* as one
   layer — but a brittle one.

**The headline:** URL structure alone is not a generalizable phishing signal. The right use is as an
**independent channel fused with content** (my partner's half) and with non-lexical signals (domain age,
reputation) — so that when an attacker defeats one channel, another still fires.

### Course concepts used, and where
| Concept | Where |
|---|---|
| EDA, distributions, skewness/kurtosis, robust statistics | §1, §4 |
| Correlation: Pearson vs Spearman; Mann–Whitney U | §4 |
| Feature engineering; Shannon entropy; Levenshtein edit distance | §2 |
| Accuracy paradox; Precision/Recall/F1/**F2**/**MCC**/AUC; cost-sensitive threshold | §3, §5 |
| Statistical validity: bootstrap CIs, McNemar | §5 |
| Explainability (SHAP) | §6 |
| Adversarial ML: evasion, perturbation, homoglyphs, transferability, adversarial training | §7 |
| Anomaly detection: Isolation Forest, LOF | §8 |
| Calibration / goodness of fit | §9 |
| Domain shift / concept drift; **distance metrics (KS, Wasserstein/EMD)** | §10 |
| Dimensionality via feature-group ablation; error analysis | §11 |

**Limitations & future work:** the cross-dataset comparison is affected by differing URL encodings
(schemes) — I control for it with the no-`is_https` variant, which is *worse*, confirming the bias is
diffuse. Next: WHOIS/domain-age and redirect-chain features, a live-feed retraining loop, and the
**fusion** with the content detector (deliberately out of scope for this half).

*References:* Prasad & Chandra 2024 (PhiUSIIL); Siddhartha 2021 (Kaggle Malicious URLs); OpenPhish;
Majestic Million; Ma et al. 2009; Garera et al. 2007; Sahingoz et al. 2019; Le et al. 2018 (URLNet);
Boucher et al. 2022 (Bad Characters); Lundberg & Lee 2017 (SHAP); Unicode TR39 (confusables).
"""))

nb = nbf.v4.new_notebook()
nb.cells = c
nb.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
               "language_info": {"name": "python", "version": "3.10"}}
nbf.write(nb, "notebooks/url_detector.ipynb")
print("wrote notebooks/url_detector.ipynb")
