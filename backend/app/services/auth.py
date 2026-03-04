import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request

from app.config import SESSION_COOKIE_NAME, SESSION_DURATION_HOURS
from app.services.db import get_connection
from app.services.subscriptions import DEFAULT_TIER, normalize_tier


PBKDF2_ITERATIONS = 310000


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"{PBKDF2_ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(derived).decode()}"


def verify_password(password: str, stored_hash: str) -> bool:
    iterations_raw, salt_raw, digest_raw = stored_hash.split("$")
    salt = base64.b64decode(salt_raw.encode())
    expected = base64.b64decode(digest_raw.encode())
    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        int(iterations_raw),
    )
    return hmac.compare_digest(candidate, expected)


def _hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def register_user(email: str, password: str, name: str) -> dict:
    normalized_email = email.strip().lower()
    if not normalized_email or "@" not in normalized_email:
        raise ValueError("Valid email is required.")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    if not name.strip():
        raise ValueError("Name is required.")

    verification_token = secrets.token_urlsafe(32)

    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            (normalized_email,),
        ).fetchone()
        if existing:
            raise ValueError("User already exists.")

        created_at = datetime.now(timezone.utc).isoformat()
        connection.execute(
            "INSERT INTO users (email, name, password_hash, tier, created_at, verification_token) VALUES (?, ?, ?, ?, ?, ?)",
            (normalized_email, name.strip(), hash_password(password), DEFAULT_TIER, created_at, verification_token),
        )
        user = connection.execute(
            "SELECT id, email, name, tier, created_at, is_verified FROM users WHERE email = ?",
            (normalized_email,),
        ).fetchone()
        
        # Here we would send the email with the verification_token
        # send_verification_email(normalized_email, verification_token)
        
        return dict(user)


def authenticate_user(email: str, password: str) -> dict:
    normalized_email = email.strip().lower()
    with get_connection() as connection:
        user = connection.execute(
            "SELECT id, email, name, password_hash, tier, created_at FROM users WHERE email = ?",
            (normalized_email,),
        ).fetchone()
    if not user or not verify_password(password, user["password_hash"]):
        raise ValueError("Invalid credentials.")
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "tier": normalize_tier(user["tier"]),
        "created_at": user["created_at"],
    }


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = _hash_session_token(token)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=SESSION_DURATION_HOURS)
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO sessions (user_id, token_hash, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (user_id, token_hash, expires_at.isoformat(), now.isoformat()),
        )
    return token


def delete_session(token: str | None):
    if not token:
        return
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM sessions WHERE token_hash = ?",
            (_hash_session_token(token),),
        )


def get_user_from_session(token: str | None) -> dict | None:
    if not token:
        return None
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT users.id, users.email, users.name, users.created_at, sessions.expires_at
                 , users.tier, users.is_verified
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ?
            """,
            (_hash_session_token(token),),
        ).fetchone()
        if not row:
            return None
        expires_at = datetime.fromisoformat(row["expires_at"])
        if expires_at <= datetime.now(timezone.utc):
            connection.execute(
                "DELETE FROM sessions WHERE token_hash = ?",
                (_hash_session_token(token),),
            )
            return None
        return {
            "id": row["id"],
            "email": row["email"],
            "name": row["name"],
            "tier": normalize_tier(row["tier"]),
            "created_at": row["created_at"],
            "is_verified": bool(row["is_verified"]),
        }

def verify_email(token: str) -> bool:
    with get_connection() as connection:
        user = connection.execute("SELECT id FROM users WHERE verification_token = ?", (token,)).fetchone()
        if not user:
            raise ValueError("Invalid or expired verification token.")
        connection.execute(
            "UPDATE users SET is_verified = 1, verification_token = NULL WHERE id = ?",
            (user["id"],)
        )
        return True

def generate_password_reset_token(email: str) -> str:
    normalized_email = email.strip().lower()
    with get_connection() as connection:
        user = connection.execute("SELECT id FROM users WHERE email = ?", (normalized_email,)).fetchone()
        if not user:
            return "" # Silently fail to avoid email enumeration
        
        reset_token = secrets.token_urlsafe(32)
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        connection.execute(
            "UPDATE users SET reset_token = ?, reset_token_expires_at = ? WHERE id = ?",
            (reset_token, expires_at, user["id"])
        )
        # Here we would send the email with the reset_token
        # send_password_reset_email(normalized_email, reset_token)
        return reset_token

def reset_password(token: str, new_password: str) -> bool:
    if len(new_password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    
    with get_connection() as connection:
        user = connection.execute("SELECT id, reset_token_expires_at FROM users WHERE reset_token = ?", (token,)).fetchone()
        if not user:
            raise ValueError("Invalid reset token.")
            
        expires_at = datetime.fromisoformat(user["reset_token_expires_at"])
        if expires_at <= datetime.now(timezone.utc):
            raise ValueError("Reset token has expired.")
            
        connection.execute(
            "UPDATE users SET password_hash = ?, reset_token = NULL, reset_token_expires_at = NULL WHERE id = ?",
            (hash_password(new_password), user["id"])
        )
        return True


def update_user_tier(user_id: int, tier: str) -> dict:
    normalized = normalize_tier(tier)
    with get_connection() as connection:
        connection.execute(
            "UPDATE users SET tier = ? WHERE id = ?",
            (normalized, user_id),
        )
        row = connection.execute(
            "SELECT id, email, name, tier, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return dict(row)


def current_user_or_401(request: Request) -> dict:
    user = get_user_from_session(request.cookies.get(SESSION_COOKIE_NAME))
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user
