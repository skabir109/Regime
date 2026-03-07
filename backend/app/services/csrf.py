import hashlib
import hmac
import secrets
from urllib.parse import urlparse

from app.config import CORS_ORIGINS, CSRF_SECRET


def _csrf_secret() -> str:
    # Fall back to a deterministic but app-local secret only when env secret is not provided.
    return CSRF_SECRET or "regime-dev-csrf-secret"


def generate_csrf_token() -> str:
    raw = secrets.token_urlsafe(32)
    signature = hmac.new(_csrf_secret().encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{raw}.{signature}"


def validate_csrf_token(token: str | None) -> bool:
    if not token or "." not in token:
        return False
    raw, signature = token.rsplit(".", 1)
    if not raw or not signature:
        return False
    expected = hmac.new(_csrf_secret().encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)


def allowed_origin_set() -> set[str]:
    allowed: set[str] = set()
    for origin in CORS_ORIGINS:
        parsed = urlparse(origin)
        if parsed.scheme and parsed.netloc:
            allowed.add(f"{parsed.scheme}://{parsed.netloc}".lower())
    return allowed


def extract_origin_from_referer(referer: str | None) -> str | None:
    if not referer:
        return None
    parsed = urlparse(referer)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}".lower()
