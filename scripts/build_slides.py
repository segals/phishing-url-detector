"""Build the ~20-minute slide deck (presentation/url_detector.pptx) from the results."""
import os, pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

INK = RGBColor(0x1d, 0x2b, 0x3a); ACCENT = RGBColor(0x2a, 0x9d, 0x8f)
RED = RGBColor(0xe7, 0x6f, 0x51); GREY = RGBColor(0x5b, 0x64, 0x72); WHITE = RGBColor(0xff, 0xff, 0xff)
TAB, FIG = "results/tables", "results/figures"

def val(tab, col, contains, valcol):
    d = pd.read_csv(f"{TAB}/{tab}.csv"); r = d[d[col].astype(str).str.contains(contains)]
    return str(r.iloc[0][valcol]) if len(r) else "?"

prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]

def _box(s, l, t, w, h):
    tb = s.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h)); tb.text_frame.word_wrap = True
    return tb.text_frame

def _run(p, text, size, color=INK, bold=False, italic=False):
    r = p.add_run(); r.text = text; f = r.font
    f.size = Pt(size); f.color.rgb = color; f.bold = bold; f.italic = italic; f.name = "Calibri"

def header(s, title, kicker=None):
    bar = s.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(0.18))
    bar.fill.solid(); bar.fill.fore_color.rgb = ACCENT; bar.line.fill.background()
    tf = _box(s, 0.6, 0.45, 12.1, 1.2)
    p = tf.paragraphs[0]; _run(p, title, 30, INK, bold=True)
    if kicker:
        p2 = tf.add_paragraph(); _run(p2, kicker, 14, ACCENT, italic=True)

def bullets(s, items, top=1.9, size=18, left=0.7, width=12.0):
    tf = _box(s, left, top, width, 5.0)
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(10)
        lvl = 0
        if it.startswith("  "): lvl = 1; it = it.strip()
        p.level = lvl
        _run(p, ("•  " if lvl == 0 else "–  ") + it, size - lvl*2, INK if lvl == 0 else GREY)

def picture(s, name, left=7.0, top=1.9, width=6.0):
    p = f"{FIG}/{name}.png"
    if os.path.exists(p): s.shapes.add_picture(p, Inches(left), Inches(top), width=Inches(width))

def slide(): return prs.slides.add_slide(BLANK)

# 1 title
s = slide()
bg = s.shapes.add_shape(1, 0, 0, prs.slide_width, prs.slide_height)
bg.fill.solid(); bg.fill.fore_color.rgb = INK; bg.line.fill.background()
tf = _box(s, 0.9, 2.4, 11.5, 3)
_run(tf.paragraphs[0], "Catching phishing from the link alone", 40, WHITE, bold=True)
p = tf.add_paragraph(); _run(p, "…and why “99% accuracy” in URL phishing detection is mostly an illusion", 20, RGBColor(0x9a,0xd1,0xc9), italic=True)
p = tf.add_paragraph(); p.space_before = Pt(24)
_run(p, "Data Science & Cyber  ·  the URL / link detector (Student B)", 15, RGBColor(0xc7,0xd0,0xd8))

# 2 the question
s = slide(); header(s, "The question", "one half of a two-part detector")
bullets(s, ["Phishing is the #1 initial-access vector — and much of it is just a link.",
            "Can we catch phishing from the URL ALONE (no page fetch, no content)?",
            "This project = the URL / link channel. My partner built the text / content channel.",
            "Built to be independent; the two are meant to be fused later.",
            "Plan: build a URL detector → get a near-perfect score → prove it is a mirage."])

# 3 data
s = slide(); header(s, "The data", "real, public, recent")
bullets(s, ["PhiUSIIL (Prasad & Chandra, 2024; UCI id 967)",
            "235,795 real URLs · 43% phishing · raw URL strings",
            "One of the largest, most recent public URL datasets",
            "Cross-dataset test later: Kaggle Malicious-URLs (651k) + live OpenPhish"], width=6.2)
picture(s, "F1_eda", left=6.9, top=2.2, width=6.1)

# 4 looks perfect
s = slide(); header(s, "It looks perfect — F1 ≈ 1.0")
bullets(s, [f"All provided features → F1 { val('T0_artifact_decomposition','representation','provided','f1') }",
            f"ONE feature (URLSimilarityIndex) → F1 { val('T0_artifact_decomposition','representation','URLSimilarityIndex','f1') }  (≈ the label: leakage)",
            f"Even honest hand-built lexical features → F1 { val('T0_artifact_decomposition','representation','honest','f1') }",
            "Majority-class baseline: 57% accuracy, 0% recall — the accuracy paradox",
            "A one-line ‘not-HTTPS → phishing’ rule alone scores F1 0.68"])
tf = _box(s, 0.7, 6.4, 12, 0.8); _run(tf.paragraphs[0], "→ the score is a DATASET ARTIFACT, not phishing detection", 20, RED, bold=True)

# 5 why: the artifact
s = slide(); header(s, "Why? The HTTPS collection artifact")
bullets(s, ["Legitimate URLs in PhiUSIIL: 100% HTTPS", "Phishing URLs: only 49% HTTPS",
            "So the model largely learns ‘HTTP = phishing’ — a collection bias, not a real signal",
            "(Real modern phishing is mostly HTTPS — this rule is backwards in the wild)"], width=6.2)
picture(s, "F5_shap", left=7.0, top=2.0, width=6.0)
tf = _box(s, 7.0, 6.6, 6, 0.6); _run(tf.paragraphs[0], "SHAP: is_https drives it (~3× any other feature)", 13, GREY, italic=True)

# 6 features
s = slide(); header(s, "40 features from the URL string alone", "feature engineering · information theory · edit distance")
bullets(s, ["Lexical: length, dots, digits, entropy of the URL/host",
            "Host/TLD: subdomains, IP-as-host, punycode, suspicious TLDs",
            "Shannon entropy H = −Σ pᵢ log₂ pᵢ  → random-looking (DGA) domains",
            "Brand look-alike = Levenshtein edit distance to a known brand (paypa1, arnazon)",
            "All computable offline → fast (~ms), private, reproducible"])

# 7 honest evaluation
s = slide(); header(s, "Evaluation done honestly", "the metric zoo + statistics")
bullets(s, ["Never accuracy alone (accuracy paradox) — report Precision/Recall/F1/F2/MCC/AUC",
            "F2 & cost-sensitive threshold: a missed phish (FN) costs more than a false alarm (FP)",
            "Bootstrap 95% CIs on every headline metric",
            "McNemar’s test on every pairwise model comparison",
            "Result: LogReg / RandomForest / HistGBM are all near-perfect & statistically tied"])

# 8 arms race
s = slide(); header(s, "Attack it, then defend it", "adversarial ML")
bullets(s, ["Structural attacks (homoglyph, typo-squat) barely dent it (0.99)",
            "  → a structural detector resists the char-tricks that BREAK text models",
            f"HTTPS-upgrade → recall { val('T3_arms_race','attack','https_upgrade','recall_attacked') }",
            f"Home-page mimicry → recall { val('T3_arms_race','attack','homepage_mimicry','recall_attacked') }  (total evasion)",
            "Normalization defeats homoglyphs; nothing URL-only defeats mimicry"], width=6.4)
picture(s, "F3_arms_race", left=7.2, top=2.3, width=5.9)

# 9 anomaly
s = slide(); header(s, "An unsupervised angle", "abnormality detection")
bullets(s, ["Train on legitimate URLs only; flag phishing as anomalies",
            f"Isolation Forest: AUC { val('T10_anomaly','unsupervised_detector','IsolationForest','auc') }",
            f"Local Outlier Factor: AUC { val('T10_anomaly','unsupervised_detector','LocalOutlierFactor','auc') }",
            "Respectable with NO labels — but below supervised, and riding the same artifacts"])

# 10 cross-dataset (the big one)
s = slide(); header(s, "The reality check: it does NOT generalize", "domain shift")
bullets(s, [f"In-distribution: F1 { val('T4_cross_dataset','setting','in-distribution','f1') }, AUC { val('T4_cross_dataset','setting','in-distribution','auc') }",
            f"Independent Kaggle 651k dataset: F1 { val('T4_cross_dataset','setting','full model','f1') }, AUC { val('T4_cross_dataset','setting','full model','auc') }",
            "  AUC < 0.5 → the ranking INVERTS (the artifact reverses across datasets)",
            f"But live OpenPhish phishing: recall { val('T4_cross_dataset','setting','OpenPhish','recall_phishing') } (today’s phishing is still messy)"], width=6.4)
picture(s, "F4_cross_dataset", left=7.2, top=2.3, width=5.9)

# 11 why it inverts — distance metrics
s = slide(); header(s, "Why it inverts — distance metrics", "KS & Wasserstein")
bullets(s, ["Measure the shift PhiUSIIL → Kaggle per feature (KS statistic)",
            "Most-shifted features = is_https, path_len, n_subdomain",
            "…which are exactly the top SHAP drivers",
            "The model built its decision on the LEAST transferable signals"], width=6.4)
picture(s, "F7_domain_shift", left=7.2, top=2.2, width=5.9)

# 12 conclusions
s = slide(); header(s, "So what is a URL detector good for?")
bullets(s, ["Fast (~ms), private, interpretable, robust to character obfuscation, catches today’s phishing",
            "BUT: URL structure alone is not a generalizable phishing signal",
            "  trivially evaded by HTTPS + legitimate hosting; collapses across datasets",
            "Right design = FUSION: link channel + content channel + reputation/domain-age",
            "So when an attacker beats one channel, another still fires"])
tf = _box(s, 0.7, 6.4, 12, 0.8); _run(tf.paragraphs[0], "Near-perfect URL benchmarks measure dataset construction, not phishing.", 19, RED, bold=True)

# 13 course concepts
s = slide(); header(s, "Course concepts used")
bullets(s, ["EDA · distributions · skewness/kurtosis · robust stats · Pearson vs Spearman · Mann–Whitney U",
            "Feature engineering · Shannon entropy · Levenshtein edit distance",
            "Accuracy paradox · P/R/F1/F2/MCC/AUC · cost thresholds · bootstrap CIs · McNemar",
            "Explainability (SHAP) · adversarial ML (evasion, homoglyphs, adversarial training)",
            "Anomaly detection (Isolation Forest, LOF) · calibration · distance metrics (KS, Wasserstein)",
            "Domain shift / concept drift · feature ablation · error analysis"], size=16)

# 14 thanks
s = slide()
bg = s.shapes.add_shape(1, 0, 0, prs.slide_width, prs.slide_height)
bg.fill.solid(); bg.fill.fore_color.rgb = INK; bg.line.fill.background()
tf = _box(s, 0.9, 3, 11.5, 2)
_run(tf.paragraphs[0], "Thank you", 40, WHITE, bold=True)
p = tf.add_paragraph(); _run(p, "github.com/segals/phishing-url-detector  ·  reproducible: python run_all.py", 16, RGBColor(0x9a,0xd1,0xc9))

os.makedirs("presentation", exist_ok=True)
prs.save("presentation/url_detector.pptx")
print(f"wrote presentation/url_detector.pptx ({len(prs.slides._sldIdLst)} slides)")
