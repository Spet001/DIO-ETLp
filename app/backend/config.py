import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_PATH = DATA_DIR / "raw_city_innovations.csv"
ENRICHED_DATA_PATH = DATA_DIR / "enriched_city_innovations.json"
FRONTEND_DIR = BASE_DIR / "frontend"

load_dotenv(BASE_DIR / ".env")


class Settings:
    """Centralized configuration for the service."""

    huggingface_model: str = os.getenv("HUGGINGFACE_MODEL", "facebook/bart-large-cnn")
    huggingface_api_token: Optional[str] = os.getenv("HUGGINGFACE_API_TOKEN")
    api_timeout: float = float(os.getenv("API_TIMEOUT", "60"))
    max_summary_tokens: int = int(os.getenv("MAX_SUMMARY_TOKENS", "60"))
    min_summary_tokens: int = int(os.getenv("MIN_SUMMARY_TOKENS", "20"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
