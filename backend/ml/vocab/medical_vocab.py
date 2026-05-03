from pathlib import Path
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "datasets"

def load_set(filename):
    path = DATA_DIR / filename
    with open(path) as f:
        return {line.strip().lower() for line in f if line.strip()}

DRUGS = load_set("drugs_clean.csv")
DIAGNOSES = load_set("diagnoses_clean.csv")
SYMPTOMS = load_set("symptoms_clean.csv")