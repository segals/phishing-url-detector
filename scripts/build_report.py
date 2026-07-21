"""Build the formal submission report (report/report.pdf) from the computed results.

Academic report style: numbered sections, figure/table captions, references,
running header/footer with page numbers. ~10 pages. Written in the third
person / "we" register, distinct from the first-person notebook narrative.
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

AUTHOR = "Student B — URL / Link Detector"   # replace with your name if desired
COURSE = "Data Science &amp; Cyber — Dr. Uri Itai"
REPO = "github.com/segals/phishing-url-detector"

ss = getSampleStyleSheet()
TITLE = ParagraphStyle("TITLE", fontName="Times-Bold", fontSize=19, textColor=INK, leading=23, spaceAfter=4, alignment=TA_LEFT)
SUBTITLE = ParagraphStyle("SUBTITLE", fontName="Times-Italic", fontSize=12.5, textColor=SLATE, leading=16, spaceAfter=10)
META = ParagraphStyle("META", fontName="Times-Roman", fontSize=9.5, textColor=GREY, leading=13, spaceAfter=2)
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
def H(t, n=None):
    story.append(Paragraph(t, H1))
def H2f(t): story.append(Paragraph(t, H2))
def gap(h=4): story.append(Spacer(1, h))

def table_from_csv(name, caption, ncols=None, nrows=None, col_widths=None, fontsize=8):
    _tab_n[0] += 1
    d = pd.read_csv(f"{TAB}/{name}.csv")
    if d.columns[0].startswith("Unnamed"):
        d = d.rename(columns={d.columns[0]: "feature"})
    if ncols: d = d.iloc[:, :ncols]
    if nrows: d = d.head(nrows)
    data = [list(d.columns)] + d.round(3).astype(str).values.tolist()
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
    story.append(KeepTogether([t, Paragraph(f"<b>Table {_tab_n[0]}.</b> {caption}", CAP)]))

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
P(f"{AUTHOR} &nbsp;&middot;&nbsp; {COURSE}", META)
P(f"Code and reproducible results: {REPO}", META)
story.append(HRFlowable(width="100%", thickness=1, color=RULE, spaceBefore=8, spaceAfter=10))

P("Abstract", ABSTRACT_H)
xds_f1 = val("T4_cross_dataset", "setting", "full model", "f1")
xds_auc = val("T4_cross_dataset", "setting", "full model", "auc")
P("Phishing remains a leading initial-access vector, and a substantial fraction of it is carried "
  "entirely by a malicious link. This report presents an independent, URL-only phishing detector "
  "(one component of a two-part course project; a companion module analyses email content) and "
  "subjects it to a rigorous critical evaluation rather than treating a high benchmark score as "
  "the end of the analysis. Trained on 235,795 real URLs (PhiUSIIL; Prasad &amp; Chandra, 2024), a "
  "gradient-boosted classifier over 40 hand-engineered lexical features reaches F1&nbsp;=&nbsp;0.997 "
  "in-distribution &mdash; matching the near-perfect scores reported in the literature. We show, using "
  "single-feature ablation, explainability (SHAP), and a feature-group ablation, that this score is "
  "driven overwhelmingly by a dataset collection artifact (legitimate URLs are 100% HTTPS versus 49% "
  "for phishing in this corpus) rather than a transferable phishing signal. An adversarial evaluation "
  "shows the detector is robust to character-level obfuscation (homoglyphs, typosquatting; recall "
  "&ge;&nbsp;0.99) but is evaded completely (recall&nbsp;=&nbsp;0.00) by hosting phishing content on "
  "ordinary HTTPS infrastructure with a clean, short URL. Most critically, evaluated on an independent, "
  f"651,191-URL corpus (Siddhartha, 2021), the detector collapses to F1&nbsp;=&nbsp;{xds_f1}, "
  f"AUC&nbsp;=&nbsp;{xds_auc} &mdash; worse than random ranking &mdash; while distance-metric analysis "
  "(Kolmogorov&ndash;Smirnov, Wasserstein) confirms the collapse is driven by exactly the features the "
  "model relies on most. We conclude that URL structure alone is not a generalisable phishing signal "
  "and argue for its use as one channel in a fused, multi-signal detector.", ABSTRACT)

# =====================================================================
# 1. INTRODUCTION
# =====================================================================
H("1. Introduction")
P("Phishing attacks rely on a victim following a malicious link, so the URL itself is an attractive, "
  "lightweight detection surface: it can be scored in milliseconds, requires no page fetch, and "
  "preserves user privacy. A large body of published work reports near-perfect (F1 &gt; 0.99) "
  "classification accuracy on public URL datasets, which could suggest the problem is essentially "
  "solved. This report interrogates that claim.")
P("The project is deliberately structured as a critical evaluation rather than a model-accuracy "
  "exercise: we reproduce the strong published result, then systematically ask whether it reflects "
  "genuine phishing-specific signal or an artifact of how the benchmark dataset was constructed. We "
  "organise the investigation around four research questions.")
P("<b>RQ1 (signal).</b> How much of the reported near-perfect score survives once dataset-specific "
  "leakage and collection bias are accounted for? "
  "<b>RQ2 (robustness).</b> How does the detector respond to an adversary who deliberately reshapes a "
  "phishing URL's surface features? "
  "<b>RQ3 (generalisation).</b> Does the in-distribution score transfer to an independent dataset and "
  "to live, current phishing traffic? "
  "<b>RQ4 (explainability).</b> Which features actually drive the decision, and does that explain the "
  "robustness and generalisation results?")
P("This module is one of two independent, complementary detectors built for the course project: this "
  "report covers the <b>URL/link</b> channel; a companion module covers the <b>email content</b> "
  "channel. The two were designed and evaluated independently; fusing them is identified as future "
  "work in Section&nbsp;7.")

# =====================================================================
# 2. RELATED WORK
# =====================================================================
H("2. Related Work")
P("Lexical and host-based URL features for phishing detection were established by Ma "
  "<i>et&nbsp;al.</i> (2009) and Garera <i>et&nbsp;al.</i> (2007), who showed that structural "
  "properties of a URL &mdash; length, host composition, presence of an IP address, brand tokens "
  "&mdash; carry substantial discriminative signal without inspecting page content. Sahingoz "
  "<i>et&nbsp;al.</i> (2019) and subsequent survey work catalogue the resulting feature families, "
  "which we largely follow in Section&nbsp;4.1. Deep, character-level models such as URLNet (Le "
  "<i>et&nbsp;al.</i>, 2018) learn representations directly from the URL string, trading "
  "interpretability for potential accuracy gains; we deliberately favour interpretable, hand-engineered "
  "features so that the artifact identified in Section&nbsp;5 can be attributed to specific, "
  "human-readable causes.")
P("On the adversarial side, Boucher <i>et&nbsp;al.</i> (2022) document imperceptible-perturbation "
  "attacks against NLP and web-facing systems, including homoglyph substitution; the Unicode "
  "Technical Standard&nbsp;#39 (confusables) underlies the character-folding defence used against such "
  "attacks in Section&nbsp;5.5. For explainability we use SHAP (Lundberg &amp; Lee, 2017), a "
  "game-theoretic feature-attribution method with additivity guarantees that tree-based models lack "
  "natively. Our central methodological concern &mdash; that reported phishing-detection accuracy may "
  "not transfer across datasets &mdash; echoes a growing body of recent work directly questioning "
  "whether phishing URL features generalise across independently collected corpora; we treat this as "
  "a hypothesis to test empirically (Section&nbsp;5.9&ndash;5.10) rather than assume.")

# =====================================================================
# 3. DATA
# =====================================================================
H("3. Data")
H2f("3.1 Primary corpus: PhiUSIIL")
P("The primary dataset is <b>PhiUSIIL</b> (Prasad &amp; Chandra, 2024; UCI Machine Learning "
  "Repository, id&nbsp;967), comprising 235,795 real URLs with a raw URL string, a binary label, "
  "and 53 pre-computed descriptive features. It is among the largest and most recent public URL "
  "datasets and is a common benchmark in the literature, which motivates its use here as the primary "
  "object of critique.")
table_from_csv("T1_dataset", "Composition of the primary PhiUSIIL corpus.", col_widths=[3.1*cm,2.1*cm,2.4*cm,2.4*cm,2.4*cm])

H2f("3.2 Secondary corpora")
P("Two independent sources support the generalisation analysis (Section&nbsp;5.9): the Kaggle "
  "<i>Malicious URLs Dataset</i> (Siddhartha, 2021; 651,191 URLs spanning benign, phishing, "
  "defacement, and malware classes, of which the benign/phishing subset is used) and a live snapshot "
  "of the OpenPhish community feed (300 currently active phishing URLs). A ranked list of legitimate "
  "domains (Majestic Million) was used in early exploratory checks and is superseded by the "
  "Kaggle corpus for the reported cross-dataset result, since the latter is itself a mixed, "
  "independently labelled corpus rather than an unlabelled top-sites list.")

H2f("3.3 Data preparation")
P("Labels were standardised to the convention 1&nbsp;=&nbsp;phishing, 0&nbsp;=&nbsp;legitimate "
  "(PhiUSIIL natively encodes the opposite polarity). Rows with a missing URL or label were dropped; "
  "the URL column was stripped of surrounding whitespace; and rows were de-duplicated on the exact URL "
  "string prior to splitting, so that no URL could appear in both the training and test partitions "
  "(235,795 &rarr; 235,370 rows after de-duplication). No class rebalancing, outlier removal, or "
  "imputation was performed &mdash; the natural class ratio of the source data "
  "(42.7% phishing) is retained throughout, so that the results reported below are not an artifact of "
  "our own preprocessing choices. Data were split 60/20/20 into train/validation/test using a fixed "
  "random seed (42) with stratification on the label; the test partition was evaluated exactly once. "
  "For reproducibility, the cleaned dataset is hashed (SHA-256) and logged alongside its row count and "
  "class balance in the project repository.")

# =====================================================================
# 4. METHODOLOGY
# =====================================================================
H("4. Methodology")
H2f("4.1 Feature engineering")
P("Every feature is computed from the URL string alone, requiring no network access. Forty features "
  "are grouped into six families: <i>lexical/length</i> (character and token counts, digit ratio), "
  "<i>host/domain</i> (subdomain count, IP-literal host, port), <i>TLD</i> (suffix length, membership "
  "in an abuse-associated TLD list), <i>entropy</i> (Shannon entropy of the URL, host, and registrable "
  "domain), <i>scheme/encoding</i> (HTTPS, punycode, percent-encoding), and <i>brand/cue</i> "
  "(minimum Levenshtein edit distance to a list of eighteen frequently-impersonated brands, and the "
  "count of urgency/credential cue words). Shannon entropy is computed as "
  "H(s) = &minus;&Sigma;<sub>i</sub> p<sub>i</sub> log&#8322; p<sub>i</sub> over the character "
  "distribution of a string s; higher values indicate less predictable, more random-looking strings, "
  "characteristic of algorithmically generated domains. The Levenshtein edit distance between two "
  "strings is the minimum number of single-character insertions, deletions, or substitutions required "
  "to transform one into the other, computed by the standard dynamic-programming recurrence; a "
  "registered domain label within edit distance 1&ndash;2 of a known brand (e.g. <i>paypa1</i> versus "
  "<i>paypal</i>) is flagged as a probable typosquat.")

H2f("4.2 Models")
P("Three classifiers were compared, selected on validation F1: <b>logistic regression</b> (a linear, "
  "directly interpretable baseline, features standardised), <b>random forest</b> (a bagged ensemble "
  "of decision trees), and <b>histogram-based gradient boosting</b> (trees fit sequentially to "
  "residual error). All hyperparameter and model-selection decisions were made on the validation "
  "partition; the test partition was not consulted until final evaluation.")

H2f("4.3 Evaluation protocol")
P("Because the majority class is a substantial fraction of the data, accuracy alone is not reported "
  "as a primary metric (the <i>accuracy paradox</i>: a majority-class classifier attains 57.3% "
  "accuracy while achieving zero recall &mdash; Section&nbsp;5.1). We report precision, recall, F1, "
  "F2 (recall-weighted, reflecting that a missed phishing URL is costlier than a false alarm), the "
  "Matthews Correlation Coefficient (MCC, which uses all four confusion-matrix cells and is stable "
  "under class imbalance), and AUC-ROC (the probability that a randomly drawn phishing URL is scored "
  "above a randomly drawn legitimate one; 0.5 indicates uninformative ranking). Every headline metric "
  "is accompanied by a bootstrap 95% confidence interval (1,000 resamples of the test set with "
  "replacement), and pairwise model comparisons use McNemar's test on the discordant predictions of "
  "the same test set, so that no comparative claim rests on a single point estimate.")

H2f("4.4 Threat model and adversarial evaluation")
P("We model an attacker with black-box query access who can freely choose the phishing URL's surface "
  "form but must keep it functional (it must still resolve to the attacker's content). Four "
  "perturbation families are evaluated: <i>homoglyph substitution</i> (Latin characters replaced with "
  "visually identical Cyrillic/Greek confusables), <i>typosquatting</i> (a single character duplicated "
  "or inserted in the registered domain), <i>scheme upgrade</i> (serving the identical page over "
  "HTTPS instead of HTTP), and <i>home-page mimicry</i> (hosting on a short, clean, path-free HTTPS "
  "domain, approximating abuse of legitimate cloud-hosting infrastructure). Two defences are evaluated "
  "against the detector's original features: <i>canonicalisation</i> (folding confusable characters "
  "back to their ASCII skeleton before scoring, following the Unicode TR39 approach) and "
  "<i>de-biasing</i> (retraining with the HTTPS feature removed, to test whether the artifact is "
  "concentrated in a single feature or distributed across correlated ones).")

H2f("4.5 Generalisation and diagnostic tools")
P("Cross-dataset generalisation is measured by training exclusively on PhiUSIIL and evaluating, "
  "without any retraining, on the independent Kaggle corpus and on the live OpenPhish feed. To "
  "diagnose <i>why</i> any observed gap occurs, we compare the per-feature distributions of the two "
  "datasets using the Kolmogorov&ndash;Smirnov statistic (the maximum vertical gap between two "
  "empirical cumulative distribution functions) and the Wasserstein (earth-mover's) distance (the "
  "minimum total probability mass, weighted by distance moved, required to transform one distribution "
  "into the other). We additionally report two label-free anomaly detectors trained only on "
  "legitimate URLs (Isolation Forest and Local Outlier Factor) as an independent, weaker-assumption "
  "point of comparison, and assess probability calibration via the Brier score and a reliability "
  "curve.")

# =====================================================================
# 5. RESULTS
# =====================================================================
H("5. Results")

H2f("5.1 Baseline behaviour and the accuracy paradox")
P("Table&nbsp;2 reports three trivial baselines. A majority-class predictor attains 57.3% accuracy "
  "with zero recall, illustrating the accuracy paradox and motivating the metric choices in "
  "Section&nbsp;4.3. More strikingly, a single hand-written rule &mdash; flag any non-HTTPS URL as "
  "phishing &mdash; already attains F1&nbsp;=&nbsp;0.68 with no learning involved, foreshadowing the "
  "artifact analysis below.")
table_from_csv("T1b_baselines", "Trivial baselines. A single-rule HTTPS check alone reaches F1 0.68.")

H2f("5.2 Decomposing the near-perfect score")
P("Training on all 50 dataset-provided features reproduces the near-perfect published result "
  "(F1&nbsp;=&nbsp;1.000). Decomposing this score is the central diagnostic of this report "
  "(Table&nbsp;3). A single provided feature, <i>URLSimilarityIndex</i>, alone attains "
  "F1&nbsp;=&nbsp;0.995, indicating that feature is effectively derived from the label (a leakage "
  "artifact rather than a genuine predictor). Our own 40 hand-engineered, leakage-free lexical "
  "features attain F1&nbsp;=&nbsp;0.997 &mdash; still near-perfect, but for a different and more "
  "diagnosable reason, explored via explainability in Section&nbsp;5.4.")
table_from_csv("T0_artifact_decomposition", "Decomposing the near-perfect score: all provided features, a single leaked feature, and our own honest lexical features.", col_widths=[7.4*cm,1.7*cm,1.7*cm,3*cm])
P(f"The mechanism is direct: in PhiUSIIL, 100% of legitimate URLs use HTTPS versus only 48.6% of "
  f"phishing URLs (Table&nbsp;4). This 51-point gap is a property of how the two classes were "
  f"collected, not an inherent property of phishing.")
table_from_csv("T3a_https_artifact", "HTTPS usage by class in PhiUSIIL &mdash; the primary collection artifact.", col_widths=[6*cm,4*cm])

H2f("5.3 Feature distributions and non-parametric tests")
P("URL-derived features are strongly right-skewed and heavy-tailed (e.g. URL length has a skewness "
  "of 54.7 and excess kurtosis of 5,812), which motivates rank-based statistics over parametric "
  "ones. Spearman correlation with the label often diverges substantially from Pearson correlation "
  "&mdash; e.g. path length has Pearson r&nbsp;=&nbsp;0.17 but Spearman &rho;&nbsp;=&nbsp;0.67 "
  "&mdash; indicating a strong monotonic but non-linear relationship that a linear correlation "
  "coefficient alone would understate. A Mann&ndash;Whitney U test (chosen over a t-test given the "
  "skewed, non-normal feature distributions) confirms every leading feature differs significantly "
  "between classes (p&nbsp;&lt;&nbsp;10<sup rise='3' size='6'>&minus;300</sup> for the features "
  "tested, reflecting the very large sample size); HTTPS shows a perfect median separation "
  "(median&nbsp;=&nbsp;0 for phishing, 1 for legitimate).")
table_from_csv("T7_correlation", "Feature&ndash;label correlation, Pearson vs. Spearman (top 10 by |Spearman|).", nrows=10, col_widths=[4.6*cm,3.2*cm,3.2*cm])

H2f("5.4 Model comparison")
P("Table&nbsp;6 compares the three candidate classifiers on the honest 40-feature representation. "
  "Random forest and histogram gradient boosting are statistically indistinguishable "
  "(McNemar p&nbsp;=&nbsp;1.00) and both significantly outperform logistic regression "
  "(p&nbsp;=&nbsp;7.7&times;10<sup rise='3' size='6'>&minus;15</sup>); the gradient-boosted model is "
  "used as the reference detector for all subsequent experiments.")
table_from_csv("T2_model_comparison", "Model comparison with bootstrap 95% CIs and McNemar tests against the best model.", fontsize=7.3, col_widths=[2.4*cm,1.9*cm,1.9*cm,1.9*cm,1.6*cm,1.9*cm,1.9*cm,1.9*cm])

H2f("5.5 Explainability")
P("SHAP attribution (Table&nbsp;7, Figure&nbsp;1) identifies <i>is_https</i> as the dominant feature "
  "by a factor of roughly three over the next-ranked feature, directly implicating the artifact "
  "identified in Section&nbsp;5.2 as the model's primary decision driver rather than an incidental "
  "correlate.")
table_from_csv("T5_shap_importance", "Global SHAP feature importance (top 8 of 40).", nrows=8, col_widths=[6*cm,4*cm])
figure("F5_shap", "SHAP global feature importance. is_https dominates the model's decisions.", width=10.5*cm, height=7.2*cm)

H2f("5.6 Feature-group ablation")
P("Grouping the 40 features into six families and training on each family alone (Table&nbsp;8) "
  "reveals that the artifact is not confined to a single feature: the plain <i>length/counts</i> "
  "group (8 features, none of them <i>is_https</i>) alone reaches F1&nbsp;=&nbsp;0.993, nearly "
  "matching the full model, while the <i>brand/cue</i> family &mdash; the features most directly "
  "associated with phishing intent in prior literature &mdash; is the weakest in isolation "
  "(F1&nbsp;=&nbsp;0.273). The artifact is therefore distributed across a cluster of correlated "
  "structural proxies for &ldquo;clean home-page&rdquo; versus &ldquo;deep, messy link,&rdquo; which "
  "anticipates the limited effect of the de-biasing defence in Section&nbsp;5.7.")
table_from_csv("T12_ablation", "Feature-group ablation. Length/count features alone nearly reproduce the full model.", col_widths=[4.2*cm,2.6*cm,1.9*cm,1.9*cm])

H2f("5.7 Adversarial robustness")
P("Table&nbsp;9 and Figure&nbsp;2 report recall on phishing URLs under each attack, with and without "
  "each defence. Character-level attacks (homoglyph substitution, typosquatting) leave recall "
  "essentially unchanged (&ge;&nbsp;0.99): a structural detector is largely insensitive to the exact "
  "characters used, in contrast to lexical text classifiers, which such attacks are known to defeat. "
  "The detector is, however, highly vulnerable along the axis it is biased on: a scheme upgrade alone "
  "(HTTP&rarr;HTTPS, no other change) reduces recall to 0.672, and home-page mimicry defeats the "
  "detector completely (recall&nbsp;=&nbsp;0.000). Canonicalisation, as expected, has no effect on "
  "these two attacks (there is no confusable character to fold); removing <i>is_https</i> and "
  "retraining recovers only marginally (0.672&nbsp;&rarr;&nbsp;0.704), confirming the ablation "
  "finding in Section&nbsp;5.6 that the bias is diffuse rather than localised to one feature, and "
  "that no purely feature-engineering fix within the URL-only feature space closes this gap.")
table_from_csv("T3_arms_race", "Recall on phishing under each attack and defence.", col_widths=[3.6*cm,3.2*cm,3.2*cm,3.6*cm])
figure("F3_arms_race", "Recall under structural attacks (robust) versus artifact-exploiting attacks (evaded).", width=13*cm, height=6.6*cm)

H2f("5.8 Unsupervised anomaly detection and calibration")
P("As an independent, weaker-assumption comparison, two unsupervised anomaly detectors were trained "
  "exclusively on legitimate URLs (no phishing labels). Isolation Forest attains AUC&nbsp;=&nbsp;0.828 "
  "and Local Outlier Factor AUC&nbsp;=&nbsp;0.944 &mdash; respectable given the absence of labels, "
  "though both remain below the supervised model and are still expected to be sensitive to the same "
  "structural artifacts. In-distribution, the supervised detector's predicted probabilities are "
  "well-calibrated (Brier score&nbsp;=&nbsp;0.0025); Section&nbsp;5.10 shows this calibration does "
  "not survive the change of dataset.")
table_from_csv("T10_anomaly", "Unsupervised anomaly detectors trained on legitimate URLs only.", col_widths=[6*cm,4*cm])

H2f("5.9 Cross-dataset generalisation")
P(f"The central generalisation result is reported in Table&nbsp;10 and Figure&nbsp;3. The "
  f"in-distribution detector (F1&nbsp;=&nbsp;0.997, AUC&nbsp;=&nbsp;0.999) collapses on the "
  f"independent Kaggle corpus to F1&nbsp;=&nbsp;{xds_f1}, "
  f"AUC&nbsp;=&nbsp;{xds_auc}. Figure&nbsp;3 makes the mechanism directly visible: in-distribution, "
  "the predicted-probability distributions for the two classes are cleanly separated (legitimate URLs "
  "cluster near 0, phishing URLs near 1); on the independent corpus, <b>both</b> classes collapse to "
  "the same region near 1.0 (mean predicted probability 1.000 for benign URLs and 0.999 for phishing "
  "URLs &mdash; 100.0% of benign and 99.9% of phishing scored above 0.9). The model has not merely "
  "become less confident; it treats the two classes as indistinguishable. An AUC below 0.5 reflects "
  "this precisely: within that saturated band, benign URLs are on average scored fractionally "
  "<i>higher</i> than phishing URLs, so the ranking is not just uninformative but systematically "
  "inverted. This explains why re-thresholding &mdash; selecting the cost-optimal cutoff rather than "
  "the default 0.5 &mdash; recovers almost nothing (F1&nbsp;0.666&nbsp;&rarr;&nbsp;0.667): "
  "re-thresholding can correct a model whose ranking is intact but miscalibrated, not one whose "
  "outputs no longer separate the classes at all. Notably, recall on the <b>live OpenPhish</b> feed "
  "of current, real phishing URLs remains 1.00, indicating that present-day phishing URLs are still "
  "structurally &ldquo;messy&rdquo; even though the lab dataset's own legitimate class is not "
  "representative of general legitimate web traffic.")
table_from_csv("T4_cross_dataset", "Cross-dataset generalisation: in-distribution versus an independent 651k-URL corpus and a live phishing feed.", fontsize=7.6, col_widths=[6.2*cm,1.9*cm,2.6*cm,1.9*cm,2*cm])
figure("F4_cross_dataset", "Predicted-probability distributions by true class, in-distribution versus the independent corpus. In-distribution the classes are cleanly separated; on the independent corpus both collapse to the same saturated region.", width=11*cm, height=6.2*cm)

H2f("5.10 Diagnosing the collapse")
P("To identify <i>why</i> generalisation fails, Table&nbsp;11 ranks features by the "
  "Kolmogorov&ndash;Smirnov distance between their PhiUSIIL and Kaggle distributions. The most-shifted "
  "features &mdash; <i>is_https</i>, <i>path_len</i>, and <i>n_subdomain</i> &mdash; are precisely the "
  "features SHAP identified as the model's strongest decision drivers (Section&nbsp;5.5). The "
  "detector's accuracy is therefore built on the least transferable part of the feature space; this "
  "is a mechanistic, quantitative explanation for the collapse in Section&nbsp;5.9, not merely a "
  "restatement of it.")
table_from_csv("T9_domain_shift", "Distributional shift (Kolmogorov&ndash;Smirnov, normalised Wasserstein distance) between PhiUSIIL and the Kaggle corpus, top 8 features.", nrows=8, col_widths=[4.2*cm,3.2*cm,3.2*cm])
figure("F7_domain_shift", "KS distance per feature between the two datasets. The top-shifted features match the top SHAP drivers.", width=11.5*cm, height=6.5*cm)

H2f("5.11 Error analysis")
P("On the clean, in-distribution test set (47,074 URLs) the detector makes very few errors: 15 false "
  "positives and 119 false negatives. Manual inspection shows false positives are dominated by "
  "legitimate sites on uncommon top-level domains, and false negatives include a phishing page hosted "
  "on a legitimate developer-sandbox subdomain (an in-the-wild instance of the home-page-mimicry "
  "attack modelled in Section&nbsp;5.7) alongside confidently-scored gibberish domains. The rarity of "
  "in-distribution errors stands in contrast to the severity of the cross-dataset and mimicry "
  "failures, underscoring that clean-data error analysis alone would have missed the project's central "
  "finding.")
table_from_csv("T13_error_counts", "Error counts on the clean, in-distribution test set.", col_widths=[6*cm,4*cm])

# =====================================================================
# 6. DISCUSSION
# =====================================================================
H("6. Discussion")
P("The four research questions posed in Section&nbsp;1 can now be answered directly. "
  "<b>RQ1</b>: essentially none of the headline near-perfect score reflects a phishing-specific "
  "signal once the leaked feature and the HTTPS collection artifact are accounted for; a one-line "
  "rule recovers the majority of a naive model's apparent skill (Section&nbsp;5.1&ndash;5.2). "
  "<b>RQ2</b>: the detector is genuinely robust to cheap character-level evasion, but this robustness "
  "is incidental to its structural feature design rather than a deliberately engineered defence, and "
  "it provides no protection against an attacker who simply uses legitimate hosting (Section&nbsp;5.7). "
  "<b>RQ3</b>: the score does not transfer &mdash; not only does it degrade, its ranking inverts on an "
  "independent dataset, which is a materially worse failure mode than the miscalibration typically "
  "assumed in domain-adaptation settings (Section&nbsp;5.9). <b>RQ4</b>: explainability and distance "
  "metrics jointly and independently converge on the same small set of features as both the strongest "
  "decision drivers and the most dataset-specific, non-transferable signals (Section&nbsp;5.10) "
  "&mdash; a rare case where two different diagnostic tools corroborate one causal story.")
P("These findings are consistent with, and add a controlled adversarial and cross-dataset dimension "
  "to, recent literature questioning whether phishing URL features are trustworthy across datasets "
  "(Section&nbsp;2). They also parallel, on a structurally different signal, the companion "
  "content-based detector's finding that a near-perfect in-distribution text classifier degrades "
  "sharply on out-of-distribution and adversarially perturbed email &mdash; suggesting the fragility "
  "observed here is not specific to URL features but a more general property of narrow, single-signal "
  "phishing classifiers evaluated only in-distribution.")

# =====================================================================
# 7. LIMITATIONS AND FUTURE WORK
# =====================================================================
H("7. Limitations and Future Work")
P("The cross-dataset comparison, while informative, is not perfectly controlled: PhiUSIIL and the "
  "Kaggle corpus differ in collection methodology as well as in genuine URL characteristics, so some "
  "portion of the measured shift may reflect encoding or crawling conventions rather than a property "
  "of phishing URLs per se; the de-biased (no-HTTPS) variant, which still fails "
  "(AUC&nbsp;=&nbsp;0.168), is presented as partial evidence that the failure is not attributable to a "
  "single confound. The feature set is intentionally limited to string-derived signals; it omits "
  "network-observable and third-party signals such as domain age (WHOIS), hosting reputation, "
  "certificate metadata, and redirect-chain analysis, any of which could plausibly improve "
  "cross-dataset robustness and would be a natural extension. The live-feed check uses a single "
  "snapshot of 300 URLs from one feed and should be treated as indicative rather than a comprehensive "
  "temporal-drift study. Finally, and most directly motivated by Section&nbsp;5.7's finding that no "
  "URL-only defence closes the mimicry gap, the clearest next step is <b>fusion</b> with the "
  "companion content-based detector, so that an attacker who defeats one channel (e.g. by using "
  "legitimate hosting) must simultaneously defeat an independent second channel operating on entirely "
  "different evidence.")

# =====================================================================
# 8. CONCLUSION
# =====================================================================
H("8. Conclusion")
P("A URL-only phishing detector can be made fast, interpretable, and robust to cheap character-level "
  "obfuscation, and it continues to catch a large share of current real-world phishing traffic. "
  "However, the widely reported near-perfect accuracy of such detectors on standard benchmarks is "
  "substantially a property of how those benchmarks were constructed rather than of phishing itself: "
  "it is trivially evaded by an attacker willing to use ordinary legitimate infrastructure, and it "
  "does not survive contact with an independently collected dataset. We conclude that URL structure "
  "is a useful but insufficient signal on its own, best deployed as one component of a fused, "
  "multi-signal detection system rather than as a stand-alone solution.")

# =====================================================================
# REFERENCES
# =====================================================================
H("References")
refs = [
 "Prasad, A. &amp; Chandra, S. (2024). PhiUSIIL: A diverse security profile empowered phishing URL "
 "detection framework based on similarity index and incremental learning. <i>Computers &amp; Security</i>, "
 "136. UCI Machine Learning Repository, dataset id 967.",
 "Siddhartha, M. (2021). <i>Malicious URLs Dataset</i>. Kaggle.",
 "OpenPhish. Community phishing feed. https://openphish.com",
 "Majestic. <i>The Majestic Million</i>. https://majestic.com",
 "Ma, J., Saul, L. K., Savage, S., &amp; Voelker, G. M. (2009). Beyond blacklists: learning to detect "
 "malicious web sites from suspicious URLs. <i>Proceedings of the 15th ACM SIGKDD International "
 "Conference on Knowledge Discovery and Data Mining</i>.",
 "Garera, S., Provos, N., Chew, M., &amp; Rubin, A. D. (2007). A framework for detection and measurement "
 "of phishing attacks. <i>Proceedings of the 2007 ACM Workshop on Recurring Malcode</i>.",
 "Sahingoz, O. K., Buber, E., Demir, O., &amp; Diri, B. (2019). Machine learning based phishing "
 "detection from URLs. <i>Expert Systems with Applications</i>, 117, 345&ndash;357.",
 "Le, H., Pham, Q., Sahoo, D., &amp; Hoi, S. C. H. (2018). URLNet: learning a URL representation with "
 "deep learning for malicious URL detection. <i>arXiv:1802.03162</i>.",
 "Boucher, N., Shumailov, I., Anderson, R., &amp; Papernot, N. (2022). Bad characters: imperceptible "
 "NLP attacks. <i>2022 IEEE Symposium on Security and Privacy</i>.",
 "Lundberg, S. M. &amp; Lee, S.-I. (2017). A unified approach to interpreting model predictions. "
 "<i>Advances in Neural Information Processing Systems</i>, 30.",
 "Unicode Consortium. <i>Unicode Technical Standard #39: Unicode Security Mechanisms</i> "
 "(confusables.txt).",
]
for i, r in enumerate(refs, 1):
    story.append(Paragraph(f"[{i}]&nbsp;&nbsp;{r}", REF))

os.makedirs("report", exist_ok=True)
doc = SimpleDocTemplate("report/report.pdf", pagesize=A4, leftMargin=2.2*cm, rightMargin=2.2*cm,
                        topMargin=2*cm, bottomMargin=2.1*cm, title="Catching Phishing from the Link Alone",
                        author=AUTHOR.replace("&nbsp;", " "))
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("wrote report/report.pdf")
