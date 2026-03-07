from pathlib import Path
import os
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR.parent / ".env")

DATA_PATH = BASE_DIR / "data" / "prices_daily.csv"
MODEL_DIR = BASE_DIR / "model"
MODEL_PATH = MODEL_DIR / "regime_xgb.joblib"
META_PATH = MODEL_DIR / "model_meta.json"
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
SESSION_SECURE = os.getenv("REGIME_SESSION_SECURE", "true").lower() == "true"
SESSION_SAMESITE = os.getenv("REGIME_SESSION_SAMESITE", "strict")
CSRF_COOKIE_NAME = os.getenv("REGIME_CSRF_COOKIE_NAME", "regime_csrf")
CSRF_HEADER_NAME = os.getenv("REGIME_CSRF_HEADER_NAME", "x-csrf-token")
CSRF_SECRET = os.getenv("REGIME_CSRF_SECRET", "").strip()
REDIS_URL = os.getenv("REDIS_URL", "").strip()
REDIS_KEY_PREFIX = os.getenv("REDIS_KEY_PREFIX", "regime")

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
CALENDAR_PROVIDER = os.getenv("REGIME_CALENDAR_PROVIDER", "auto").lower()

SUPABASE_URL = os.getenv("SUPABASE_URL", os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")).rstrip("/")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", ""))

# Clerk auth migration settings.
CLERK_ISSUER = os.getenv("CLERK_ISSUER", "").strip().rstrip("/")
CLERK_AUDIENCE = os.getenv("CLERK_AUDIENCE", "").strip()
CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL", f"{CLERK_ISSUER}/.well-known/jwks.json" if CLERK_ISSUER else "").strip()
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "").strip()
CLERK_API_URL = os.getenv("CLERK_API_URL", "https://api.clerk.com").strip().rstrip("/")

LLM_API_KEY = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", "")).strip()
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instruct")
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
AI_ANALYZE_CACHE_TTL_SECONDS = int(os.getenv("AI_ANALYZE_CACHE_TTL_SECONDS", "180"))
AI_ANALYZE_CACHE_MAX_ENTRIES = int(os.getenv("AI_ANALYZE_CACHE_MAX_ENTRIES", "512"))
AI_ANALYZE_CACHE_PATH = Path(
    os.getenv("AI_ANALYZE_CACHE_PATH", str(BASE_DIR / "data" / "ai_analyze_cache.json"))
)

# Billing/paywall controls. Keep REGIME_BILLING_TOKEN server-side only.
REGIME_BILLING_TOKEN = os.getenv("REGIME_BILLING_TOKEN", "").strip()

# Stripe billing integration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "").strip()
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
STRIPE_PRICE_ID_PRO = os.getenv("STRIPE_PRICE_ID_PRO", "").strip()
STRIPE_PRICE_ID_DESK = os.getenv("STRIPE_PRICE_ID_DESK", "").strip()
STRIPE_SUCCESS_URL = os.getenv("STRIPE_SUCCESS_URL", f"{FRONTEND_ORIGIN}/app?billing=success").strip()
STRIPE_CANCEL_URL = os.getenv("STRIPE_CANCEL_URL", f"{FRONTEND_ORIGIN}/app?billing=cancel").strip()

# Sensitive field encryption (Fernet key, base64 urlsafe 32-byte key).
REGIME_FIELD_ENCRYPTION_KEY = os.getenv("REGIME_FIELD_ENCRYPTION_KEY", "").strip()
