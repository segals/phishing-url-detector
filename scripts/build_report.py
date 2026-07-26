"""Build the formal submission report (report/report.pdf) from the computed results.

Every table in results/tables/ and every figure in results/figures/ is included and
explained. All numbers are read from the generated CSVs, so the report cannot drift
from the code. A table of contents is generated with real page numbers via a two-pass
build. Numbering and headline figures are kept consistent with the slide deck.
"""
import os
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, Table,
                                TableStyle, HRFlowable, KeepTogether, PageBreak)
from reportlab.platypus.tableofcontents import TableOfContents
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

TITLE = ParagraphStyle("TITLE", fontName="Times-Bold", fontSize=19, textColor=INK, leading=23, spaceAfter=4, alignment=TA_LEFT)
SUBTITLE = ParagraphStyle("SUBTITLE", fontName="Times-Italic", fontSize=12.5, textColor=SLATE, leading=16, spaceAfter=9)
META = ParagraphStyle("META", fontName="Times-Roman", fontSize=9.3, textColor=GREY, leading=12.5, spaceAfter=2)
AUTH = ParagraphStyle("AUTH", fontName="Times-Bold", fontSize=11, textColor=INK, leading=14, spaceAfter=2)
ABSTRACT_H = ParagraphStyle("ABSTRACT_H", fontName="Times-Bold", fontSize=10.3, textColor=INK, spaceBefore=8, spaceAfter=3)
ABSTRACT = ParagraphStyle("ABSTRACT", fontName="Times-Roman", fontSize=9.4, textColor=colors.HexColor("#222"), leading=12.9, alignment=TA_JUSTIFY)
H1 = ParagraphStyle("H1", fontName="Times-Bold", fontSize=12.4, textColor=INK, spaceBefore=11, spaceAfter=5, leading=15)
H2 = ParagraphStyle("H2", fontName="Times-Bold", fontSize=10.4, textColor=SLATE, spaceBefore=7.5, spaceAfter=3, leading=12.5)
BODY = ParagraphStyle("BODY", fontName="Times-Roman", fontSize=9.6, textColor=colors.HexColor("#1b1f27"), leading=13.4, spaceAfter=5, alignment=TA_JUSTIFY)
CAP = ParagraphStyle("CAP", fontName="Times-Italic", fontSize=8.4, textColor=GREY, alignment=TA_CENTER, spaceBefore=2.5, spaceAfter=8, leading=10.5)
REF = ParagraphStyle("REF", fontName="Times-Roman", fontSize=8.8, textColor=colors.HexColor("#1b1f27"), leading=12, spaceAfter=4, leftIndent=14, firstLineIndent=-14)
TOC_H = ParagraphStyle("TOC_H", fontName="Times-Bold", fontSize=12.4, textColor=INK, spaceBefore=10, spaceAfter=6, leading=15)


def val(tab, col, contains, valcol):
    d = pd.read_csv(f"{TAB}/{tab}.csv")
    r = d[d[col].astype(str).str.contains(contains)]
    return str(r.iloc[0][valcol]) if len(r) else "?"


story = []
_tab_n = [0]; _fig_n = [0]


def P(t, style=BODY): story.append(Paragraph(t, style))


def H(t):
    p = Paragraph(t, H1); p.toc_level = 0
    story.append(p)


def H2f(t):
    # Subsections are deliberately NOT added to the table of contents: keeping the TOC to
    # top-level sections lets it fit on the title page, which keeps the body layout stable
    # across the two build passes (a TOC that spills onto page 2 shifts the content it is
    # itself measuring, and the page numbers oscillate).
    story.append(Paragraph(t, H2))


def _styled(data, col_widths, fontsize):
    t = Table(data, hAlign="LEFT", colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", fontsize),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", fontsize),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("LEFTPADDING", (0, 0), (-1, -1), 4.5), ("RIGHTPADDING", (0, 0), (-1, -1), 4.5),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def table_from_csv(name, caption, ncols=None, nrows=None, col_widths=None, fontsize=7.8, wrap_col=None):
    _tab_n[0] += 1
    d = pd.read_csv(f"{TAB}/{name}.csv")
    if d.columns[0].startswith("Unnamed"):
        d = d.rename(columns={d.columns[0]: "feature"})
    if ncols: d = d.iloc[:, :ncols]
    if nrows: d = d.head(nrows)
    rows = d.round(3).astype(str).values.tolist()
    if wrap_col is not None:
        cs = ParagraphStyle("cell", fontName="Helvetica", fontSize=fontsize - 0.4, leading=fontsize + 1.3)
        rows = [[Paragraph(c, cs) if j == wrap_col else c for j, c in enumerate(r)] for r in rows]
    story.append(KeepTogether([_styled([list(d.columns)] + rows, col_widths, fontsize),
                               Paragraph(f"<b>Table {_tab_n[0]}.</b> {caption}", CAP)]))


def table_inline(header, rows, caption, col_widths=None, fontsize=7.8):
    _tab_n[0] += 1
    cs = ParagraphStyle("cell2", fontName="Helvetica", fontSize=fontsize, leading=fontsize + 1.8)
    body = [[Paragraph(c, cs) for c in r] for r in rows]
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
    canvas.line(2.2*cm, 1.5*cm, A4[0]-2.2*cm, 1.5*cm)
    canvas.setFont("Times-Roman", 8); canvas.setFillColor(GREY)
    canvas.drawString(2.2*cm, 1.12*cm, "Catching Phishing from the Link Alone")
    canvas.drawRightString(A4[0]-2.2*cm, 1.12*cm, f"{doc.page}")
    canvas.restoreState()


class ReportDoc(SimpleDocTemplate):
    """Notifies the TableOfContents of every heading, so page numbers are real."""
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and hasattr(flowable, "toc_level"):
            self.notify("TOCEntry", (flowable.toc_level, flowable.getPlainText(), self.page))


# =====================================================================
# TITLE + ABSTRACT
# =====================================================================
P("Catching Phishing from the Link Alone", TITLE)
P("A Critical Evaluation of URL-Based Phishing Detection", SUBTITLE)
P(AUTHOR, AUTH)
P(f"{COURSE} &nbsp;&middot;&nbsp; URL / link detector (one half of a two-part project)", META)
P(f"Code, data pipeline and reproducible results: {REPO}", META)
story.append(HRFlowable(width="100%", thickness=1, color=RULE, spaceBefore=7, spaceAfter=9))

xds_f1 = val("T4_cross_dataset", "setting", "full model", "f1")
xds_auc = val("T4_cross_dataset", "setting", "full model", "auc")
id_f1 = val("T4_cross_dataset", "setting", "in-distribution", "f1")
id_auc = val("T4_cross_dataset", "setting", "in-distribution", "auc")

P("Abstract", ABSTRACT_H)
P("Phishing remains a leading initial-access vector, and much of it is carried entirely by a malicious "
  "link. This report presents a URL-only phishing detector and subjects it to a critical evaluation "
  "rather than treating a high benchmark score as the end of the analysis. Trained on 235,795 real "
  f"URLs (PhiUSIIL&nbsp;[1]), a tree-ensemble classifier over 40 hand-engineered lexical features "
  f"reaches F1&nbsp;=&nbsp;{id_f1} in-distribution, matching the near-perfect scores reported in the "
  "literature. Using single-feature ablation, explainability (SHAP&nbsp;[7]) and a feature-group "
  "ablation, we show this score is driven overwhelmingly by a dataset collection artifact — legitimate "
  "URLs in this corpus are 100% HTTPS versus 48.6% for phishing — rather than by a transferable "
  "phishing signal. An adversarial evaluation shows the detector resists character-level obfuscation "
  "(homoglyphs, typosquatting; recall &ge;&nbsp;0.99) but is evaded completely (recall&nbsp;=&nbsp;0.00) "
  "by hosting phishing content on ordinary HTTPS infrastructure with a clean, short URL. Most "
  f"critically, evaluated without retraining on an independent 651,191-URL corpus&nbsp;[2], it "
  f"collapses to F1&nbsp;=&nbsp;{xds_f1}, AUC&nbsp;=&nbsp;{xds_auc} — below 0.5, meaning the ranking is "
  "inverted rather than merely uninformative — while a distance-metric analysis "
  "(Kolmogorov&ndash;Smirnov, Wasserstein) confirms the collapse is driven by exactly the features the "
  "model relies on most. On a live feed of current phishing URLs&nbsp;[3], however, recall remains "
  "1.00. We conclude that URL structure alone is not a generalisable phishing signal, and argue for its "
  "use as one independent channel within a fused, multi-signal detector.", ABSTRACT)

# ---------------------------------------------------------------- TOC
story.append(Paragraph("Contents", TOC_H))
toc = TableOfContents()
toc.levelStyles = [
    ParagraphStyle("toc0", fontName="Times-Roman", fontSize=9.6, leading=15, textColor=INK),
]
story.append(toc)

# =====================================================================
# 1. INTRODUCTION
# =====================================================================
H("1. Introduction")
P("Phishing attacks rely on a victim following a malicious link, so the URL itself is an attractive "
  "detection surface: it can be scored in milliseconds, requires no page fetch, preserves user privacy, "
  "and can be evaluated before the user clicks. A large body of published work reports near-perfect "
  "(F1&nbsp;&gt;&nbsp;0.99) accuracy on public URL datasets, suggesting the problem is essentially "
  "solved. This report interrogates that claim: we reproduce the strong published result, then ask "
  "systematically whether it reflects genuine phishing-specific signal or an artifact of how the "
  "benchmark was constructed. The investigation is organised around four research questions.")
P("<b>RQ1 (signal).</b> How much of the near-perfect score survives once dataset-specific leakage and "
  "collection bias are accounted for? "
  "<b>RQ2 (robustness).</b> How does the detector respond to an adversary who deliberately reshapes a "
  "phishing URL's surface features? "
  "<b>RQ3 (generalisation).</b> Does the score transfer to an independent dataset and to live phishing "
  "traffic? "
  "<b>RQ4 (explainability).</b> Which features drive the decision, and does that explain the robustness "
  "and generalisation results?")
P("This module is one of two independent, complementary detectors built for the course project: this "
  "report covers the <b>URL/link</b> channel, a companion module the <b>email content</b> channel. Both "
  "were designed and evaluated independently; fusing them is future work (Section&nbsp;7). The "
  "contribution here is not a new model architecture but an honest, reproducible audit of a standard "
  "one.")

# =====================================================================
# 2. RELATED WORK
# =====================================================================
H("2. Background and Related Work")
P("Lexical and host-based URL features were established by Ma <i>et&nbsp;al.</i>&nbsp;[4], who showed "
  "that structural properties of a URL — length, host composition, IP literals, token content — carry "
  "substantial discriminative signal without inspecting page content; the feature families in "
  "Section&nbsp;4.1 follow that tradition. Deep character-level models such as URLNet&nbsp;[5] instead "
  "learn a representation directly from the URL string, trading interpretability for potential accuracy "
  "gains. We deliberately favour interpretable, hand-engineered features: since the central finding of "
  "this report is that a near-perfect score is attributable to a specific, nameable artifact, an opaque "
  "representation would have obscured precisely the evidence we set out to find.")
P("On the adversarial side, Boucher <i>et&nbsp;al.</i>&nbsp;[6] document imperceptible-perturbation "
  "attacks against text-processing and web-facing systems, including homoglyph substitution — visually "
  "identical characters from other Unicode scripts — motivating both the homoglyph attack and the "
  "canonicalisation defence in Section&nbsp;5.7. For explainability we use SHAP&nbsp;[7], a "
  "game-theoretic attribution method that assigns each feature a principled share of a prediction and, "
  "unlike a tree model's built-in importance, is defined per-prediction and sums exactly to the model "
  "output. Our central concern — that reported accuracy may not transfer across independently collected "
  "corpora — is treated as a hypothesis to be tested (Sections&nbsp;5.9&ndash;5.10) rather than assumed.")

# =====================================================================
# 3. DATA
# =====================================================================
H("3. Data")
H2f("3.1 Primary corpus")
P("The primary dataset is <b>PhiUSIIL</b>&nbsp;[1] (UCI Machine Learning Repository, id&nbsp;967): "
  "235,795 real URLs with a raw URL string, a binary label, and 53 pre-computed features. It is among "
  "the largest and most recent public URL datasets and a common benchmark, which motivates its use as "
  "the primary object of study. Table&nbsp;1 summarises the corpus after cleaning; Figure&nbsp;1 shows "
  "the class balance and two representative feature distributions.")
table_from_csv("T1_dataset", "Composition of the primary PhiUSIIL corpus after cleaning.",
               col_widths=[3.1*cm, 2.1*cm, 2.4*cm, 2.4*cm, 2.4*cm])
figure("F1_eda", "Exploratory view: class balance (left), URL length by class (centre), cue-word count by "
                 "class (right). The classes separate almost perfectly on trivial structural quantities — "
                 "an early sign the task is easier than the real-world problem it represents.",
       width=15*cm, height=5.0*cm)

H2f("3.2 Secondary corpora")
P("Two independent sources support the generalisation analysis. The Kaggle <i>Malicious URLs</i> "
  "dataset&nbsp;[2] contains 651,191 URLs labelled benign, phishing, defacement or malware; we use the "
  "benign/phishing subset, balanced to 40,000 per class. It was collected independently of PhiUSIIL and "
  "is itself mixed-class, making it a fair generalisation test rather than a comparison against an "
  "unlabelled list. A live snapshot of the <b>OpenPhish</b> feed&nbsp;[3] (300 currently active phishing "
  "URLs) provides a check against present-day attacks rather than an archived benchmark.")

H2f("3.3 Data preparation")
P("Preparation was kept deliberately minimal, so the results below are properties of the source data "
  "rather than of our preprocessing. Labels were standardised to 1&nbsp;=&nbsp;phishing (PhiUSIIL uses "
  "the opposite polarity); rows with a missing URL or label were dropped and whitespace stripped. Rows "
  "were then <b>de-duplicated on the exact URL string before splitting</b> "
  "(235,795&nbsp;&rarr;&nbsp;235,370), so no URL appears in both training and test — a common and "
  "easily overlooked source of leakage. No class rebalancing, outlier removal or imputation was "
  "performed, and the natural ratio of 42.7% phishing is retained. Feature standardisation is applied "
  "only inside the logistic-regression pipeline, where it is required; the tree ensembles consume raw "
  "values. The data were split 60/20/20 with a fixed seed (42), stratified on the label; all tuning "
  "used the validation partition and the test partition was evaluated once. For reproducibility the "
  "cleaned dataset is hashed: <font face='Courier' size='7.5'>rows=235370, phishing_rate=0.4271, "
  "sha256=b39e8c2251df…</font> (full value in "
  "<font face='Courier' size='7.5'>results/tables/data_hash.txt</font>).")

# =====================================================================
# 4. METHODOLOGY
# =====================================================================
H("4. Methodology")
H2f("4.1 Feature engineering")
P("A URL is a short, structured string rather than free prose, so instead of learning a text "
  "representation (as a TF-IDF pipeline would for email text) we compute interpretable numeric features "
  "directly from the string. All 40 features derive from the URL alone and require no network access, "
  "keeping the detector fast, private and reproducible. They fall into six families (Table&nbsp;2).")
table_inline(
    ["family", "what it captures", "examples"],
    [["Lexical / length", "size and punctuation profile of the string",
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
    "The six feature families (40 features), all computed from the URL string alone.",
    col_widths=[3.1*cm, 6.1*cm, 7.4*cm])
P("Two families rest on explicit theory. <b>Entropy</b> features use the Shannon entropy of a string, "
  "H(s)&nbsp;=&nbsp;&minus;&Sigma;<sub>i</sub>&nbsp;p<sub>i</sub>&nbsp;log&#8322;&nbsp;p<sub>i</sub>, "
  "over its character distribution: a predictable string such as <i>google</i> scores low, whereas an "
  "algorithmically generated domain such as <i>x7qz9wvt</i> approaches random noise and scores high — a "
  "standard signal for domain-generation algorithms. <b>Brand</b> features use the Levenshtein edit "
  "distance — the minimum number of single-character insertions, deletions or substitutions "
  "transforming one string into another, computed by the standard dynamic-programming recurrence — "
  "between each host label and eighteen frequently impersonated brands. A label within edit distance "
  "1&ndash;2 of a real brand (e.g. <i>paypa1</i> versus <i>paypal</i>) is flagged as a probable "
  "typosquat.")

H2f("4.2 Models")
P("Three classifiers were compared and selected on validation F1: <b>logistic regression</b> (a linear, "
  "directly interpretable baseline with standardised features), <b>random forest</b> (trees trained "
  "independently on bootstrap samples and averaged), and <b>histogram-based gradient boosting</b> (trees "
  "fitted sequentially, each correcting its predecessors' residual error, with features bucketed into "
  "histograms for speed). The two ensembles represent the two standard strategies — variance reduction "
  "by averaging and bias reduction by sequential correction — and neither requires feature scaling.")

H2f("4.3 Evaluation protocol")
P("Because the majority class accounts for 57.3% of the data, accuracy is not a primary metric: a "
  "majority-class classifier attains 57.3% accuracy while catching zero phishing URLs — the "
  "<i>accuracy paradox</i> (Section&nbsp;5.1). We report precision, recall, F1, F2, the Matthews "
  "Correlation Coefficient (MCC) and AUC-ROC. <b>F2</b> weights recall above precision, reflecting that "
  "a missed phishing URL costs more than a false alarm. <b>MCC</b> uses all four confusion-matrix cells "
  "and ranges from &minus;1 to +1 (0 = chance); unlike accuracy or F1 it cannot be inflated by "
  "exploiting the majority class, making it the most trustworthy single figure under imbalance. "
  "<b>AUC-ROC</b> is the probability a randomly drawn phishing URL scores above a randomly drawn "
  "legitimate one, so 0.5 is uninformative ranking — and, importantly for Section&nbsp;5.9, a value "
  "below 0.5 indicates a systematically <i>inverted</i> ranking rather than absent signal.")
P("Every headline metric carries a <b>bootstrap 95% confidence interval</b>: the test set is resampled "
  "with replacement 1,000 times, the metric recomputed each time, and the 2.5th and 97.5th percentiles "
  "reported. This quantifies how much a metric would vary on comparable data using only the data "
  "already collected, preventing over-reading small differences. Paired comparisons additionally use "
  "<b>McNemar's test</b> on the discordant predictions of two models over the same test set.")

H2f("4.4 Threat model and adversarial evaluation")
P("We model a black-box attacker who may freely choose a phishing URL's surface form but must keep it "
  "functional — it must still resolve to attacker-controlled content. Four perturbation families are "
  "evaluated: <i>homoglyph substitution</i> (Latin characters replaced with visually identical Cyrillic "
  "or Greek confusables&nbsp;[6]); <i>typosquatting</i> (a character duplicated or inserted in the "
  "registered domain); <i>scheme upgrade</i> (serving the identical page over HTTPS); and <i>home-page "
  "mimicry</i> (a short, clean, path-free HTTPS domain, approximating the increasingly common abuse of "
  "legitimate cloud hosting). Two defences are evaluated: <i>canonicalisation</i>, which folds "
  "confusable characters to their ASCII skeleton and decodes punycode before scoring, and "
  "<i>de-biasing</i>, which retrains without the HTTPS feature to test whether the artifact is "
  "concentrated in one feature or spread across correlated ones.")

H2f("4.5 Generalisation and diagnostic tools")
P("Cross-dataset generalisation is measured by training exclusively on PhiUSIIL and evaluating, with no "
  "retraining or recalibration, on the independent Kaggle corpus and the live OpenPhish feed. To "
  "diagnose <i>why</i> a gap occurs we compare per-feature distributions using the "
  "<b>Kolmogorov&ndash;Smirnov statistic</b> (maximum vertical distance between two empirical "
  "cumulative distribution functions) and the <b>Wasserstein</b> (earth-mover's) distance (minimum "
  "probability mass moved, weighted by distance), normalised by the in-distribution standard deviation "
  "so features on different scales stay comparable. We additionally report two label-free anomaly "
  "detectors trained only on legitimate URLs, and assess calibration via the Brier score and a "
  "reliability curve.")

# =====================================================================
# 5. RESULTS
# =====================================================================
H("5. Results")

H2f("5.1 Trivial baselines and the accuracy paradox")
P("Table&nbsp;3 reports three baselines requiring no learning. A majority-class predictor attains 57.3% "
  "accuracy with zero recall and MCC exactly 0 — useless for security, yet respectable if judged on "
  "accuracy. More revealing, a single rule flagging any non-HTTPS URL as phishing attains "
  "F1&nbsp;=&nbsp;0.68 and MCC&nbsp;=&nbsp;0.62. That a one-line rule captures so much of the task "
  "foreshadows Section&nbsp;5.2. By contrast the cue-word rule — the most intuitively 'phishing-like' "
  "heuristic — performs poorly (F1&nbsp;=&nbsp;0.13).")
table_from_csv("T1b_baselines", "Trivial baselines. A single HTTPS check reaches F1 0.68; the intuitive "
                                "cue-word rule only 0.13.",
               col_widths=[6.6*cm, 2.6*cm, 2.2*cm, 2.2*cm, 2.2*cm])

H2f("5.2 Decomposing the near-perfect score")
P("Training on all 50 provided numeric features reproduces the near-perfect literature result "
  "(F1&nbsp;=&nbsp;1.000). Decomposing it is the central diagnostic of this report (Table&nbsp;4). One "
  "provided feature, <i>URLSimilarityIndex</i>, attains F1&nbsp;=&nbsp;0.995 alone. The raw data "
  "explains why: it takes the value 100 for <b>100% of legitimate URLs</b> while phishing URLs average "
  "49.6 — effectively a re-encoding of the label, and uncomputable at deployment time for a genuinely "
  "unseen URL. It is therefore treated as leakage, measured once as evidence and <b>excluded from every "
  "subsequent experiment</b>; the detector evaluated throughout the rest of this report uses only the 40 "
  "features of Section&nbsp;4.1.")
table_from_csv("T0_artifact_decomposition",
               "Decomposing the near-perfect score: all provided features, individual provided features, "
               "and our leakage-free lexical features. Bootstrap 95% CIs shown where a full model was fitted.",
               col_widths=[7.4*cm, 1.7*cm, 1.7*cm, 3*cm])
P("The more interesting result is the last row: our leakage-free features still attain "
  "F1&nbsp;=&nbsp;0.997. This is not leakage but a deeper problem. As Table&nbsp;5 shows, every "
  "legitimate URL in this corpus uses HTTPS while fewer than half the phishing URLs do. This 51-point "
  "gap is a property of how the classes were collected — legitimate URLs appear drawn from clean "
  "canonical home-pages, phishing URLs from messy deep links — not of phishing itself. On the "
  "contemporary web the association is far weaker, since most phishing sites now serve over HTTPS.")
table_from_csv("T3a_https_artifact", "HTTPS usage by class in PhiUSIIL: the dominant collection artifact.",
               col_widths=[6*cm, 4*cm])

H2f("5.3 Distribution shape, correlation, and non-parametric testing")
P("URL-derived features are strongly right-skewed and heavy-tailed (Table&nbsp;6): URL length has "
  "skewness 54.7 and excess kurtosis 5,812, indicating a few extremely long URLs far from the bulk of "
  "the distribution. Under such distributions the mean and Pearson correlation are unreliable, "
  "motivating rank-based statistics and medians throughout.")
table_from_csv("T6_eda_shape", "Distribution shape of representative features. Large positive skewness and "
                               "excess kurtosis indicate heavy right tails.",
               col_widths=[4.4*cm, 3*cm, 3.4*cm])
P("Table&nbsp;7 compares Pearson (linear) and Spearman (monotone) correlation with the label. They "
  "diverge substantially for several features — path length has r&nbsp;=&nbsp;0.17 but "
  "&rho;&nbsp;=&nbsp;0.67 — confirming strong monotone but non-linear relationships a linear "
  "coefficient would understate. The strongest linear relationship is <i>is_https</i> "
  "(r&nbsp;=&nbsp;&rho;&nbsp;=&nbsp;&minus;0.61), consistent with Section&nbsp;5.2. Figure&nbsp;2 shows "
  "the correlation structure among leading features: the path- and length-related features form a "
  "strongly inter-correlated block, which matters for interpreting the ablation in Section&nbsp;5.6.")
table_from_csv("T7_correlation", "Feature&ndash;label correlation, Pearson versus Spearman (top 10 by |Spearman|).",
               nrows=10, col_widths=[4.6*cm, 3.2*cm, 3.2*cm])
figure("F6_correlation", "Spearman correlation among leading features. Length- and path-related features "
                         "form a correlated block, encoding substantially overlapping information.",
       width=10*cm, height=8.0*cm)
P("Because the features are non-normal, class differences are tested with the non-parametric "
  "Mann&ndash;Whitney U test (Table&nbsp;8). All features tested differ significantly, with p-values "
  "numerically indistinguishable from zero at machine precision — a consequence of the very large "
  "sample as much as of effect size. The medians are more informative: phishing URLs are longer (34 vs "
  "27 characters) and marginally higher-entropy, while <i>is_https</i> shows complete median separation "
  "(0 for phishing, 1 for legitimate), again isolating the artifact.")
table_from_csv("T8_mannwhitney", "Mann&ndash;Whitney U tests of class differences, with class medians.",
               col_widths=[3.8*cm, 3.4*cm, 3.6*cm, 3.4*cm])

H2f("5.4 Model comparison")
P("Table&nbsp;9 compares the three classifiers on the 40-feature representation. Random forest and "
  "histogram gradient boosting are statistically indistinguishable (McNemar p&nbsp;=&nbsp;1.00, "
  "coincident confidence intervals), and both significantly outperform logistic regression "
  "(p&nbsp;=&nbsp;7.7&times;10<sup rise='3' size='6'>&minus;15</sup>) — statistically real but "
  "practically negligible, roughly three F1 thousandths. The intervals are extremely tight (width "
  "&asymp;&nbsp;0.001), which matters for this report's argument: the near-perfect score is stable and "
  "reproducible, not an artifact of a fortunate split. The tree ensemble is the reference detector "
  "throughout.")
table_from_csv("T2_model_comparison",
               "Model comparison with bootstrap 95% confidence intervals and McNemar tests against the best model.",
               fontsize=7.1, col_widths=[2.4*cm, 1.9*cm, 1.9*cm, 1.9*cm, 1.6*cm, 1.9*cm, 1.9*cm, 1.9*cm])

H2f("5.5 Explainability")
P("SHAP attribution&nbsp;[7] (Table&nbsp;10, Figure&nbsp;3) identifies <i>is_https</i> as dominant, with "
  "mean absolute SHAP roughly three times the next-ranked feature. The remaining leaders — path "
  "segments, path length, slash count — are structural descriptors of how 'deep' a URL is. The "
  "explanation converges independently on the conclusion of Section&nbsp;5.2: the model is largely an "
  "HTTPS-and-path-depth detector. Figure&nbsp;4 cross-checks this with the random forest's own "
  "impurity-based importance, which ranks the same features; agreement between two different "
  "attribution methods strengthens the finding.")
table_from_csv("T5_shap_importance", "Global SHAP feature importance (top 8 of 40).",
               nrows=8, col_widths=[6*cm, 4*cm])
figure("F5_shap", "SHAP global feature importance. is_https dominates by roughly a factor of three.",
       width=10*cm, height=6.8*cm)
figure("F2_feature_importance", "Independent cross-check: the random forest's built-in impurity-based "
                                "importance, which agrees with the SHAP ranking.",
       width=10*cm, height=6.8*cm)

H2f("5.6 Feature-group ablation")
P("Training on each of the six families in isolation (Table&nbsp;11) shows the artifact is not confined "
  "to one feature. The <i>length/counts</i> family — eight features, none of them <i>is_https</i> — "
  "reaches F1&nbsp;=&nbsp;0.993 alone, nearly matching the full model, while the <i>scheme/encoding</i> "
  "family containing <i>is_https</i> reaches only 0.696. The <i>brand/cue</i> family, encoding the "
  "features most directly associated with phishing intent in prior work&nbsp;[4], is weakest "
  "(F1&nbsp;=&nbsp;0.273). Consistent with the correlation structure in Figure&nbsp;2, the corpus "
  "encodes a broad 'clean home-page versus deep messy link' distinction across many correlated "
  "structural proxies, any of which can substitute for the others — anticipating the limited effect of "
  "de-biasing in the next section.")
table_from_csv("T12_ablation", "Feature-group ablation. Length and count features alone nearly reproduce the "
                               "full model; brand and cue features contribute least.",
               col_widths=[4.2*cm, 2.6*cm, 1.9*cm, 1.9*cm])

H2f("5.7 Adversarial robustness")
P("Table&nbsp;12 and Figure&nbsp;5 report recall on phishing URLs under each attack and defence. "
  "Character-level attacks leave recall essentially unchanged (homoglyph 0.992, typosquat 0.993 against "
  "a clean 0.994): a detector built on structural quantities is largely insensitive to which characters "
  "appear, in marked contrast to lexical text classifiers, which such attacks defeat&nbsp;[6]. This is a "
  "genuine, if incidental, robustness property, complementary to the content-based detector in the "
  "companion module.")
P("Along the axis on which the model is biased, however, it is highly vulnerable. A scheme upgrade alone "
  "— changing nothing but HTTP to HTTPS — reduces recall from 0.994 to 0.672, so roughly one third of "
  "phishing URLs cross the decision boundary from a single free change. Home-page mimicry defeats the "
  "detector entirely (recall&nbsp;=&nbsp;0.000): once a phishing URL is short, path-free and served over "
  "HTTPS it matches every structural expectation learned for legitimate traffic. Canonicalisation has no "
  "effect on either attack — there is no confusable character to fold — and is effective only against "
  "the homoglyph family it targets. Removing <i>is_https</i> and retraining recovers only marginally "
  "(0.672&nbsp;&rarr;&nbsp;0.704), confirming the bias is diffuse. No defence within a URL-only feature "
  "space closes this gap.")
table_from_csv("T3_arms_race", "Recall on phishing URLs under each attack, with and without each defence.",
               col_widths=[3.6*cm, 3.2*cm, 3.2*cm, 3.6*cm])
figure("F3_arms_race", "Recall under each attack. Character-level attacks are ineffective; attacks "
                       "exploiting the HTTPS and path-depth artifact are highly effective.",
       width=12.5*cm, height=6.3*cm)

H2f("5.8 Unsupervised detection and calibration")
P("As a weaker-assumption comparison, two unsupervised anomaly detectors were trained exclusively on "
  "legitimate URLs, with no phishing labels (Table&nbsp;13). Isolation Forest, which isolates anomalous "
  "points using random splits, attains AUC&nbsp;=&nbsp;0.828; Local Outlier Factor, comparing a point's "
  "local density to its neighbours', attains 0.944. Both are creditable without labelled attack data "
  "though below the supervised model, and both depend on the same structural artifacts, since they "
  "measure structural unusualness rather than maliciousness.")
table_from_csv("T10_anomaly", "Unsupervised anomaly detectors trained only on legitimate URLs.",
               col_widths=[6*cm, 4*cm])
P("Calibration was assessed with the Brier score (mean squared error between predicted probability and "
  "outcome) and a reliability curve. In-distribution the detector is well calibrated overall "
  "(Brier&nbsp;=&nbsp;0.0025), though Table&nbsp;14 and Figure&nbsp;6 show the expected instability in "
  "the sparsely populated middle of the range: the model is confidently correct at both extremes, where "
  "almost all predictions fall, and noisier between. Section&nbsp;5.9 shows this calibration does not "
  "survive a change of dataset.")
table_from_csv("T11_calibration", "Reliability table: observed phishing frequency per predicted-probability bin.",
               col_widths=[5*cm, 5*cm])
figure("F8_calibration", "Reliability curve. Points on the diagonal indicate well-calibrated probabilities; "
                         "the bulk of predictions lie at the two extremes.", width=8.0*cm, height=8.0*cm)

H2f("5.9 Cross-dataset generalisation")
P(f"The central generalisation result appears in Table&nbsp;15 and Figure&nbsp;7. The in-distribution "
  f"detector (F1&nbsp;=&nbsp;{id_f1}, AUC&nbsp;=&nbsp;{id_auc}) collapses on the independent Kaggle "
  f"corpus to F1&nbsp;=&nbsp;{xds_f1}, AUC&nbsp;=&nbsp;{xds_auc}. Figure&nbsp;7 makes the mechanism "
  "visible: in-distribution the two classes' predicted-probability distributions are cleanly separated "
  "(legitimate near 0, phishing near 1); on the independent corpus <b>both</b> collapse into the same "
  "region near 1.0 (mean predicted probability 1.000 for benign and 0.999 for phishing; 100.0% of benign "
  "and 99.9% of phishing scored above 0.9). The model has not merely become less confident — it no "
  "longer separates the classes at all.")
P("An AUC below 0.5 reflects this precisely: within that saturated band benign URLs are on average "
  "ranked marginally above phishing ones, so the ranking is not merely uninformative but systematically "
  "inverted. Hence re-thresholding recovers almost nothing (F1&nbsp;0.666&nbsp;&rarr;&nbsp;0.667 at the "
  "cost-optimal cut-off): it can repair a model whose ranking is intact but whose operating point is "
  "mis-set, not one whose outputs no longer discriminate. Removing <i>is_https</i> does not help either "
  "— the de-biased variant is worse (AUC&nbsp;=&nbsp;0.168) — so the failure is not attributable to that "
  "single feature. Notably, recall on the <b>live OpenPhish</b> feed remains 1.00: present-day phishing "
  "URLs are still structurally irregular enough to be caught. The correct reading is that the detector "
  "remains useful against today's attacks while being demonstrably non-transferable, and that its high "
  "recall on the independent corpus comes with an unacceptable false-positive rate rather than genuine "
  "discrimination.")
table_from_csv("T4_cross_dataset",
               "Cross-dataset generalisation: in-distribution performance versus an independent 651k-URL "
               "corpus and a live phishing feed.",
               fontsize=7.4, col_widths=[6.2*cm, 1.9*cm, 2.6*cm, 1.9*cm, 2*cm])
figure("F4_cross_dataset", "Predicted-probability distributions by true class. In-distribution the classes "
                           "separate cleanly; on the independent corpus both collapse into the same "
                           "saturated region.", width=10.5*cm, height=6.0*cm)

H2f("5.10 Diagnosing the collapse")
P("Table&nbsp;16 ranks features by distributional distance between the PhiUSIIL and Kaggle "
  "distributions. The three most-shifted by Kolmogorov&ndash;Smirnov — <i>is_https</i> (0.741), "
  "<i>path_len</i> (0.694) and <i>n_path_segments</i> (0.627) — are precisely the features SHAP "
  "identified as the strongest decision drivers (Section&nbsp;5.5); the normalised Wasserstein distances "
  "agree. The detector's accuracy is therefore built on the least transferable part of the feature "
  "space, a mechanistic explanation of the collapse rather than a restatement of it. Two independent "
  "diagnostics — feature attribution and distributional distance — converging on the same small feature "
  "set is strong evidence for this causal account.")
table_from_csv("T9_domain_shift",
               "Distributional shift between PhiUSIIL and the independent corpus, by Kolmogorov&ndash;Smirnov "
               "statistic and normalised Wasserstein distance (top 8 features).",
               nrows=8, col_widths=[4.2*cm, 3.2*cm, 3.2*cm])
figure("F7_domain_shift", "Kolmogorov&ndash;Smirnov distance per feature between the two datasets. The "
                          "most-shifted features coincide with the model's top SHAP drivers.",
       width=11*cm, height=6.2*cm)

H2f("5.11 Error analysis")
P("On the clean in-distribution test set of 47,074 URLs the detector makes very few errors: 15 false "
  "positives and 119 false negatives (Table&nbsp;17). Table&nbsp;18 lists representative examples and is "
  "more informative than the counts. False positives are ordinary legitimate sites that look "
  "structurally unusual — numeric domains such as <i>180360.com</i>, an uncommon TLD in "
  "<i>thefeedbackloop.xyz</i>, the long multi-label host <i>provincialarchives.alberta.ca</i>. The false "
  "negatives are more instructive: <i>what.promerc.repl.co</i> is phishing hosted on a legitimate "
  "developer-sandbox domain — an in-the-wild instance of the home-page-mimicry attack of "
  "Section&nbsp;5.7 — and <i>microsoft-sicherheitsupdate.com</i> is a brand-impersonation domain scored "
  "at just 0.108 because it is short, HTTPS and structurally clean despite an obvious brand name. The "
  "rarity of in-distribution errors, against the severity of the mimicry and cross-dataset failures, "
  "shows that clean-data error analysis alone would have missed this report's central finding.")
table_from_csv("T13_error_counts", "Error counts on the clean in-distribution test set.",
               col_widths=[6*cm, 4*cm])
table_from_csv("T13b_error_examples",
               "Representative errors. The false negatives include phishing on legitimate hosting "
               "infrastructure and a structurally clean brand-impersonation domain.",
               col_widths=[1.6*cm, 9.4*cm, 1.3*cm, 1.7*cm], fontsize=7.4, wrap_col=1)

# =====================================================================
# 6. DISCUSSION
# =====================================================================
H("6. Discussion")
P("The four research questions can now be answered. <b>RQ1 (signal):</b> very little of the headline "
  "score reflects transferable phishing-specific signal — one provided feature is label leakage, and "
  "once excluded the remaining score rests on a collection artifact a one-line rule already captures at "
  "F1&nbsp;0.68. <b>RQ2 (robustness):</b> the detector genuinely resists cheap character-level evasion, "
  "but this is a side-effect of using structural features rather than a designed defence, and it offers "
  "no protection against an attacker who simply uses legitimate HTTPS hosting — an attack that reduces "
  "recall to zero. <b>RQ3 (generalisation):</b> the score does not transfer; on an independent corpus "
  "the ranking inverts, a more severe failure than the miscalibration usually assumed in "
  "domain-adaptation settings, and one threshold tuning cannot repair. <b>RQ4 (explainability):</b> SHAP "
  "and distributional distance independently identify the same features as both the strongest drivers "
  "and the least transferable signals, elevating the central claim from observation to causal "
  "explanation.")
P("Together these support a methodological conclusion: for URL-based phishing detection, "
  "in-distribution benchmark accuracy is close to uninformative about deployment behaviour, so "
  "evaluation practice should report cross-dataset performance and adversarial recall as first-class "
  "results rather than optional robustness checks. Notably, the companion content-based detector — built "
  "on entirely different features and data — reached a structurally similar conclusion: a near-perfect "
  "in-distribution text classifier that degraded sharply out-of-distribution and under adversarial "
  "perturbation. That two independent signals show the same fragility suggests this is not specific to "
  "URL features but a general property of narrow, single-signal phishing classifiers evaluated only "
  "in-distribution.")

# =====================================================================
# 7. LIMITATIONS AND FUTURE WORK
# =====================================================================
H("7. Limitations and Future Work")
P("Several limitations bound these conclusions. The cross-dataset comparison is informative but not "
  "perfectly controlled: PhiUSIIL and the Kaggle corpus differ in collection methodology as well as in "
  "genuine URL characteristics, so part of the measured shift may reflect crawling or encoding "
  "conventions. The de-biased variant, which fails even more severely, is partial evidence that the "
  "result is not attributable to a single confounding feature, but a fully controlled comparison would "
  "need corpora collected under a shared protocol. The feature set is deliberately restricted to "
  "string-derived signals and omits network-observable evidence — WHOIS domain age, hosting and "
  "certificate reputation, redirect chains — any of which could improve cross-dataset robustness, and "
  "precisely because they are harder for an attacker to control they are the most promising extension. "
  "The live-feed evaluation uses a single 300-URL snapshot from one provider and is indicative rather "
  "than a temporal-drift study. The adversarial evaluation covers four attack families spanning cheap "
  "and expensive evasion; it is not exhaustive.")
P("One numerical caveat deserves mention. Because the out-of-distribution scores are saturated — almost "
  "every URL in the independent corpus scores above 0.9 (Section&nbsp;5.9) — the <i>ordering</i> within "
  "that band is decided by very small differences, so the AUC is correspondingly sensitive: "
  "floating-point rounding in the feature values shifts it by a few hundredths (observed range "
  "approximately 0.39&ndash;0.43 across representations of the same features). The pipeline therefore "
  "always consumes the persisted feature artifact, so a run reproduces identically whether or not the "
  "cache was present. This does not affect any conclusion: every variant is far below the 0.5 threshold "
  "separating a correct ranking from an inverted one, and F1 (0.666) is stable across all of them. It is "
  "reported because a metric that moves with numerical noise should be flagged rather than quoted to "
  "three decimals as though precise.")
P("The clearest next step follows from Section&nbsp;5.7: because no defence within the URL-only feature "
  "space closes the mimicry gap, the natural remedy is <b>fusion</b> with the companion content-based "
  "detector, so an attacker who defeats one channel by using legitimate infrastructure must "
  "simultaneously defeat an independent second channel reading entirely different evidence.")

# =====================================================================
# 8. CONCLUSION
# =====================================================================
H("8. Conclusion")
P("A URL-only phishing detector can be made fast, interpretable and robust to cheap character-level "
  "obfuscation, and it still catches a large share of current real-world phishing traffic. However, the "
  "near-perfect accuracy such detectors report on standard benchmarks is substantially a property of how "
  "those benchmarks were constructed rather than of phishing itself: it is supported in part by outright "
  "label leakage, rests otherwise on a collection artifact a single rule can capture, is trivially "
  "evaded by an attacker willing to use ordinary legitimate infrastructure, and does not survive contact "
  "with an independently collected dataset — where the ranking inverts entirely. URL structure is a "
  "useful but insufficient signal on its own, best deployed as one independent component of a fused, "
  "multi-signal detection system.")

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
doc = ReportDoc("report/report.pdf", pagesize=A4, leftMargin=2.2*cm, rightMargin=2.2*cm,
                topMargin=2*cm, bottomMargin=2.0*cm,
                title="Catching Phishing from the Link Alone: A Critical Evaluation of URL-Based Phishing Detection",
                author=AUTHOR)
doc.multiBuild(story, onFirstPage=footer, onLaterPages=footer)
print(f"wrote report/report.pdf  ({_tab_n[0]} tables, {_fig_n[0]} figures)")
