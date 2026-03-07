from cryptography.fernet import Fernet, InvalidToken

from app.config import REGIME_FIELD_ENCRYPTION_KEY


def _get_fernet() -> Fernet:
    key = REGIME_FIELD_ENCRYPTION_KEY.strip()
    if not key:
        raise ValueError("REGIME_FIELD_ENCRYPTION_KEY is not configured.")
    try:
        return Fernet(key.encode("utf-8"))
    except Exception as exc:
        raise ValueError("REGIME_FIELD_ENCRYPTION_KEY is invalid.") from exc


def encrypt_secret(value: str | None) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    token = _get_fernet().encrypt(raw.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_secret(value: str | None) -> str:
    token = (value or "").strip()
    if not token:
        return ""
    try:
        decoded = _get_fernet().decrypt(token.encode("utf-8"))
        return decoded.decode("utf-8")
    except (InvalidToken, ValueError):
        return ""
