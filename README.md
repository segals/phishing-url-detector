# Catching phishing from the link alone

**A URL-based phishing detector — and an honest audit of why "99% accuracy" in this field is mostly a
dataset artifact.**

**Gilad Segal** — Data Science & Cyber (Dr. Uri Itai).

This is the **URL / link detector** — one half of a two-part project; a partner built the
**content / text detector**. This half reads only the URL and decides phishing vs. legitimate, then
spends most of the effort showing that its near-perfect score is fragile.

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

- **PhiUSIIL** — 235,795 URLs (Prasad & Chandra, 2024; UCI id 967) — training/testing. `scripts/fetch_data.py`.
- **Kaggle Malicious-URLs** — 651,191 URLs (Siddhartha, 2021) — the independent cross-dataset test. `scripts/fetch_kaggle.py`.
- **OpenPhish** live feed — 300 current real phishing URLs. `scripts/fetch_modern.py`
  (the same script also caches Majestic Million top domains, used only in early exploratory checks —
  they are not part of any reported result).

## Reproduce

```
pip install -r requirements.txt
python scripts/fetch_data.py        # PhiUSIIL
python scripts/fetch_kaggle.py      # Kaggle (needs a Kaggle token at ~/.kaggle/access_token)
python scripts/fetch_modern.py      # OpenPhish + Majestic
python run_all.py                   # regenerates every table + figure (seed 42, deterministic)
python scripts/build_nb.py          # notebook   (optional)
python scripts/build_report.py      # submission report PDF (optional)
python scripts/build_slides.py      # slides     (optional)
```

## Deliverables

- **`report/report.pdf`** — the formal submission report (13 pages: contents, abstract, numbered sections,
  every table and figure with captions and interpretation, references).
- **`presentation/url_detector.pptx`** — the ~15-minute talk (with speaker notes). This file was
  hand-edited after generation and is the authoritative version; `scripts/build_slides.py` would
  overwrite it.
- **`notebooks/url_detector.ipynb`** — the end-to-end story with code, tables, figures, interpretation.

## Layout

```
src/       data · features (40 URL features) · models · stats (CIs/McNemar/cost) · attacks · normalize · explain (SHAP)
run_all.py 10 phases: artifact → EDA → arms race → cross-dataset → SHAP → distance-metrics → anomaly → calibration → ablation → error
results/   tables/ (17 CSVs, T0..T13b + data_hash.txt) and figures/ (F1..F8) — all used in the report
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

*References: Prasad & Chandra 2024 (PhiUSIIL); Siddhartha 2021 (Kaggle Malicious-URLs); OpenPhish;
Ma et al. 2009; Le et al. 2018 (URLNet); Boucher et al. 2022; Lundberg & Lee 2017 (SHAP).*
