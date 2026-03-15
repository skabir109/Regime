from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import text

from app.config import APP_ENV, CORS_ORIGINS, DATA_PATH, SESSION_SAMESITE, SESSION_SECURE
from app.services.api_protection import rate_limit_backend_status
from app.services.db import get_engine
from app.services.features import build_feature_frame


def _iso_or_empty(value: object) -> str:
    if isinstance(value, datetime):
        target = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return target.isoformat()
    if isinstance(value, pd.Timestamp):
        target = value.to_pydatetime()
        if target.tzinfo is None:
            target = target.replace(tzinfo=timezone.utc)
        return target.isoformat()
    return str(value or "")


def _load_model_artifacts():
    from app.services.model import load_artifacts

    return load_artifacts()


def build_system_status() -> dict:
    model, meta = _load_model_artifacts()

    db_ok = False
    db_error = ""
    try:
        engine = get_engine(use_direct=True)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:  # pragma: no cover
        db_error = str(exc)

    data_file_exists = DATA_PATH.exists()
    data_file_updated_at = ""
    latest_market_data_at = ""
    latest_feature_data_at = ""
    data_rows = 0
    if data_file_exists:
        data_file_updated_at = datetime.fromtimestamp(DATA_PATH.stat().st_mtime, tz=timezone.utc).isoformat()
        try:
            prices = pd.read_csv(DATA_PATH, index_col=0, parse_dates=True).sort_index().ffill()
            data_rows = int(len(prices.index))
            if not prices.empty:
                latest_market_data_at = _iso_or_empty(prices.index[-1])
                features = build_feature_frame(prices)
                if not features.empty:
                    latest_feature_data_at = _iso_or_empty(features.index[-1])
        except Exception:
            pass

    training = meta.get("training", {}) if isinstance(meta, dict) else {}
    metrics = training.get("metrics", {}) if isinstance(training, dict) else {}

    warnings: list[str] = []
    if not db_ok:
        warnings.append("Database connectivity check failed.")
    if not SESSION_SECURE:
        warnings.append("Secure session cookies are disabled.")
    if str(SESSION_SAMESITE).lower() != "strict":
        warnings.append("Session cookie SameSite is not strict.")
    if not data_file_exists:
        warnings.append("Local fallback market data file is missing.")

    return {
        "app_env": APP_ENV,
        "database": {
            "connected": db_ok,
            "error": db_error,
        },
        "security": {
            "session_secure": SESSION_SECURE,
            "session_samesite": SESSION_SAMESITE,
            "cors_origins": CORS_ORIGINS,
            "rate_limit_backend": rate_limit_backend_status(),
        },
        "data": {
            "file_exists": data_file_exists,
            "file_updated_at": data_file_updated_at,
            "latest_market_data_at": latest_market_data_at,
            "latest_feature_data_at": latest_feature_data_at,
            "rows": data_rows,
        },
        "model": {
            "loaded": bool(model),
            "classes": meta.get("classes", []),
            "feature_count": len(meta.get("features", [])),
            "training_window": training.get("date_range", {}),
            "metrics": metrics,
        },
        "warnings": warnings,
    }
