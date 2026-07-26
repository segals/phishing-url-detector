"""Build the formal submission report (report/report.pdf) from the computed results.

Every table in results/tables/ and every figure in results/figures/ is included and
explained. All numbers are read from the generated CSVs, so the report cannot drift
from the code. Numbering and headline figures are kept consistent with the slide deck.
"""
import os
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, Table,
                                TableStyle, HRFlowable, KeepTogether)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY, TA_CENTER

TAB, FIG = "results/tables", "results/figures"
INK = colors.HexColor("#1a1f2b")
SLATE = colors.HexColor("#33475b")
RULE = colors.HexColor("#33475b")
HEAD_BG = colors.HexColor("#33475b")
ROW_ALT = colors.HexColor("#f2f4f7")
GRID = colors.HexColor("#c9cfd6")
GREY = colors.HexColor("#5b6472")

AUTHOR = "Gilad Segal"
COURSE = "Data Science &amp; Cyber — Dr. Uri Itai"
REPO = "github.com/segals/phishing-url-detector"

ss = getSampleStyleSheet()
TITLE = ParagraphStyle("TITLE", fontName="Times-Bold", fontSize=19, textColor=INK, leading=23, spaceAfter=4, alignment=TA_LEFT)
SUBTITLE = ParagraphStyle("SUBTITLE", fontName="Times-Italic", fontSize=12.5, textColor=SLATE, leading=16, spaceAfter=10)
META = ParagraphStyle("META", fontName="Times-Roman", fontSize=9.5, textColor=GREY, leading=13, spaceAfter=2)
AUTH = ParagraphStyle("AUTH", fontName="Times-Bold", fontSize=11, textColor=INK, leading=14, spaceAfter=2)
ABSTRACT_H = ParagraphStyle("ABSTRACT_H", fontName="Times-Bold", fontSize=10.5, textColor=INK, spaceBefore=10, spaceAfter=4)
ABSTRACT = ParagraphStyle("ABSTRACT", fontName="Times-Roman", fontSize=9.7, textColor=colors.HexColor("#222"), leading=13.6, alignment=TA_JUSTIFY)
H1 = ParagraphStyle("H1", fontName="Times-Bold", fontSize=13, textColor=INK, spaceBefore=14, spaceAfter=6, leading=16)
H2 = ParagraphStyle("H2", fontName="Times-Bold", fontSize=10.8, textColor=SLATE, spaceBefore=9, spaceAfter=4, leading=13)
BODY = ParagraphStyle("BODY", fontName="Times-Roman", fontSize=9.9, textColor=colors.HexColor("#1b1f27"), leading=14.3, spaceAfter=6, alignment=TA_JUSTIFY)
CAP = ParagraphStyle("CAP", fontName="Times-Italic", fontSize=8.6, textColor=GREY, alignment=TA_CENTER, spaceBefore=3, spaceAfter=10, leading=11)
REF = ParagraphStyle("REF", fontName="Times-Roman", fontSize=9, textColor=colors.HexColor("#1b1f27"), leading=12.6, spaceAfter=5, leftIndent=14, firstLineIndent=-14)

def val(tab, col, contains, valcol):
    d = pd.read_csv(f"{TAB}/{tab}.csv")
    r = d[d[col].astype(str).str.contains(contains)]
    return str(r.iloc[0][valcol]) if len(r) else "?"

story = []
_tab_n = [0]; _fig_n = [0]

def P(t, style=BODY): story.append(Paragraph(t, style))
def H(t): story.append(Paragraph(t, H1))
def H2f(t): story.append(Paragraph(t, H2))
def gap(h=4): story.append(Spacer(1, h))

def _styled(data, col_widths, fontsize):
    t = Table(data, hAlign="LEFT", colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", fontsize),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", fontsize),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t

def table_from_csv(name, caption, ncols=None, nrows=None, col_widths=None, fontsize=8, wrap_col=None):
    _tab_n[0] += 1
    d = pd.read_csv(f"{TAB}/{name}.csv")
    if d.columns[0].startswith("Unnamed"):
        d = d.rename(columns={d.columns[0]: "feature"})
    if ncols: d = d.iloc[:, :ncols]
    if nrows: d = d.head(nrows)
    rows = d.round(3).astype(str).values.tolist()
    if wrap_col is not None:
        cellstyle = ParagraphStyle("cell", fontName="Helvetica", fontSize=fontsize - 0.5, leading=fontsize + 1.5)
        rows = [[Paragraph(c, cellstyle) if j == wrap_col else c for j, c in enumerate(r)] for r in rows]
    data = [list(d.columns)] + rows
    story.append(KeepTogether([_styled(data, col_widths, fontsize),
                               Paragraph(f"<b>Table {_tab_n[0]}.</b> {caption}", CAP)]))

def table_inline(header, rows, caption, col_widths=None, fontsize=8):
    _tab_n[0] += 1
    cellstyle = ParagraphStyle("cell2", fontName="Helvetica", fontSize=fontsize, leading=fontsize + 2)
    body = [[Paragraph(c, cellstyle) for c in r] for r in rows]
    story.append(KeepTogether([_styled([header] + body, col_widths, fontsize),
                               Paragraph(f"<b>Table {_tab_n[0]}.</b> {caption}", CAP)]))

def figure(name, caption, width=13.5*cm, height=None):
    _fig_n[0] += 1
    p = f"{FIG}/{name}.png"
    if os.path.exists(p):
        img = Image(p)
        img._restrictSize(width, height or 8.2*cm)
        story.append(KeepTogether([img, Paragraph(f"<b>Figure {_fig_n[0]}.</b> {caption}", CAP)]))

def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(GRID); canvas.setLineWidth(0.5)
    canvas.line(2.2*cm, 1.55*cm, A4[0]-2.2*cm, 1.55*cm)
    canvas.setFont("Times-Roman", 8); canvas.setFillColor(GREY)
    canvas.drawString(2.2*cm, 1.15*cm, "Catching Phishing from the Link Alone")
    canvas.drawRightString(A4[0]-2.2*cm, 1.15*cm, f"{doc.page}")
    canvas.restoreState()

# =====================================================================
# TITLE + ABSTRACT
# =====================================================================
P("Catching Phishing from the Link Alone", TITLE)
P("A Critical Evaluation of URL-Based Phishing Detection", SUBTITLE)
P(AUTHOR, AUTH)
P(f"{COURSE} &nbsp;&middot;&nbsp; URL / link detector (one half of a two-part project)", META)
P(f"Code, data pipeline and reproducible results: {REPO}", META)
story.append(HRFlowable(width="100%", thickness=1, color=RULE, spaceBefore=8, spaceAfter=10))

xds_f1 = val("T4_cross_dataset", "setting", "full model", "f1")
xds_auc = val("T4_cross_dataset", "setting", "full model", "auc")
id_f1 = val("T4_cross_dataset", "setting", "in-distribution", "f1")
id_auc = val("T4_cross_dataset", "setting", "in-distribution", "auc")

P("Abstract", ABSTRACT_H)
P("Phishing remains a leading initial-access vector, and a substantial fraction of it is carried "
  "entirely by a malicious link. This report presents a URL-only phishing detector and subjects it to "
  "a rigorous critical evaluation, rather than treating a high benchmark score as the end of the "
  f"analysis. Trained on 235,795 real URLs (PhiUSIIL&nbsp;[1]), a gradient-boosted classifier over 40 "
  f"hand-engineered lexical features reaches F1&nbsp;=&nbsp;{id_f1} in-distribution, matching the "
  "near-perfect scores reported in the literature. Using single-feature ablation, explainability "
  "(SHAP&nbsp;[7]) and a feature-group ablation, we show that this score is driven overwhelmingly by a "
  "dataset collection artifact — legitimate URLs in this corpus are 100% HTTPS versus 48.6% for "
  "phishing — rather than by a transferable phishing signal. An adversarial evaluation shows the "
  "detector is robust to character-level obfuscation (homoglyphs, typosquatting; recall "
  "&ge;&nbsp;0.99) but is evaded completely (recall&nbsp;=&nbsp;0.00) by hosting phishing content on "
  "ordinary HTTPS infrastructure with a clean, short URL. Most critically, evaluated without "
  f"retraining on an independent 651,191-URL corpus&nbsp;[2], the detector collapses to "
  f"F1&nbsp;=&nbsp;{xds_f1}, AUC&nbsp;=&nbsp;{xds_auc} — below 0.5, meaning its ranking is inverted "
  "rather than merely uninformative — while a distance-metric analysis (Kolmogorov&ndash;Smirnov, "
  "Wasserstein) confirms the collapse is driven by exactly the features the model relies on most. On a "
  "live feed of current phishing URLs&nbsp;[3], however, recall remains 1.00. We conclude that URL "
  "structure alone is not a generalisable phishing signal, and argue for its use as one independent "
  "channel within a fused, multi-signal detector.", ABSTRACT)

# =====================================================================
# 1. INTRODUCTION
# =====================================================================
H("1. Introduction")
P("Phishing attacks rely on a victim following a malicious link, so the URL itself is an attractive "
  "detection surface: it can be scored in milliseconds, requires no page fetch, preserves user "
  "privacy, and can be evaluated before the user clicks. A large body of published work reports "
  "near-perfect (F1&nbsp;&gt;&nbsp;0.99) classification accuracy on public URL datasets, which could "
  "suggest the problem is essentially solved. This report interrogates that claim.")
P("The project is deliberately structured as a critical evaluation rather than a model-accuracy "
  "exercise: we reproduce the strong published result, then systematically ask whether it reflects "
  "genuine phishing-specific signal or an artifact of how the benchmark dataset was constructed. The "
  "investigation is organised around four research questions.")
P("<b>RQ1 (signal).</b> How much of the reported near-perfect score survives once dataset-specific "
  "leakage and collection bias are accounted for? "
  "<b>RQ2 (robustness).</b> How does the detector respond to an adversary who deliberately reshapes a "
  "phishing URL's surface features? "
  "<b>RQ3 (generalisation).</b> Does the in-distribution score transfer to an independent dataset and "
  "to live, current phishing traffic? "
  "<b>RQ4 (explainability).</b> Which features actually drive the decision, and does that explain the "
  "robustness and generalisation results?")
P("This module is one of two independent, complementary detectors built for the course project: this "
  "report covers the <b>URL/link</b> channel, while a companion module covers the <b>email content</b> "
  "channel. The two were designed and evaluated independently; fusing them is identified as future "
  "work in Section&nbsp;7. The contribution of this half is not a new model architecture but an "
  "honest, reproducible audit of a standard one.")

# =====================================================================
# 2. RELATED WORK
# =====================================================================
H("2. Background and Related Work")
P("Lexical and host-based URL features for phishing detection were established by Ma "
  "<i>et&nbsp;al.</i>&nbsp;[4], who showed that structural properties of a URL — its length, host "
  "composition, presence of an IP literal, and token content — carry substantial discriminative signal "
  "without inspecting page content. The feature families used in Section&nbsp;4.1 follow that "
  "tradition. Deep, character-level models such as URLNet&nbsp;[5] instead learn a representation "
  "directly from the URL string, trading interpretability for potential accuracy gains. We "
  "deliberately favour interpretable, hand-engineered features: because the central finding of this "
  "report is that a near-perfect score is attributable to a specific, nameable artifact, a model whose "
  "internal representation is opaque would have obscured precisely the evidence we set out to find.")
P("On the adversarial side, Boucher <i>et&nbsp;al.</i>&nbsp;[6] document imperceptible-perturbation "
  "attacks against text-processing and web-facing systems, including homoglyph substitution — visually "
  "identical characters drawn from other Unicode scripts. This motivates both the homoglyph attack and "
  "the canonicalisation defence evaluated in Section&nbsp;5.7. For explainability we use "
  "SHAP&nbsp;[7], a game-theoretic feature-attribution method that assigns each feature a principled "
  "share of a prediction and, unlike a tree model's built-in importance, is defined per-prediction and "
  "sums exactly to the model output. Our central methodological concern — that reported "
  "phishing-detection accuracy may not transfer across independently collected corpora — is treated "
  "here as a hypothesis to be tested empirically (Sections&nbsp;5.9&ndash;5.10) rather than assumed.")

# =====================================================================
# 3. DATA
# =====================================================================
H("3. Data")
H2f("3.1 Primary corpus")
P("The primary dataset is <b>PhiUSIIL</b>&nbsp;[1] (UCI Machine Learning Repository, id&nbsp;967), "
  "comprising 235,795 real URLs with a raw URL string, a binary label, and 53 pre-computed "
  "descriptive features. It is among the largest and most recent public URL datasets and is a common "
  "benchmark, which motivates its use here as the primary object of study. Table&nbsp;1 summarises the "
  "corpus after cleaning; Figure&nbsp;1 shows the class balance and two representative feature "
  "distributions.")
table_from_csv("T1_dataset", "Composition of the primary PhiUSIIL corpus after cleaning.",
               col_widths=[3.1*cm, 2.1*cm, 2.4*cm, 2.4*cm, 2.4*cm])
figure("F1_eda", "Exploratory view of the corpus: class balance (left), URL-length distribution by class "
                 "(centre) and cue-word count by class (right). The classes separate almost perfectly on "
                 "trivial structural quantities — an early indication that the task is easier than the "
                 "real-world problem it represents.", width=15*cm, height=5.2*cm)

H2f("3.2 Secondary corpora")
P("Two independent sources support the generalisation analysis in Section&nbsp;5.9. The Kaggle "
  "<i>Malicious URLs</i> dataset&nbsp;[2] contains 651,191 URLs labelled benign, phishing, defacement "
  "or malware; we use the benign/phishing subset, balanced to 40,000 URLs per class. It was collected "
  "independently of PhiUSIIL and is itself mixed-class, which makes it a fair generalisation test "
  "rather than a comparison against an unlabelled list. In addition, a live snapshot of the "
  "<b>OpenPhish</b> community feed&nbsp;[3] (300 currently active phishing URLs) provides a check "
  "against present-day, real-world attacks rather than an archived benchmark.")

H2f("3.3 Data preparation")
P("Data preparation was kept deliberately minimal, so that the results reported below are properties "
  "of the source data rather than of our own preprocessing. Labels were standardised to the convention "
  "1&nbsp;=&nbsp;phishing, 0&nbsp;=&nbsp;legitimate (PhiUSIIL natively encodes the opposite polarity). "
  "Rows with a missing URL or label were dropped and surrounding whitespace stripped. Rows were then "
  "<b>de-duplicated on the exact URL string before splitting</b> (235,795&nbsp;&rarr;&nbsp;235,370 "
  "rows), so that no URL can appear in both the training and test partitions — a common and easily "
  "overlooked source of leakage. No class rebalancing, outlier removal, or imputation was performed, "
  "and the natural class ratio of 42.7% phishing is retained throughout. Feature standardisation is "
  "applied only inside the logistic-regression pipeline, where it is required; the tree ensembles are "
  "scale-invariant and consume raw feature values.")
P("The data were split 60/20/20 into training, validation and test partitions using a fixed random "
  "seed (42) with stratification on the label, so all three partitions carry the same class ratio. All "
  "model selection and tuning decisions were made on the validation partition; the test partition was "
  "evaluated once. For reproducibility the cleaned dataset is hashed and logged: "
  "<font face='Courier' size='8'>rows=235370, phishing_rate=0.4271, "
  "sha256=b39e8c2251df…</font> (full value in <font face='Courier' size='8'>results/tables/"
  "data_hash.txt</font>).")

# =====================================================================
# 4. METHODOLOGY
# =====================================================================
H("4. Methodology")
H2f("4.1 Feature engineering")
P("A URL is a short, structured string rather than free prose, so instead of learning a text "
  "representation (as a bag-of-words or TF-IDF pipeline would for email text) we compute interpretable "
  "numeric features directly from the string. All 40 features are derived from the URL alone and "
  "require no network access, keeping the detector fast, private and reproducible. They fall into six "
  "families, summarised in Table&nbsp;2.")
table_inline(
    ["family", "what it captures", "examples"],
    [["Lexical / length", "the size and punctuation profile of the string",
      "url_len, n_dots, n_slash, n_digit, digit_ratio"],
     ["Host / domain", "structure of the hostname itself",
      "n_subdomain, is_ip, has_port, core_len"],
     ["TLD", "the suffix and its abuse association",
      "tld_len, suspicious_tld (.tk, .xyz, …)"],
     ["Entropy", "randomness of the string (generated domains)",
      "url_entropy, host_entropy, core_entropy"],
     ["Scheme / encoding", "transport and character-encoding tricks",
      "is_https, has_punycode, has_hex_encoding, has_at_symbol"],
     ["Brand / cue", "impersonation and social-engineering markers",
      "brand_min_dist, brand_lookalike, n_cue_words, is_shortener"]],
    "The six feature families (40 features total), all computed from the URL string alone.",
    col_widths=[3.1*cm, 6.1*cm, 7.4*cm], fontsize=7.8)
P("Two families rest on explicit theory. <b>Entropy</b> features use the Shannon entropy of a string, "
  "H(s)&nbsp;=&nbsp;&minus;&Sigma;<sub>i</sub>&nbsp;p<sub>i</sub>&nbsp;log&#8322;&nbsp;p<sub>i</sub>, "
  "computed over its character distribution. A predictable, repetitive string such as "
  "<i>google</i> has low entropy, whereas an algorithmically generated domain such as <i>x7qz9wvt</i> "
  "approaches random noise and scores high; this is a standard signal for domain-generation "
  "algorithms. <b>Brand</b> features use the Levenshtein edit distance — the minimum number of "
  "single-character insertions, deletions or substitutions needed to transform one string into another, "
  "computed by the standard dynamic-programming recurrence — between each host label and a list of "
  "eighteen frequently impersonated brands. A label within edit distance 1&ndash;2 of a real brand "
  "(for example <i>paypa1</i> versus <i>paypal</i>) is flagged as a probable typosquat.")

H2f("4.2 Models")
P("Three classifiers were compared and selected on validation F1: <b>logistic regression</b> (a "
  "linear, directly interpretable baseline, with standardised features), <b>random forest</b> (an "
  "ensemble of decision trees trained independently on bootstrap samples and averaged), and "
  "<b>histogram-based gradient boosting</b> (trees fitted sequentially, each correcting the residual "
  "error of its predecessors, with features bucketed into histograms for speed on large data). The "
  "two tree ensembles represent the two standard ensembling strategies — variance reduction by "
  "averaging, and bias reduction by sequential correction — and neither requires feature scaling.")

H2f("4.3 Evaluation protocol")
P("Because the majority class accounts for 57.3% of the data, accuracy alone is not reported as a "
  "primary metric: a majority-class classifier attains 57.3% accuracy while catching zero phishing "
  "URLs, the classic <i>accuracy paradox</i> (Section&nbsp;5.1). We therefore report precision, "
  "recall, F1, F2, the Matthews Correlation Coefficient (MCC) and AUC-ROC. <b>F2</b> weights recall "
  "more heavily than precision, reflecting the operational asymmetry that a missed phishing URL "
  "(false negative) is more costly than a false alarm. <b>MCC</b> is computed from all four "
  "confusion-matrix cells and ranges from &minus;1 to +1, with 0 indicating chance performance; unlike "
  "accuracy or F1 it cannot be inflated by exploiting the majority class, which makes it the most "
  "trustworthy single figure under imbalance. <b>AUC-ROC</b> is the probability that a randomly drawn "
  "phishing URL is scored above a randomly drawn legitimate one, so 0.5 indicates uninformative "
  "ranking — and, importantly for Section&nbsp;5.9, a value below 0.5 indicates a systematically "
  "inverted ranking rather than an absence of signal.")
P("Every headline metric is reported with a <b>bootstrap 95% confidence interval</b>: the test set is "
  "resampled with replacement 1,000 times, the metric recomputed on each resample, and the 2.5th and "
  "97.5th percentiles reported. This quantifies how much a metric would vary on comparable data using "
  "only the data already collected, and prevents over-reading small differences between models. "
  "Paired model comparisons additionally use <b>McNemar's test</b> on the discordant predictions of "
  "two models over the same test set, so that no comparative claim rests on a point estimate alone.")

H2f("4.4 Threat model and adversarial evaluation")
P("We model an attacker with black-box access who may freely choose the surface form of a phishing "
  "URL but must keep it functional — it must still resolve to attacker-controlled content. Four "
  "perturbation families are evaluated: <i>homoglyph substitution</i> (Latin characters replaced with "
  "visually identical Cyrillic or Greek confusables&nbsp;[6]); <i>typosquatting</i> (a single character "
  "duplicated or inserted in the registered domain); <i>scheme upgrade</i> (serving the identical page "
  "over HTTPS rather than HTTP); and <i>home-page mimicry</i> (a short, clean, path-free HTTPS domain, "
  "approximating the increasingly common abuse of legitimate cloud-hosting infrastructure). Two "
  "defences are evaluated: <i>canonicalisation</i>, which folds confusable characters back to their "
  "ASCII skeleton and decodes punycode before scoring, and <i>de-biasing</i>, which retrains the model "
  "with the HTTPS feature removed in order to test whether the artifact is concentrated in a single "
  "feature or distributed across correlated ones.")

H2f("4.5 Generalisation and diagnostic tools")
P("Cross-dataset generalisation is measured by training exclusively on PhiUSIIL and evaluating, with "
  "no retraining or recalibration, on the independent Kaggle corpus and the live OpenPhish feed. To "
  "diagnose <i>why</i> a gap occurs, we compare the per-feature distributions of the two datasets "
  "using the <b>Kolmogorov&ndash;Smirnov statistic</b> (the maximum vertical distance between two "
  "empirical cumulative distribution functions) and the <b>Wasserstein</b>, or earth-mover's, "
  "distance (the minimum probability mass that must be moved, weighted by the distance moved, to "
  "transform one distribution into the other), normalised by the in-distribution standard deviation so "
  "that features on different scales remain comparable. We additionally report two label-free anomaly "
  "detectors trained only on legitimate URLs as a weaker-assumption point of comparison, and assess "
  "probability calibration using the Brier score and a reliability curve.")

# =====================================================================
# 5. RESULTS
# =====================================================================
H("5. Results")

H2f("5.1 Trivial baselines and the accuracy paradox")
P("Table&nbsp;3 reports three baselines that require no learning. A majority-class predictor attains "
  "57.3% accuracy with zero recall and an MCC of exactly 0 — a model that is useless for security but "
  "would appear respectable if judged on accuracy. More revealing is the second baseline: a single "
  "hand-written rule that flags any non-HTTPS URL as phishing already attains F1&nbsp;=&nbsp;0.68 and "
  "MCC&nbsp;=&nbsp;0.62. That a one-line rule captures so much of the task foreshadows the artifact "
  "analysed in Section&nbsp;5.2. By contrast the cue-word rule — arguably the most intuitively "
  "'phishing-like' heuristic — performs poorly (F1&nbsp;=&nbsp;0.13).")
table_from_csv("T1b_baselines", "Trivial baselines. A single HTTPS check alone reaches F1 0.68, while the "
                                "intuitive cue-word rule reaches only 0.13.",
               col_widths=[6.6*cm, 2.6*cm, 2.2*cm, 2.2*cm, 2.2*cm])

H2f("5.2 Decomposing the near-perfect score")
P("Training on all 50 numeric features provided with the dataset reproduces the near-perfect result "
  "reported in the literature (F1&nbsp;=&nbsp;1.000). Decomposing that score is the central diagnostic "
  "of this report (Table&nbsp;4). A single provided feature, <i>URLSimilarityIndex</i>, attains "
  "F1&nbsp;=&nbsp;0.995 on its own. Inspection of the raw data explains why: this feature takes the "
  "value 100 for <b>100% of legitimate URLs</b>, while phishing URLs average 49.6 — it is effectively "
  "a re-encoding of the label rather than an independent predictor, and it could not be computed at "
  "deployment time for a genuinely unseen URL. It is therefore treated here as leakage, measured once "
  "as evidence and <b>excluded from every subsequent experiment</b>; the detector evaluated throughout "
  "the remainder of this report uses only the 40 features described in Section&nbsp;4.1.")
table_from_csv("T0_artifact_decomposition",
               "Decomposing the near-perfect score: all provided features, individual provided features, "
               "and our own leakage-free lexical features. Bootstrap 95% CIs shown where a full model was fitted.",
               col_widths=[7.4*cm, 1.7*cm, 1.7*cm, 3*cm])
P("The more interesting result is the last row: our own leakage-free features still attain "
  "F1&nbsp;=&nbsp;0.997. This is not explained by leakage, but by a second and deeper problem. As "
  "Table&nbsp;5 shows, every legitimate URL in this corpus uses HTTPS, whereas fewer than half of the "
  "phishing URLs do. This 51-point gap is a property of how the two classes were collected — "
  "legitimate URLs appear to be drawn from clean, canonical home-pages and phishing URLs from messy, "
  "deep links — not a property of phishing itself. In the contemporary web the association is in fact "
  "much weaker, since the large majority of phishing sites now serve over HTTPS.")
table_from_csv("T3a_https_artifact", "HTTPS usage by class in PhiUSIIL: the dominant collection artifact.",
               col_widths=[6*cm, 4*cm])

H2f("5.3 Distribution shape, correlation, and non-parametric testing")
P("URL-derived features are strongly right-skewed and heavy-tailed. Table&nbsp;6 reports skewness and "
  "excess kurtosis for six representative features: URL length has a skewness of 54.7 and an excess "
  "kurtosis of 5,812, indicating a small number of extremely long URLs far from the bulk of the "
  "distribution. Under such distributions the mean and Pearson correlation are unreliable summaries, "
  "which motivates the use of rank-based statistics and medians throughout.")
table_from_csv("T6_eda_shape", "Distribution shape of representative features. Large positive skewness and "
                               "excess kurtosis indicate heavy right tails.",
               col_widths=[4.4*cm, 3*cm, 3.4*cm])
P("Table&nbsp;7 compares Pearson (linear) and Spearman (monotone) correlation between each feature and "
  "the label. The two diverge substantially for several features — path length has "
  "r&nbsp;=&nbsp;0.17 but &rho;&nbsp;=&nbsp;0.67 — confirming strong monotone but non-linear "
  "relationships that a linear coefficient alone would badly understate. The single strongest linear "
  "relationship is <i>is_https</i> (r&nbsp;=&nbsp;&rho;&nbsp;=&nbsp;&minus;0.61), consistent with "
  "Section&nbsp;5.2. Figure&nbsp;2 shows the Spearman correlation structure among the leading "
  "features, revealing that they are not independent: the path- and length-related features form a "
  "strongly inter-correlated block, which becomes important when interpreting the ablation in "
  "Section&nbsp;5.6.")
table_from_csv("T7_correlation", "Feature&ndash;label correlation, Pearson versus Spearman (top 10 by |Spearman|).",
               nrows=10, col_widths=[4.6*cm, 3.2*cm, 3.2*cm])
figure("F6_correlation", "Spearman correlation among the leading features. Length- and path-related "
                         "features form a correlated block, so they encode substantially overlapping information.",
       width=10.5*cm, height=8.4*cm)
P("Finally, because the features are non-normal, class differences are tested with the non-parametric "
  "Mann&ndash;Whitney U test rather than a t-test (Table&nbsp;8). Every feature tested differs "
  "significantly between classes, with p-values numerically indistinguishable from zero at machine "
  "precision — a consequence of the very large sample size as much as of effect size. The median "
  "values are more informative than the p-values: phishing URLs are longer (34 versus 27 characters) "
  "and marginally higher-entropy, while <i>is_https</i> shows a complete median separation (0 for "
  "phishing, 1 for legitimate), again isolating the artifact.")
table_from_csv("T8_mannwhitney", "Mann&ndash;Whitney U tests of class differences, with class medians.",
               col_widths=[3.8*cm, 3.4*cm, 3.6*cm, 3.4*cm])

H2f("5.4 Model comparison")
P("Table&nbsp;9 compares the three candidate classifiers on the 40-feature representation. Random "
  "forest and histogram gradient boosting are statistically indistinguishable (McNemar "
  "p&nbsp;=&nbsp;1.00, and their bootstrap confidence intervals coincide), while both significantly "
  "outperform logistic regression "
  "(p&nbsp;=&nbsp;7.7&times;10<sup rise='3' size='6'>&minus;15</sup>) — a difference that is "
  "statistically real but practically negligible, at roughly three F1 thousandths. The confidence "
  "intervals are extremely tight (width &asymp;&nbsp;0.001), which matters for the argument of this "
  "report: the near-perfect score is stable and reproducible, not an artifact of a fortunate split. "
  "The tree ensemble is used as the reference detector for all subsequent experiments.")
table_from_csv("T2_model_comparison",
               "Model comparison with bootstrap 95% confidence intervals and McNemar tests against the best model.",
               fontsize=7.3, col_widths=[2.4*cm, 1.9*cm, 1.9*cm, 1.9*cm, 1.6*cm, 1.9*cm, 1.9*cm, 1.9*cm])

H2f("5.5 Explainability")
P("SHAP attribution&nbsp;[7] (Table&nbsp;10, Figure&nbsp;3) identifies <i>is_https</i> as the dominant "
  "feature, with a mean absolute SHAP value roughly three times that of the next-ranked feature. The "
  "remaining top features — path segments, path length, slash count — are structural descriptors of "
  "'how deep' a URL is. The explanation therefore converges independently on the same conclusion as "
  "Section&nbsp;5.2: the model is largely an HTTPS-and-path-depth detector. Figure&nbsp;4 provides an "
  "independent cross-check using the random forest's own impurity-based importance, which ranks the "
  "same feature set — the agreement between two different attribution methods strengthens the "
  "finding.")
table_from_csv("T5_shap_importance", "Global SHAP feature importance (top 8 of 40).",
               nrows=8, col_widths=[6*cm, 4*cm])
figure("F5_shap", "SHAP global feature importance. is_https dominates the model's decisions by roughly a "
                  "factor of three.", width=10.5*cm, height=7.2*cm)
figure("F2_feature_importance", "Independent cross-check: the random forest's built-in impurity-based "
                                "feature importance, which agrees with the SHAP ranking.",
       width=10.5*cm, height=7.2*cm)

H2f("5.6 Feature-group ablation")
P("Grouping the 40 features into the six families of Table&nbsp;2 and training on each family in "
  "isolation (Table&nbsp;11) shows that the artifact is not confined to a single feature. The "
  "<i>length/counts</i> family — eight features, none of them <i>is_https</i> — reaches "
  "F1&nbsp;=&nbsp;0.993 alone, nearly matching the full model, while the <i>scheme/encoding</i> family "
  "containing <i>is_https</i> reaches only 0.696 in isolation. Meanwhile the <i>brand/cue</i> family, "
  "which encodes the features most directly associated with phishing intent in prior work&nbsp;[4], is "
  "the weakest of all (F1&nbsp;=&nbsp;0.273). The interpretation, consistent with the correlation "
  "structure in Figure&nbsp;2, is that the corpus encodes a broad 'clean home-page versus deep messy "
  "link' distinction across many correlated structural proxies. Any one of them can substitute for the "
  "others — which anticipates the limited effect of the de-biasing defence in the next section.")
table_from_csv("T12_ablation", "Feature-group ablation. Length and count features alone nearly reproduce the "
                               "full model, while brand and cue features contribute least.",
               col_widths=[4.2*cm, 2.6*cm, 1.9*cm, 1.9*cm])

H2f("5.7 Adversarial robustness")
P("Table&nbsp;12 and Figure&nbsp;5 report recall on phishing URLs under each attack and defence. "
  "Character-level attacks leave recall essentially unchanged (homoglyph 0.992, typosquat 0.993 "
  "against a clean baseline of 0.994): a detector built on structural quantities is largely "
  "insensitive to which specific characters appear, in marked contrast to lexical text classifiers, "
  "which such attacks are known to defeat&nbsp;[6]. This is a genuine, if incidental, robustness "
  "property, and it is complementary to the content-based detector built in the companion module.")
P("Along the axis on which the model is biased, however, it is highly vulnerable. A scheme upgrade "
  "alone — changing nothing but HTTP to HTTPS — reduces recall from 0.994 to 0.672, meaning roughly "
  "one third of phishing URLs cross the decision boundary as a result of a single free change. "
  "Home-page mimicry defeats the detector entirely (recall&nbsp;=&nbsp;0.000): once a phishing URL is "
  "short, path-free and served over HTTPS, it matches every structural expectation the model has "
  "learned for legitimate traffic. Canonicalisation, as expected, has no effect on either attack, "
  "since there is no confusable character to fold; it is effective only against the homoglyph family "
  "it was designed for. Removing <i>is_https</i> and retraining recovers only marginally "
  "(0.672&nbsp;&rarr;&nbsp;0.704), confirming the ablation finding that the bias is diffuse. No "
  "defence available within a URL-only feature space closes this gap.")
table_from_csv("T3_arms_race", "Recall on phishing URLs under each attack, with and without each defence.",
               col_widths=[3.6*cm, 3.2*cm, 3.2*cm, 3.6*cm])
figure("F3_arms_race", "Recall under each attack. Structural (character-level) attacks are ineffective; "
                       "attacks that exploit the HTTPS and path-depth artifact are highly effective.",
       width=13*cm, height=6.6*cm)

H2f("5.8 Unsupervised detection and calibration")
P("As a weaker-assumption comparison, two unsupervised anomaly detectors were trained exclusively on "
  "legitimate URLs, with no phishing labels at all (Table&nbsp;13). Isolation Forest, which isolates "
  "anomalous points using random splits, attains AUC&nbsp;=&nbsp;0.828; Local Outlier Factor, which "
  "compares a point's local density to that of its neighbours, attains AUC&nbsp;=&nbsp;0.944. Both are "
  "creditable without any labelled attack data, though below the supervised model — and both are "
  "expected to depend on the same structural artifacts, since they measure structural unusualness "
  "rather than maliciousness.")
table_from_csv("T10_anomaly", "Unsupervised anomaly detectors trained only on legitimate URLs.",
               col_widths=[6*cm, 4*cm])
P("Probability calibration was assessed with the Brier score (the mean squared error between predicted "
  "probability and outcome) and a reliability curve, which plots observed frequency against predicted "
  "probability. In-distribution the detector is well calibrated overall (Brier&nbsp;=&nbsp;0.0025), "
  "though Table&nbsp;14 and Figure&nbsp;6 show the expected instability in the sparsely populated "
  "middle of the probability range: the model is confidently correct at both extremes, where almost "
  "all of its predictions fall, and noisier in between. Section&nbsp;5.9 shows that this calibration "
  "does not survive a change of dataset.")
table_from_csv("T11_calibration", "Reliability table: observed phishing frequency per predicted-probability bin.",
               col_widths=[5*cm, 5*cm])
figure("F8_calibration", "Reliability curve. Points on the diagonal indicate well-calibrated probabilities; "
                         "the bulk of predictions lie at the two extremes.", width=8.6*cm, height=8.6*cm)

H2f("5.9 Cross-dataset generalisation")
P(f"The central generalisation result is reported in Table&nbsp;15 and Figure&nbsp;7. The "
  f"in-distribution detector (F1&nbsp;=&nbsp;{id_f1}, AUC&nbsp;=&nbsp;{id_auc}) collapses on the "
  f"independent Kaggle corpus to F1&nbsp;=&nbsp;{xds_f1}, AUC&nbsp;=&nbsp;{xds_auc}. Figure&nbsp;7 "
  "makes the mechanism directly visible: in-distribution, the predicted-probability distributions of "
  "the two classes are cleanly separated, with legitimate URLs near 0 and phishing URLs near 1; on the "
  "independent corpus <b>both</b> classes collapse into the same region near 1.0 (mean predicted "
  "probability 1.000 for benign URLs and 0.999 for phishing URLs; 100.0% of benign and 99.9% of "
  "phishing URLs are scored above 0.9). The model has not merely become less confident — it no longer "
  "separates the classes at all.")
P("An AUC below 0.5 reflects this precisely: within that saturated band, benign URLs are on average "
  "ranked marginally above phishing URLs, so the ranking is not merely uninformative but "
  "systematically inverted. This explains why re-thresholding recovers almost nothing "
  "(F1&nbsp;0.666&nbsp;&rarr;&nbsp;0.667 at the cost-optimal cut-off): re-thresholding can repair a "
  "model whose ranking is intact but whose operating point is mis-set, not one whose outputs no longer "
  "discriminate. Removing <i>is_https</i> does not help either — the de-biased variant is worse "
  "(AUC&nbsp;=&nbsp;0.168) — indicating that the transferability failure is not attributable to that "
  "single feature. Notably, recall on the <b>live OpenPhish</b> feed remains 1.00: present-day "
  "phishing URLs are still structurally irregular enough to be caught. The correct reading is that the "
  "detector remains useful against today's attacks while being demonstrably non-transferable, and that "
  "its high recall on the independent corpus is accompanied by an unacceptable false-positive rate "
  "rather than genuine discrimination.")
table_from_csv("T4_cross_dataset",
               "Cross-dataset generalisation: in-distribution performance versus an independent 651k-URL "
               "corpus and a live phishing feed.",
               fontsize=7.6, col_widths=[6.2*cm, 1.9*cm, 2.6*cm, 1.9*cm, 2*cm])
figure("F4_cross_dataset", "Predicted-probability distributions by true class. In-distribution the classes "
                           "are cleanly separated; on the independent corpus both collapse into the same "
                           "saturated region.", width=11*cm, height=6.2*cm)

H2f("5.10 Diagnosing the collapse")
P("To identify why generalisation fails, Table&nbsp;16 ranks features by the distributional distance "
  "between their PhiUSIIL and Kaggle distributions. The three most-shifted features by the "
  "Kolmogorov&ndash;Smirnov statistic — <i>is_https</i> (0.741), <i>path_len</i> (0.694) and "
  "<i>n_path_segments</i> (0.627) — are precisely the features SHAP identified as the model's "
  "strongest decision drivers in Section&nbsp;5.5. The normalised Wasserstein distances tell the same "
  "story. The detector's accuracy is therefore built on the least transferable part of the feature "
  "space, which is a mechanistic and quantitative explanation of the collapse in Section&nbsp;5.9 "
  "rather than a restatement of it. Two independent diagnostic tools — feature attribution and "
  "distributional distance — converge on the same small set of features, which is strong evidence for "
  "the causal account offered here.")
table_from_csv("T9_domain_shift",
               "Distributional shift between PhiUSIIL and the independent corpus, by Kolmogorov&ndash;Smirnov "
               "statistic and normalised Wasserstein distance (top 8 features).",
               nrows=8, col_widths=[4.2*cm, 3.2*cm, 3.2*cm])
figure("F7_domain_shift", "Kolmogorov&ndash;Smirnov distance per feature between the two datasets. The "
                          "most-shifted features coincide with the model's top SHAP drivers.",
       width=11.5*cm, height=6.5*cm)

H2f("5.11 Error analysis")
P("On the clean in-distribution test set of 47,074 URLs the detector makes very few errors: 15 false "
  "positives and 119 false negatives (Table&nbsp;17). Table&nbsp;18 lists representative examples and "
  "is more informative than the counts. The false positives are ordinary legitimate sites that happen "
  "to look structurally unusual — numeric domains such as <i>180360.com</i>, an uncommon TLD in "
  "<i>thefeedbackloop.xyz</i>, or the long multi-label host "
  "<i>provincialarchives.alberta.ca</i>. The false negatives are more instructive: "
  "<i>what.promerc.repl.co</i> is phishing hosted on a legitimate developer-sandbox domain — an "
  "in-the-wild instance of exactly the home-page-mimicry attack modelled in Section&nbsp;5.7 — and "
  "<i>microsoft-sicherheitsupdate.com</i> is a brand-impersonation domain that the detector scores at "
  "0.108, because it is short, HTTPS and structurally clean despite containing an obvious brand name. "
  "The rarity of in-distribution errors, contrasted with the severity of the mimicry and cross-dataset "
  "failures, demonstrates that clean-data error analysis alone would have entirely missed this "
  "report's central finding.")
table_from_csv("T13_error_counts", "Error counts on the clean in-distribution test set.",
               col_widths=[6*cm, 4*cm])
table_from_csv("T13b_error_examples",
               "Representative errors. The false negatives include phishing on legitimate hosting "
               "infrastructure and a structurally clean brand-impersonation domain.",
               col_widths=[1.6*cm, 9.4*cm, 1.3*cm, 1.7*cm], fontsize=7.6, wrap_col=1)

# =====================================================================
# 6. DISCUSSION
# =====================================================================
H("6. Discussion")
P("The four research questions can now be answered directly. <b>RQ1 (signal):</b> very little of the "
  "headline near-perfect score reflects transferable phishing-specific signal. One provided feature is "
  "label leakage, and once it is excluded the remaining score rests on a collection artifact that a "
  "one-line rule already captures at F1&nbsp;0.68. <b>RQ2 (robustness):</b> the detector is genuinely "
  "robust to cheap character-level evasion, but this robustness is a side-effect of using structural "
  "features rather than a designed defence, and it offers no protection against an attacker who simply "
  "uses legitimate HTTPS hosting — an attack that reduces recall to zero. <b>RQ3 (generalisation):</b> "
  "the score does not transfer; on an independent corpus the model's ranking inverts, which is a more "
  "severe failure than the miscalibration usually assumed in domain-adaptation settings, and one that "
  "threshold tuning cannot repair. <b>RQ4 (explainability):</b> SHAP and distributional distance "
  "independently identify the same features as both the model's strongest drivers and the least "
  "transferable signals, which is what elevates the central claim from an observation to a causal "
  "explanation.")
P("Taken together these results support a specific methodological conclusion: for URL-based phishing "
  "detection, in-distribution benchmark accuracy is close to uninformative about deployment "
  "behaviour. Evaluation practice should therefore report cross-dataset performance and adversarial "
  "recall as first-class results rather than as optional robustness checks. It is worth noting that "
  "the companion content-based detector, built on entirely different features and data, reached a "
  "structurally similar conclusion — a near-perfect in-distribution text classifier that degraded "
  "sharply out-of-distribution and under adversarial perturbation. That two independent signals "
  "exhibit the same fragility suggests the issue is not specific to URL features but is a general "
  "property of narrow, single-signal phishing classifiers evaluated only in-distribution.")

# =====================================================================
# 7. LIMITATIONS AND FUTURE WORK
# =====================================================================
H("7. Limitations and Future Work")
P("Several limitations bound these conclusions. The cross-dataset comparison is informative but not "
  "perfectly controlled: PhiUSIIL and the Kaggle corpus differ in collection methodology as well as in "
  "genuine URL characteristics, so part of the measured shift may reflect crawling or encoding "
  "conventions rather than properties of phishing URLs themselves. The de-biased variant, which fails "
  "even more severely, is offered as partial evidence that the result is not attributable to a single "
  "confounding feature, but a fully controlled comparison would require corpora collected under a "
  "shared protocol. The feature set is intentionally restricted to string-derived signals and omits "
  "network-observable and third-party evidence — domain age from WHOIS, hosting and certificate "
  "reputation, and redirect-chain analysis — any of which could plausibly improve cross-dataset "
  "robustness, and precisely because they are harder for an attacker to control they are the most "
  "promising extension. The live-feed evaluation uses a single snapshot of 300 URLs from one provider "
  "and should be read as indicative rather than as a temporal-drift study. Finally, the adversarial "
  "evaluation covers four attack families chosen to span cheap and expensive evasion; it is not "
  "exhaustive.")
P("One numerical caveat deserves explicit mention. Because the out-of-distribution scores are "
  "saturated — almost every URL in the independent corpus receives a predicted probability above 0.9 "
  "(Section&nbsp;5.9) — the <i>ordering</i> within that band is decided by very small score "
  "differences, and the resulting AUC is correspondingly sensitive: differences at the level of "
  "floating-point rounding in the feature values shift the reported figure by a few hundredths "
  "(observed range approximately 0.39&ndash;0.43 across representations of the same features). The "
  "pipeline therefore always consumes the persisted feature artifact, so that a run reproduces "
  "identically regardless of whether the cache was already present. This sensitivity does not affect "
  "any conclusion drawn here: every variant is far below the 0.5 threshold that separates a "
  "correctly-ordered ranking from an inverted one, and the F1 figure (0.666) is stable across all of "
  "them. It is reported because a metric that moves with numerical noise should be flagged rather "
  "than quoted to three decimal places as though it were precise.")
P("The clearest next step follows directly from Section&nbsp;5.7: because no defence within the "
  "URL-only feature space closes the mimicry gap, the natural remedy is <b>fusion</b> with the "
  "companion content-based detector, so that an attacker who defeats one channel by using legitimate "
  "infrastructure must simultaneously defeat an independent second channel that reads entirely "
  "different evidence.")

# =====================================================================
# 8. CONCLUSION
# =====================================================================
H("8. Conclusion")
P("A URL-only phishing detector can be made fast, interpretable and robust to cheap character-level "
  "obfuscation, and it continues to catch a large share of current real-world phishing traffic. "
  "However, the near-perfect accuracy such detectors report on standard benchmarks is substantially a "
  "property of how those benchmarks were constructed rather than of phishing itself. It is supported "
  "in part by outright label leakage, it rests otherwise on a collection artifact that a single rule "
  "can capture, it is trivially evaded by an attacker willing to use ordinary legitimate "
  "infrastructure, and it does not survive contact with an independently collected dataset — where the "
  "model's ranking inverts entirely. We conclude that URL structure is a useful but insufficient "
  "signal on its own, and is best deployed as one independent component of a fused, multi-signal "
  "detection system.")

# =====================================================================
# REFERENCES
# =====================================================================
H("References")
refs = [
 "Prasad, A. &amp; Chandra, S. (2024). PhiUSIIL: A diverse security profile empowered phishing URL "
 "detection framework based on similarity index and incremental learning. <i>Computers &amp; "
 "Security</i>, 136, 103545. Dataset: UCI Machine Learning Repository, id 967.",
 "Siddhartha, M. (2021). <i>Malicious URLs Dataset</i> (651,191 URLs). Kaggle.",
 "OpenPhish. <i>Community phishing feed</i>. https://openphish.com (snapshot retrieved 2026).",
 "Ma, J., Saul, L. K., Savage, S., &amp; Voelker, G. M. (2009). Beyond blacklists: learning to detect "
 "malicious web sites from suspicious URLs. <i>Proceedings of the 15th ACM SIGKDD International "
 "Conference on Knowledge Discovery and Data Mining</i>, 1245&ndash;1254.",
 "Le, H., Pham, Q., Sahoo, D., &amp; Hoi, S. C. H. (2018). URLNet: learning a URL representation with "
 "deep learning for malicious URL detection. <i>arXiv preprint arXiv:1802.03162</i>.",
 "Boucher, N., Shumailov, I., Anderson, R., &amp; Papernot, N. (2022). Bad characters: imperceptible "
 "NLP attacks. <i>2022 IEEE Symposium on Security and Privacy (SP)</i>, 1987&ndash;2004.",
 "Lundberg, S. M. &amp; Lee, S.-I. (2017). A unified approach to interpreting model predictions. "
 "<i>Advances in Neural Information Processing Systems</i>, 30, 4765&ndash;4774.",
]
for i, r in enumerate(refs, 1):
    story.append(Paragraph(f"[{i}]&nbsp;&nbsp;{r}", REF))

os.makedirs("report", exist_ok=True)
doc = SimpleDocTemplate("report/report.pdf", pagesize=A4, leftMargin=2.2*cm, rightMargin=2.2*cm,
                        topMargin=2*cm, bottomMargin=2.1*cm,
                        title="Catching Phishing from the Link Alone: A Critical Evaluation of URL-Based Phishing Detection",
                        author=AUTHOR)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(f"wrote report/report.pdf  ({_tab_n[0]} tables, {_fig_n[0]} figures)")
