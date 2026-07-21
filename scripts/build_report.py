"""Build the blog-style write-up as a PDF (report/blog.pdf) from the computed results."""
import os, pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, Table,
                                TableStyle, HRFlowable, KeepTogether)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

TAB = "results/tables"; FIG = "results/figures"
INK = colors.HexColor("#1d2b3a"); ACCENT = colors.HexColor("#2a9d8f")
RED = colors.HexColor("#e76f51"); TINT = colors.HexColor("#eef4f3"); GREY = colors.HexColor("#5b6472")

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=23, textColor=INK, leading=27, spaceAfter=4, alignment=TA_LEFT)
SUB = ParagraphStyle("SUB", parent=ss["Normal"], fontName="Helvetica", fontSize=12, textColor=ACCENT, leading=15, spaceAfter=2)
META = ParagraphStyle("META", parent=ss["Normal"], fontName="Helvetica-Oblique", fontSize=9.5, textColor=GREY, spaceAfter=12)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=14.5, textColor=INK, spaceBefore=15, spaceAfter=5, leading=17)
BODY = ParagraphStyle("BODY", parent=ss["Normal"], fontName="Helvetica", fontSize=10.3, textColor=colors.HexColor("#222"), leading=15.5, spaceAfter=7, alignment=TA_LEFT)
CAP = ParagraphStyle("CAP", parent=BODY, fontName="Helvetica-Oblique", fontSize=8.6, textColor=GREY, alignment=TA_CENTER, spaceBefore=2, spaceAfter=12)
KEY = ParagraphStyle("KEY", parent=BODY, fontName="Helvetica-Bold", fontSize=10.6, textColor=INK, leading=15)

def key_val(tab, col, row_contains, valcol):
    d = pd.read_csv(f"{TAB}/{tab}.csv")
    r = d[d[col].astype(str).str.contains(row_contains)]
    return r.iloc[0][valcol] if len(r) else "?"

story = []
def P(t): story.append(Paragraph(t, BODY))
def H(t): story.append(Paragraph(t, H2))
def gap(h=4): story.append(Spacer(1, h))
def figure(name, caption, width=15*cm):
    p = f"{FIG}/{name}.png"
    if os.path.exists(p):
        img = Image(p); img._restrictSize(width, 9.5*cm)
        story.append(KeepTogether([img, Paragraph(caption, CAP)]))
def callout(t):
    tb = Table([[Paragraph(t, KEY)]], colWidths=[15.6*cm])
    tb.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), TINT), ("LEFTPADDING",(0,0),(-1,-1),12),
        ("RIGHTPADDING",(0,0),(-1,-1),12), ("TOPPADDING",(0,0),(-1,-1),9), ("BOTTOMPADDING",(0,0),(-1,-1),9),
        ("LINEBEFORE",(0,0),(0,-1),3, ACCENT)]))
    story.append(tb); gap(10)
def table_from_csv(name, ncols=None):
    d = pd.read_csv(f"{TAB}/{name}.csv")
    if ncols: d = d.iloc[:, :ncols]
    data = [list(d.columns)] + d.round(3).astype(str).values.tolist()
    t = Table(data, hAlign="LEFT")
    t.setStyle(TableStyle([("FONT",(0,0),(-1,-1),"Helvetica",8), ("FONT",(0,0),(-1,0),"Helvetica-Bold",8),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white), ("BACKGROUND",(0,0),(-1,0),INK),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, TINT]), ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#cfd8dc")),
        ("LEFTPADDING",(0,0),(-1,-1),5),("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3)]))
    story.append(t); gap(12)

# ---- header ----
story.append(Paragraph("Catching phishing from the link alone", H1))
story.append(Paragraph("...and why “99% accuracy” in URL phishing detection is mostly an illusion", SUB))
story.append(Paragraph("Data Science &amp; Cyber &middot; the URL / link detector (Student B) &middot; code: github.com/segals/phishing-url-detector", META))
story.append(HRFlowable(width="100%", thickness=1.2, color=ACCENT, spaceAfter=10))

xds_f1 = key_val("T4_cross_dataset", "setting", "full model", "f1")
xds_auc = key_val("T4_cross_dataset", "setting", "full model", "auc")
P("Phishing is the number-one way attackers get their first foothold, and a lot of it comes down to a "
  "link. So: can you catch phishing from the <b>URL alone</b>? I built a fast, interpretable URL detector, "
  "got a near-perfect score — and then spent the rest of the project proving that score is a mirage.")
callout("The one-line story: F1 ≈ 1.0 in the lab, driven by a single leaked feature and by HTTP-vs-HTTPS; "
        "evaded to 0% recall by dressing a phishing URL up as a clean home-page; and on an independent "
        f"dataset it collapses to F1 {xds_f1} / AUC {xds_auc} — worse than a coin flip.")

H("1. The data, and a first red flag")
P("I use <b>PhiUSIIL</b> (Prasad &amp; Chandra, 2024; UCI id 967): 235,795 real URLs, 43% phishing, each "
  "with the raw URL. It is one of the largest, most recent public URL datasets. The exploratory plots "
  "already look suspicious — the two classes separate almost perfectly on trivial structural quantities, "
  "which never happens with genuinely hard data.")
figure("F1_eda", "Figure 1. Class balance and two feature distributions. The classes separate far too cleanly.")

H("2. The near-perfect score is a collection artifact")
P("Train on the dataset’s own features and you reproduce the published ~perfect result. But take it "
  "apart: a <b>single</b> feature (<font face='Courier'>URLSimilarityIndex</font>) already scores F1 0.995 "
  "— it is basically the label. And even my honest, hand-built lexical features hit 0.997, because in "
  "this dataset the legitimate URLs are clean HTTPS home-pages and the phishing URLs are messy. The model "
  "learns <i>how the data was collected</i>, not what makes a link dangerous.")
table_from_csv("T0_artifact_decomposition")
P("The trivial baselines make it concrete: predicting the majority class gives 57% accuracy at <b>0% "
  "recall</b> (the accuracy paradox), and a one-line “not-HTTPS → phishing” rule already scores F1 "
  "0.68. That one artifact is doing most of the work — legitimate URLs here are 100% HTTPS, phishing only "
  "49%.")

H("3. What is the model actually using? SHAP says: the artifact")
P("Because the model is a tree ensemble, I use SHAP (Lundberg &amp; Lee, 2017) for faithful attribution. "
  "The #1 driver is <font face='Courier'>is_https</font> by roughly 3× the next feature, followed by "
  "path/structure. The detector is a thin veneer over the HTTP-vs-HTTPS artifact — which is exactly why "
  "the attacks below work.")
figure("F5_shap", "Figure 2. SHAP global importance. is_https dominates; the rest is URL structure.", 12*cm)

H("4. Attack it, then defend it")
P("A structural detector turns out to be <b>robust to the character tricks</b> that break a text model "
  "— homoglyph (Cyrillic look-alikes) and typo-squatting barely move recall (0.99). That is a genuine "
  "complementarity with the content detector, which those same tricks <i>do</i> fool. But the detector is "
  "fragile exactly where it is biased: simply serving the page over HTTPS drops recall to 0.67, and full "
  "home-page mimicry drops it to <b>0.00</b>. Normalization (the homoglyph defense) correctly does nothing "
  "here, and removing <font face='Courier'>is_https</font> barely helps — the bias is diffuse.")
table_from_csv("T3_arms_race")
figure("F3_arms_race", "Figure 3. Structural attacks are harmless; the HTTPS artifact is the exploitable hole.")

H("5. The reality check: it does not generalize")
P("The real test is a <b>different</b> dataset. On the independent Kaggle Malicious-URLs corpus "
  "(Siddhartha, 2021; 651k URLs), the near-perfect model (in-distribution F1 0.997, AUC 0.999) collapses "
  f"to F1 {xds_f1} / AUC {xds_auc} — <b>worse than random</b>. Its ranking literally inverts, because "
  "PhiUSIIL’s “home-page = legit, deep-link = phishing” artifact is reversed in another dataset. Yet it "
  "still catches <b>100% of live OpenPhish phishing</b>, because today’s real phishing is still "
  "structurally messy.")
table_from_csv("T4_cross_dataset")
P("<i>Why</i> does it invert? Distance metrics (the course’s KS and Wasserstein) make it concrete: the "
  "features that shift most between the two datasets are precisely the ones the model leans on — "
  "<font face='Courier'>is_https</font>, <font face='Courier'>path_len</font>, "
  "<font face='Courier'>n_subdomain</font>. The detector built its decision on the least transferable "
  "signals.")
figure("F7_domain_shift", "Figure 4. KS distance PhiUSIIL→Kaggle. The top-shifted features are the top SHAP drivers.")

H("6. So what is a URL detector good for?")
P("Honestly: as <b>one layer</b>, not the answer. It is fast (~milliseconds), private (nothing leaves the "
  "device), interpretable, robust to character-level obfuscation, and it catches today’s messy phishing. "
  "But URL <i>structure alone is not a generalizable phishing signal</i> — it is trivially evaded by an "
  "attacker who hosts on legitimate HTTPS infrastructure, and it does not survive a change of dataset. The "
  "right design is <b>fusion</b>: combine this link channel with my partner’s content channel and with "
  "non-lexical signals (domain age, reputation), so that when an attacker beats one channel, another still "
  "fires.")
callout("Bottom line: the celebrated near-perfect URL benchmarks measure dataset construction, not "
        "phishing detection. An honest URL detector is a useful, robust <i>second opinion</i> — not a "
        "standalone solution.")

H("Appendix — course concepts used")
P("EDA, distributions, skewness/kurtosis, robust statistics &middot; Pearson vs Spearman correlation, "
  "Mann–Whitney U &middot; feature engineering, Shannon entropy, Levenshtein edit distance &middot; the "
  "accuracy paradox, Precision/Recall/F1/F2/MCC/AUC, cost-sensitive thresholds &middot; bootstrap CIs, "
  "McNemar &middot; explainability (SHAP) &middot; adversarial ML (evasion, perturbation, homoglyphs, "
  "adversarial training) &middot; anomaly detection (Isolation Forest, LOF) &middot; calibration &middot; "
  "domain shift and distance metrics (KS, Wasserstein/EMD) &middot; feature ablation and error analysis.")
P("<font size=8 color='#5b6472'>Data: PhiUSIIL (Prasad &amp; Chandra 2024), Kaggle Malicious-URLs "
  "(Siddhartha 2021), OpenPhish, Majestic Million. Methods/refs: Ma 2009; Garera 2007; Sahingoz 2019; Le "
  "2018 (URLNet); Boucher 2022; Lundberg &amp; Lee 2017; Unicode TR39.</font>")

os.makedirs("report", exist_ok=True)
SimpleDocTemplate("report/blog.pdf", pagesize=A4, leftMargin=2.4*cm, rightMargin=2.4*cm,
                  topMargin=2*cm, bottomMargin=2*cm, title="Catching phishing from the link alone"
                  ).build(story)
print("wrote report/blog.pdf")
