"""Fetch the primary dataset (PhiUSIIL, UCI id=967) to a local CSV.
Prasad, A. & Chandra, S. (2024), Computers & Security. UCI ML Repository.
"""
import os, hashlib, pandas as pd
from ucimlrepo import fetch_ucirepo

os.makedirs("data/raw", exist_ok=True)
ds = fetch_ucirepo(id=967)
df = ds.data.features.copy()
df["label_raw"] = ds.data.targets.values.ravel()   # PhiUSIIL: 1=legit, 0=phishing
df["label"] = 1 - df["label_raw"]                    # standardize: 1=phishing, 0=legit
df = df.drop(columns=["label_raw"])
out = "data/raw/phiusiil.csv"
df.to_csv(out, index=False)
h = hashlib.sha256(open(out,"rb").read()).hexdigest()
print(f"saved {out}: {df.shape[0]} rows x {df.shape[1]} cols")
print(f"phishing rate: {df.label.mean():.3f}  (1=phishing)")
print(f"sha256: {h[:16]}...")
print("columns:", list(df.columns)[:15], "...")
