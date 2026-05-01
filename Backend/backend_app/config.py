from __future__ import annotations

import os
from pathlib import Path
from zoneinfo import ZoneInfo


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent
DEFAULT_DB_PATH = PROJECT_DIR / "compute_rental.db"

API_PREFIX = "/api"
APP_TITLE = "Compute Rental Backend"
APP_VERSION = "1.0.0"

TIMEZONE = ZoneInfo("Asia/Shanghai")
FIXED_CONNECTION = {"ip": "192.168.0.100", "password": "123456"}


def resolve_app_env() -> str:
    return (os.getenv("APP_ENV") or "local").strip().lower()


def resolve_database_url() -> str | None:
    return os.getenv("DATABASE_URL") or None


def resolve_db_path() -> Path:
    raw = os.getenv("COMPUTE_RENTAL_DB_PATH")
    return Path(raw) if raw else DEFAULT_DB_PATH


def resolve_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOWED_ORIGINS", "")
    defaults = []
    if resolve_app_env() != "production":
        defaults = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    extras = [item.strip() for item in raw.split(",") if item.strip()]
    return list(dict.fromkeys(defaults + extras))
