import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, Request
import requests
from sqlmodel import Session, select

from app.config import SESSION_COOKIE_NAME, SESSION_DURATION_HOURS, SUPABASE_ANON_KEY, SUPABASE_URL
from app.services.db import get_engine, init_db
from app.schemas import User, DBSession
from app.services.subscriptions import DEFAULT_TIER, normalize_tier


PBKDF2_ITERATIONS = 310000
_SCHEMA_READY = False


def _ensure_schema_ready() -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return
    init_db()
    _SCHEMA_READY = True


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"{PBKDF2_ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(derived).decode()}"


def verify_password(password: str, stored_hash: str) -> bool:
    if not stored_hash or "$" not in stored_hash:
        return False
    parts = stored_hash.split("$")
    if len(parts) != 3:
        return False
    iterations_raw, salt_raw, digest_raw = parts
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
    _ensure_schema_ready()
    normalized_email = email.strip().lower()
    if not normalized_email or "@" not in normalized_email:
        raise ValueError("Valid email is required.")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    if not name.strip():
        raise ValueError("Name is required.")

    verification_token = secrets.token_urlsafe(32)

    with Session(get_engine()) as session:
        existing = session.exec(select(User).where(User.email == normalized_email)).first()
        if existing:
            raise ValueError("User already exists.")

        user = User(
            email=normalized_email,
            name=name.strip(),
            password_hash=hash_password(password),
            tier=DEFAULT_TIER,
            verification_token=verification_token,
            created_at=datetime.now(timezone.utc)
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.dict()


def authenticate_user(email: str, password: str) -> dict:
    _ensure_schema_ready()
    normalized_email = email.strip().lower()
    with Session(get_engine()) as session:
        user = session.exec(select(User).where(User.email == normalized_email)).first()
        if not user:
            raise ValueError("Invalid credentials.")
            
        # Check if locked
        if user.locked_until:
            locked_until = user.locked_until
            if isinstance(locked_until, str):
                locked_until = datetime.fromisoformat(locked_until.replace("Z", "+00:00"))
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)
                
            if locked_until > datetime.now(timezone.utc):
                diff = locked_until - datetime.now(timezone.utc)
                minutes = int(diff.total_seconds() / 60)
                raise ValueError(f"Account is locked. Try again in {max(1, minutes)} minutes.")

        if not verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
            session.add(user)
            session.commit()
            raise ValueError("Invalid credentials.")
            
        # Success
        user.failed_login_attempts = 0
        user.locked_until = None
        session.add(user)
        session.commit()
        
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "tier": normalize_tier(user.tier),
            "created_at": user.created_at,
        }


def _default_name_for_email(email: str) -> str:
    local_part = email.split("@", 1)[0].replace(".", " ").replace("_", " ").replace("-", " ").strip()
    if not local_part:
        return "Regime User"
    return " ".join(part.capitalize() for part in local_part.split())


def _upsert_supabase_user(profile: dict) -> dict:
    _ensure_schema_ready()
    email = (profile.get("email") or "").strip().lower()
    if not email:
        raise ValueError("Supabase user is missing an email address.")

    user_metadata = profile.get("user_metadata") or {}
    name = (
        user_metadata.get("name")
        or user_metadata.get("full_name")
        or profile.get("name")
        or _default_name_for_email(email)
    ).strip()
    created_at_str = profile.get("created_at")
    created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00")) if created_at_str else datetime.now(timezone.utc)

    with Session(get_engine()) as session:
        user = session.exec(select(User).where(User.email == email)).first()

        if user:
            user.name = name
            user.is_verified = True
        else:
            user = User(
                email=email,
                name=name,
                password_hash=hash_password(secrets.token_urlsafe(32)),
                tier=DEFAULT_TIER,
                created_at=created_at,
                is_verified=True,
                verification_token=None
            )
        
        session.add(user)
        session.commit()
        session.refresh(user)

        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "tier": normalize_tier(user.tier),
            "created_at": user.created_at,
            "is_verified": user.is_verified,
        }


def authenticate_supabase_access_token(access_token: str) -> dict:
    token = access_token.strip()
    if not token:
        raise ValueError("Supabase access token is required.")
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise ValueError("Supabase auth is not configured on the backend.")

    response = requests.get(
        f"{SUPABASE_URL}/auth/v1/user",
        headers={
            "Authorization": f"Bearer {token}",
            "apikey": SUPABASE_ANON_KEY,
        },
        timeout=10,
    )
    if response.status_code >= 400:
        raise ValueError("Supabase session could not be verified.")

    return _upsert_supabase_user(response.json())


def create_session(user_id: int) -> str:
    _ensure_schema_ready()
    token = secrets.token_urlsafe(32)
    token_hash = _hash_session_token(token)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=SESSION_DURATION_HOURS)
    
    with Session(get_engine()) as session:
        db_session = DBSession(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_at=now
        )
        session.add(db_session)
        session.commit()
    return token


def delete_session(token: str | None):
    _ensure_schema_ready()
    if not token:
        return
    token_hash = _hash_session_token(token)
    with Session(get_engine()) as session:
        db_session = session.exec(select(DBSession).where(DBSession.token_hash == token_hash)).first()
        if db_session:
            session.delete(db_session)
            session.commit()


def get_user_from_session(token: str | None) -> dict | None:
    _ensure_schema_ready()
    if not token:
        return None
    token_hash = _hash_session_token(token)
    with Session(get_engine()) as session:
        db_session = session.exec(select(DBSession).where(DBSession.token_hash == token_hash)).first()
        if not db_session:
            return None
        
        # Check if expired
        expires_at = db_session.expires_at
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
            
        if expires_at <= datetime.now(timezone.utc):
            session.delete(db_session)
            session.commit()
            return None
            
        user = db_session.user
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "tier": normalize_tier(user.tier),
            "created_at": user.created_at,
            "is_verified": user.is_verified,
        }

def verify_email(token: str) -> bool:
    _ensure_schema_ready()
    with Session(get_engine()) as session:
        user = session.exec(select(User).where(User.verification_token == token)).first()
        if not user:
            raise ValueError("Invalid or expired verification token.")
        user.is_verified = True
        user.verification_token = None
        session.add(user)
        session.commit()
        return True

def generate_password_reset_token(email: str) -> str:
    _ensure_schema_ready()
    normalized_email = email.strip().lower()
    with Session(get_engine()) as session:
        user = session.exec(select(User).where(User.email == normalized_email)).first()
        if not user:
            return "" 
        
        reset_token = secrets.token_urlsafe(32)
        user.reset_token = reset_token
        user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        session.add(user)
        session.commit()
        return reset_token

def reset_password(token: str, new_password: str) -> bool:
    _ensure_schema_ready()
    if len(new_password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    
    with Session(get_engine()) as session:
        user = session.exec(select(User).where(User.reset_token == token)).first()
        if not user:
            raise ValueError("Invalid reset token.")
            
        expires_at = user.reset_token_expires_at
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at <= datetime.now(timezone.utc):
            raise ValueError("Reset token has expired.")
            
        user.password_hash = hash_password(new_password)
        user.reset_token = None
        user.reset_token_expires_at = None
        session.add(user)
        session.commit()
        return True


def update_user_tier(user_id: int, tier: str) -> dict:
    _ensure_schema_ready()
    normalized = normalize_tier(tier)
    with Session(get_engine()) as session:
        user = session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")
        user.tier = normalized
        session.add(user)
        session.commit()
        session.refresh(user)
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "tier": normalize_tier(user.tier),
            "created_at": user.created_at,
        }


def current_user_or_401(request: Request) -> dict:
    user = get_user_from_session(request.cookies.get(SESSION_COOKIE_NAME))
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user
