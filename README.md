# Catching phishing from the link alone

A URL-based phishing detector — and an honest look at why the headline accuracy in
this field is usually too good to be true.

This is one half of a two-part course project (Data Science & Cyber). A partner built the
**content** detector, which reads the email text; this repo is the **link** detector, which
ignores the words entirely and decides *phishing vs. legitimate* from the URL and its
structure. The two are independent by design.

## The short version

Train a model on a modern public URL dataset and you get a near-perfect score — **F1 ≈ 1.0**.
That number is real, and it is also mostly an illusion:

- A **single** provided feature (`URLSimilarityIndex`) already scores F1 ≈ 0.996, i.e. it is
  almost the label itself.
- Even plain hand-built lexical features hit F1 ≈ 0.99 — because in this dataset the legitimate
  URLs are clean home-pages (short, `https`) and the phishing URLs are messy. The classifier is
  really learning *how the two halves of the dataset were collected*, not what makes a URL
  dangerous.

So the interesting work is everything *after* the headline: measuring how much of the score is a
collection artifact, how badly it falls apart on a **different** dataset, and how easily an
attacker can dress a phishing URL up to look clean. That is what this project is about.

## Data (all public, all cited)

- **Primary — PhiUSIIL** (235,795 URLs; 134,850 legitimate / 100,945 phishing). Prasad, A. &
  Chandra, S. (2024), *PhiUSIIL: A diverse security profile empowered phishing URL detection
  framework*, Computers & Security 136. UCI ML Repository, id 967. Fetched by
  `scripts/fetch_data.py` (no login needed).
- **Cross-dataset / out-of-distribution** and a **modern live feed** are added for the
  generalization and drift experiments (see the report).

## Layout

```
src/            data.py · features.py (40 URL features) · models.py · stats.py · attacks.py · normalize.py · explain.py
scripts/        fetch_data.py (get PhiUSIIL) · build helpers
notebooks/      url_detector.ipynb — the end-to-end deliverable
results/        tables/ and figures/
report/         the write-up (blog-style PDF)
presentation/   the slide deck
```

## Reproduce

```
pip install -r requirements.txt
python scripts/fetch_data.py      # downloads PhiUSIIL to data/raw/
python run_all.py                 # regenerates every table and figure  (seeded, deterministic)
```

## Status

Foundation in place (data pipeline, 40-feature extractor, statistics helpers). Experiments are
being layered on top; see the report for the current results and the open questions.
