from __future__ import annotations

from pathlib import Path
import os
import sys
from urllib.parse import quote_plus

BASE_DIR = Path(__file__).resolve().parent.parent
DB_HOST = os.getenv("LIBRARY_DB_HOST", "localhost")
DB_PORT = int(os.getenv("LIBRARY_DB_PORT", "5432"))
DB_NAME = os.getenv("LIBRARY_DB_NAME", "library_system")
DB_USER = os.getenv("LIBRARY_DB_USER", "library_app")
DB_PASSWORD = os.getenv("LIBRARY_DB_PASSWORD", "library_app_123")
TEST_DB_NAME = os.getenv("LIBRARY_TEST_DB_NAME", "library_system_test")


def build_postgres_url(*, database: str = DB_NAME, user: str = DB_USER, password: str = DB_PASSWORD, host: str = DB_HOST, port: int = DB_PORT) -> str:
    return f"postgresql+psycopg://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{database}"


DATABASE_URL = os.getenv("LIBRARY_DATABASE_URL", build_postgres_url())
SECRET_KEY = os.getenv("LIBRARY_SECRET_KEY", "dev-secret-key-please-change-this-32b")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("LIBRARY_ACCESS_TOKEN_EXPIRE_MINUTES", "720"))
BORROW_DAYS = int(os.getenv("LIBRARY_BORROW_DAYS", "14"))
RENEW_DAYS = int(os.getenv("LIBRARY_RENEW_DAYS", "14"))
MAX_RENEWALS = int(os.getenv("LIBRARY_MAX_RENEWALS", "1"))
MAX_ACTIVE_LOANS = int(os.getenv("LIBRARY_MAX_ACTIVE_LOANS", "5"))
PICKUP_HOURS = int(os.getenv("LIBRARY_PICKUP_HOURS", "48"))
FINE_PER_DAY = float(os.getenv("LIBRARY_FINE_PER_DAY", "1"))
MAX_FINE = float(os.getenv("LIBRARY_MAX_FINE", "50"))
LOST_FINE_AMOUNT = float(os.getenv("LIBRARY_LOST_FINE_AMOUNT", str(MAX_FINE)))
DAMAGED_FINE_AMOUNT = float(os.getenv("LIBRARY_DAMAGED_FINE_AMOUNT", str(round(MAX_FINE * 0.4, 2))))
GRACE_PERIOD_DAYS = int(os.getenv("LIBRARY_GRACE_PERIOD_DAYS", "0"))
ENABLE_SCHEDULER = os.getenv("LIBRARY_ENABLE_SCHEDULER", "1") == "1"
IS_PYTEST_RUNTIME = "pytest" in Path(sys.argv[0]).name.lower() or any("pytest" in arg.lower() for arg in sys.argv)
ENABLE_SAMPLE_CATALOG = os.getenv("LIBRARY_ENABLE_SAMPLE_CATALOG", "0" if IS_PYTEST_RUNTIME else "1") == "1"
SAMPLE_CATALOG_TARGET = int(os.getenv("LIBRARY_SAMPLE_CATALOG_TARGET", "1000"))
