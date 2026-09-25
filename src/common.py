"""Shared paths, logging and label mappings for the ODRES synthetic pipeline."""
import logging
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
REF = ROOT / "data" / "reference"
CLEAN = ROOT / "data" / "clean"
PROCESSED = ROOT / "data" / "processed"
SAMPLES = ROOT / "data" / "samples"
DB = ROOT / "database" / "odres_marketing_analytics_demo.sqlite"
SQL = ROOT / "sql"
DOCS = ROOT / "docs"
POWERBI_DATA = ROOT / "powerbi" / "data"

DISCLOSURE = ("Professional context based on a real ODRES Group experience. "
              "Public technical reconstruction using synthetic data.")

REPORT_START, REPORT_END = "2025-11-01", "2026-06-30"

# Label variants seen in the source exports -> reference value
REGION_SYNONYMS = {
    "bruxelles": "Brussels", "brussel": "Brussels", "anvers": "Antwerp", "antwerpen": "Antwerp",
    "liege": "Liège", "luik": "Liège", "oost-vlaanderen": "East Flanders",
    "flandre orientale": "East Flanders", "vlaams-brabant": "Flemish Brabant",
    "brabant wallon": "Walloon Brabant", "henegouwen": "Hainaut", "namen": "Namur",
}
COMPANY_SIZES = ["1-9", "10-49", "50+"]
STAGES = ["Won", "Lost", "Open"]


def get_logger(name: str) -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
                        datefmt="%H:%M:%S")
    return logging.getLogger(name)


def norm(text) -> str:
    """Lower-case, trimmed, single-spaced label used for matching."""
    return " ".join(str(text).strip().lower().split())
