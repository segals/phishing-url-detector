# Catching phishing from the link alone

**A URL-based phishing detector — and an honest audit of why "99% accuracy" in this field is mostly a
dataset artifact.**

Course project (Data Science & Cyber). This is the **URL / link detector** — one half of a two-part
system; a partner built the **content / text detector**. This half reads only the URL and decides
phishing vs. legitimate, then spends most of the effort showing that its near-perfect score is fragile.

## The story in one line

A simple model scores **F1 ≈ 1.0** on a large modern public URL dataset — but that number is a
collection artifact. It comes from one leaked feature and from HTTP-vs-HTTPS; it can be evaded to **0%
recall** by dressing a phishing URL up as a clean home-page; and on an **independent** dataset it
collapses to **AUC 0.43 — worse than a coin flip**. URL structure alone is not a generalizable phishing
signal — which is exactly the argument for fusing it with the content channel.

## Headline results

| | F1 | AUC |
|---|---|---|
| In-distribution (PhiUSIIL, honest lexical features) | 0.997 | 0.999 |
| One leaked feature alone (`URLSimilarityIndex`) | 0.995 | — |
| **Cross-dataset (independent Kaggle 651k)** | **0.666** | **0.434** |
| Live OpenPhish (recall) | — | recall **1.00** |

- **SHAP** pins the model on `is_https` (~3× any other feature) — the collection artifact.
- **Arms race:** structural attacks (homoglyph/typo-squat) are harmless (0.99); HTTPS-upgrade → 0.67;
  home-page mimicry → **0.00**.
- **Distance metrics (KS/Wasserstein)** show the cross-dataset collapse comes from the exact features the
  model relies on being the most shifted.

## Data (all public, all cited)

- **PhiUSIIL** — 235,795 URLs (Prasad & Chandra, 2024; UCI id 967). `scripts/fetch_data.py`.
- **Kaggle Malicious-URLs** — 651,191 URLs (Siddhartha, 2021). `scripts/fetch_kaggle.py`.
- **OpenPhish** feed + **Majestic Million** — live modern test. `scripts/fetch_modern.py`.

## Reproduce

```
pip install -r requirements.txt
python scripts/fetch_data.py        # PhiUSIIL
python scripts/fetch_kaggle.py      # Kaggle (needs a Kaggle token at ~/.kaggle/access_token)
python scripts/fetch_modern.py      # OpenPhish + Majestic
python run_all.py                   # regenerates every table + figure (seed 42, deterministic)
python scripts/build_nb.py          # notebook   (optional)
python scripts/build_report.py      # blog PDF   (optional)
python scripts/build_slides.py      # slides     (optional)
```

## Deliverables

- **`notebooks/url_detector.ipynb`** — the end-to-end story with code, tables, figures, interpretation.
- **`report/blog.pdf`** — the write-up, blog style.
- **`presentation/url_detector.pptx`** — the ~20-minute talk.

## Layout

```
src/       data · features (40 URL features) · models · stats (CIs/McNemar/cost) · attacks · normalize · explain (SHAP)
run_all.py 10 phases: artifact → EDA → arms race → cross-dataset → SHAP → distance-metrics → anomaly → calibration → ablation → error
results/   tables/ (T0..T13) and figures/ (F1..F8)
scripts/   data fetchers + the notebook/report/slide builders
```

## Course concepts used

EDA · distributions · skewness/kurtosis · robust statistics · Pearson vs Spearman · Mann–Whitney U ·
feature engineering · Shannon entropy · Levenshtein edit distance · the accuracy paradox ·
Precision/Recall/F1/**F2**/**MCC**/AUC · cost-sensitive thresholds · bootstrap CIs · McNemar ·
explainability (**SHAP**) · adversarial ML (evasion, perturbation, homoglyphs, adversarial training) ·
anomaly detection (**Isolation Forest**, **LOF**) · calibration · domain shift / concept drift ·
**distance metrics (KS, Wasserstein/EMD)** · feature ablation · error analysis.

## Honest limitations

The cross-dataset comparison is affected by differing URL encodings; the no-`is_https` variant is *worse*,
confirming the bias is diffuse. Next steps: WHOIS/domain-age and redirect-chain features, a live-feed
retraining loop, and **fusion** with the content detector (out of scope for this half).

*References: Ma 2009; Garera 2007; Sahingoz 2019; Le 2018 (URLNet); Boucher 2022; Lundberg & Lee 2017
(SHAP); Unicode TR39.*
