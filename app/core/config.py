# app/core/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]  # carpeta raíz del proyecto
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # requerido para /ask
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

SERVICE_NAME = "amazon-scraper"
VERSION = "1.0.0"

RAW_FILE = DATA_DIR / "scrapped_info.json"
DATA_FILE = DATA_DIR / "data.json"

# Placeholder para DB a futuro
DATABASE_URL = os.getenv("DATABASE_URL")  # e.g. "postgresql+psycopg://..."
