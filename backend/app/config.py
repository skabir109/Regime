from pathlib import Path
import os
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR.parent / ".env")

DATA_PATH = BASE_DIR / "data" / "prices_daily.csv"
MODEL_DIR = BASE_DIR / "model"
MODEL_PATH = MODEL_DIR / "regime_xgb.joblib"
META_PATH = MODEL_DIR / "model_meta.json"
STATIC_DIR = BASE_DIR / "app" / "static"
PROMPTS_DIR = BASE_DIR / "app" / "prompts"
REGIME_ANALYST_PROMPT_PATH = Path(
    os.getenv("REGIME_ANALYST_PROMPT_PATH", str(PROMPTS_DIR / "regime_analyst.txt"))
)
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
SUPABASE_URL = os.getenv("SUPABASE_URL", os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")).rstrip("/")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", ""))

LLM_API_KEY = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", "")).strip()
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
LLM_CHAT_COMPLETIONS_URL = os.getenv("LLM_CHAT_COMPLETIONS_URL", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4.1-mini")
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
AI_ANALYZE_CACHE_TTL_SECONDS = int(os.getenv("AI_ANALYZE_CACHE_TTL_SECONDS", "180"))
AI_ANALYZE_CACHE_MAX_ENTRIES = int(os.getenv("AI_ANALYZE_CACHE_MAX_ENTRIES", "512"))
