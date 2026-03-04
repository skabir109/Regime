from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "prices_daily.csv"
MODEL_DIR = BASE_DIR / "model"
MODEL_PATH = MODEL_DIR / "regime_xgb.joblib"
META_PATH = MODEL_DIR / "model_meta.json"
STATIC_DIR = BASE_DIR / "app" / "static"
WATCHLIST_STORE_PATH = BASE_DIR / "data" / "watchlist.json"
DB_PATH = BASE_DIR / "data" / "regime.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
DIRECT_URL = os.getenv("DIRECT_URL", DATABASE_URL)
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", FRONTEND_ORIGIN).split(",") if origin.strip()]

APP_TITLE = "Regime API"
APP_VERSION = "0.2.0"
APP_DESCRIPTION = (
    "Market intelligence backend for Regime."
)

SESSION_COOKIE_NAME = "regime_session"
SESSION_DURATION_HOURS = 24 * 7
SESSION_SECURE = os.getenv("REGIME_SESSION_SECURE", "false").lower() == "true"
SESSION_SAMESITE = os.getenv("REGIME_SESSION_SAMESITE", "lax")

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
CALENDAR_PROVIDER = os.getenv("REGIME_CALENDAR_PROVIDER", "auto").lower()
