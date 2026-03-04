from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "prices_daily.csv"
MODEL_DIR = BASE_DIR / "model"
MODEL_PATH = MODEL_DIR / "regime_xgb.joblib"
META_PATH = MODEL_DIR / "model_meta.json"
STATIC_DIR = BASE_DIR / "app" / "static"

APP_TITLE = "Regime API"
APP_VERSION = "0.2.0"
APP_DESCRIPTION = (
    "Baseline market regime detection API for the DigitalOcean AI Hackathon."
)
