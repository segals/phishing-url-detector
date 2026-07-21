"""Load and prepare the URL data.

Primary corpus: PhiUSIIL (UCI id=967; Prasad & Chandra, 2024). We keep the raw `URL`
and `label` (standardized to 1 = phishing, 0 = legitimate) plus the dataset's own
features (used only to *reproduce and then critique* the near-perfect published result).
"""
from __future__ import annotations
import hashlib
import pandas as pd
from sklearn.model_selection import train_test_split
from . import config


def load_phiusiil() -> pd.DataFrame:
    """Read the fetched PhiUSIIL CSV (see scripts/fetch_data.py)."""
    path = config.DATA_RAW / "phiusiil.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} missing -- run  python scripts/fetch_data.py")
    return pd.read_csv(path)


def working_set(df: pd.DataFrame) -> pd.DataFrame:
    """Clean working set: valid URL + label, de-duplicated on the URL string.

    De-dup happens BEFORE any split so the same URL can't leak across train/test.
    """
    df = df.dropna(subset=["URL", "label"]).copy()
    df["URL"] = df["URL"].astype(str).str.strip()
    df = df[df["URL"].str.len() > 0]
    df = df.drop_duplicates(subset=["URL"]).reset_index(drop=True)
    df["id"] = range(len(df))
    return df


def split(df: pd.DataFrame, seed: int = config.SEED):
    """Stratified train/val/test (60/20/20 by default)."""
    tr_frac, va_frac, te_frac = config.SPLIT
    train, tmp = train_test_split(df, test_size=va_frac + te_frac,
                                  stratify=df["label"], random_state=seed)
    val, test = train_test_split(tmp, test_size=te_frac / (va_frac + te_frac),
                                 stratify=tmp["label"], random_state=seed)
    return (train.reset_index(drop=True), val.reset_index(drop=True),
            test.reset_index(drop=True))


def sha256_of(df: pd.DataFrame) -> str:
    return hashlib.sha256(
        pd.util.hash_pandas_object(df, index=True).values.tobytes()
    ).hexdigest()
