import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_PATH = DATA_DIR / "raw" / "netflix_titles.csv"
PROCESSED_DATA_PATH = DATA_DIR / "processed" / "netflix_cleaned.csv"
DATABASE_PATH = DATA_DIR / "processed" / "netflix.sqlite"
REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
SQL_DIR = BASE_DIR / "sql"

# Netflix Brand Theme Colors for Visualizations
NETFLIX_RED = "#E50914"
NETFLIX_DARK_RED = "#B81D24"
NETFLIX_BLACK = "#141414"
NETFLIX_DARK_GRAY = "#221F1F"
NETFLIX_LIGHT_GRAY = "#F5F5F1"
NETFLIX_ACCENT_BLUE = "#0071EB"
NETFLIX_ACCENT_GOLD = "#F5A623"

PALETTE_PRIMARY = [NETFLIX_RED, "#221F1F", "#E5E5E5", "#831010", "#0071EB", "#FFA000", "#4CAF50", "#9C27B0"]

# Ensure standard directories exist
for folder in [DATA_DIR / "raw", DATA_DIR / "processed", REPORTS_DIR, FIGURES_DIR, SQL_DIR]:
    folder.mkdir(parents=True, exist_ok=True)
