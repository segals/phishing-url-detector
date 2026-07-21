"""Central knobs so every experiment is reproducible."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROC = ROOT / "data" / "processed"
TABLES = ROOT / "results" / "tables"
FIGURES = ROOT / "results" / "figures"

SEED = 42
SPLIT = (0.6, 0.2, 0.2)          # train / val / test
BOOTSTRAP_N = 1000
# Cost model: a missed phishing URL (false negative) is worse than a false alarm.
COST_FP, COST_FN = 1.0, 5.0

for d in (DATA_PROC, TABLES, FIGURES):
    d.mkdir(parents=True, exist_ok=True)
