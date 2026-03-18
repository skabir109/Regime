import base64
import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, Request
import jwt
import requests
from sqlmodel import Session, select

from app.config import (
    CLERK_API_URL,
    CLERK_AUDIENCE,
    CLERK_ISSUER,
    CLERK_JWKS_URL,
    CLERK_SECRET_KEY,
    SESSION_COOKIE_NAME,
    SESSION_DURATION_HOURS,
)
from app.services.db import get_engine
from app.schemas import User, DBSession
from app.services.starter_pack import seed_starter_pack_for_user
from app.services.subscriptions import DEFAULT_TIER, normalize_tier


PBKDF2_ITERATIONS = 310000
_SCHEMA_READY = False
_CLERK_JWKS_CLIENT: jwt.PyJWKClient | None = None
_CLERK_JWKS_READY_AT = 0.0


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "tier": normalize_tier(user.tier),
        "created_at": user.created_at,
        "tier_selection_required": bool(getattr(user, "tier_selection_required", False)),
    }


def _ensure_schema_ready() -> None:
    global _SCHEMA_READY
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


def _hash_one_time_token(token: str) -> str:
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
    verification_token_hash = _hash_one_time_token(verification_token)

    with Session(get_engine()) as session:
        existing = session.exec(select(User).where(User.email == normalized_email)).first()
        if existing:
            raise ValueError("User already exists.")

        user = User(
            email=normalized_email,
            name=name.strip(),
            password_hash=hash_password(password),
            tier=DEFAULT_TIER,
            verification_token=None,
            verification_token_hash=verification_token_hash,
            verification_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
            created_at=datetime.now(timezone.utc),
            tier_selection_required=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        payload = _user_payload(user)

    seed_starter_pack_for_user(int(payload["id"]))
    return payload


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
        
        return _user_payload(user)


def _default_name_for_email(email: str) -> str:
    local_part = email.split("@", 1)[0].replace(".", " ").replace("_", " ").replace("-", " ").strip()
    if not local_part:
        return "Regime User"
    return " ".join(part.capitalize() for part in local_part.split())


def _full_name(first_name: str | None, last_name: str | None) -> str:
    parts = [part.strip() for part in [first_name or "", last_name or ""] if part and part.strip()]
    return " ".join(parts).strip()


def _get_clerk_jwks_client() -> jwt.PyJWKClient:
    global _CLERK_JWKS_CLIENT, _CLERK_JWKS_READY_AT
    if not CLERK_JWKS_URL:
        raise ValueError("Clerk is not configured (missing CLERK_JWKS_URL or CLERK_ISSUER).")
    now = time.time()
    if _CLERK_JWKS_CLIENT and now < _CLERK_JWKS_READY_AT:
        return _CLERK_JWKS_CLIENT
    _CLERK_JWKS_CLIENT = jwt.PyJWKClient(CLERK_JWKS_URL)
    _CLERK_JWKS_READY_AT = now + 300
    return _CLERK_JWKS_CLIENT


def _decode_clerk_session_token(session_token: str) -> dict:
    token = session_token.strip()
    if not token:
        raise ValueError("Clerk session token is required.")
    signing_key = _get_clerk_jwks_client().get_signing_key_from_jwt(token)
    decode_kwargs: dict = {
        "algorithms": ["RS256"],
        "options": {"verify_aud": bool(CLERK_AUDIENCE), "verify_iss": bool(CLERK_ISSUER)},
    }
    if CLERK_AUDIENCE:
        decode_kwargs["audience"] = CLERK_AUDIENCE
    if CLERK_ISSUER:
        decode_kwargs["issuer"] = CLERK_ISSUER
    return jwt.decode(token, signing_key.key, **decode_kwargs)


def _fetch_clerk_user(user_id: str) -> dict:
    if not CLERK_SECRET_KEY:
        return {}
    try:
        response = requests.get(
            f"{CLERK_API_URL}/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {CLERK_SECRET_KEY}"},
            timeout=3,
        )
    except requests.RequestException:
        return {}
    if response.status_code >= 400:
        return {}
    return response.json()


def _upsert_clerk_user(claims: dict) -> dict:
    _ensure_schema_ready()
    clerk_user_id = str(claims.get("sub") or "").strip()
    if not clerk_user_id:
        raise ValueError("Invalid Clerk token: missing subject.")

    email = (claims.get("email") or claims.get("email_address") or "").strip().lower()
    name = (claims.get("name") or "").strip()
    clerk_user: dict = {}

    # Avoid blocking every login on Clerk API latency; only fetch profile when required.
    if not email or not name:
        clerk_user = _fetch_clerk_user(clerk_user_id)

    if not email and clerk_user:
        addresses = clerk_user.get("email_addresses") or []
        if addresses:
            email = (addresses[0].get("email_address") or "").strip().lower()

    if not email:
        raise ValueError("Clerk session does not include an email address.")

    name = (
        name
        or (_full_name(clerk_user.get("first_name"), clerk_user.get("last_name")) if clerk_user else "")
        or _default_name_for_email(email)
    )

    with Session(get_engine()) as session:
        created_new = False
        user = session.exec(select(User).where(User.email == email)).first()
        if user:
            user.name = name
            user.is_verified = True
        else:
            created_new = True
            user = User(
                email=email,
                name=name,
                password_hash=hash_password(secrets.token_urlsafe(32)),
                tier=DEFAULT_TIER,
                created_at=datetime.now(timezone.utc),
                is_verified=True,
                verification_token=None,
                tier_selection_required=True,
            )
        session.add(user)
        session.commit()
        session.refresh(user)
        payload = _user_payload(user)

    if created_new:
        seed_starter_pack_for_user(int(payload["id"]))
    return payload


def authenticate_clerk_session_token(session_token: str) -> dict:
    claims = _decode_clerk_session_token(session_token)
    return _upsert_clerk_user(claims)


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
        payload = _user_payload(user)
        payload["is_verified"] = user.is_verified
        return payload

def verify_email(token: str) -> bool:
    _ensure_schema_ready()
    token_hash = _hash_one_time_token(token.strip())
    with Session(get_engine()) as session:
        user = session.exec(select(User).where(User.verification_token_hash == token_hash)).first()
        if not user:
            # Legacy fallback for pre-hash token rows.
            user = session.exec(select(User).where(User.verification_token == token)).first()
        if not user:
            raise ValueError("Invalid or expired verification token.")

        expires_at = user.verification_token_expires_at
        if expires_at:
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at <= datetime.now(timezone.utc):
                raise ValueError("Invalid or expired verification token.")

        user.is_verified = True
        user.verification_token = None
        user.verification_token_hash = None
        user.verification_token_expires_at = None
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
        user.reset_token = None
        user.reset_token_hash = _hash_one_time_token(reset_token)
        user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        session.add(user)
        session.commit()
        return reset_token

def reset_password(token: str, new_password: str) -> bool:
    _ensure_schema_ready()
    if len(new_password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    
    token_hash = _hash_one_time_token(token.strip())
    with Session(get_engine()) as session:
        user = session.exec(select(User).where(User.reset_token_hash == token_hash)).first()
        if not user:
            # Legacy fallback for pre-hash token rows.
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
        user.reset_token_hash = None
        user.reset_token_expires_at = None
        session.add(user)
        active_sessions = session.exec(select(DBSession).where(DBSession.user_id == user.id)).all()
        for db_session in active_sessions:
            session.delete(db_session)
        session.commit()
        return True


def update_user_tier(user_id: int, tier: str, *, allow_upgrade: bool = False) -> dict:
    _ensure_schema_ready()
    normalized = normalize_tier(tier)
    with Session(get_engine()) as session:
        user = session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")
        current = normalize_tier(user.tier)
        if normalized != current and normalized != DEFAULT_TIER and not allow_upgrade:
            raise ValueError("Tier upgrades require billing confirmation.")
        user.tier = normalized
        session.add(user)
        session.commit()
        session.refresh(user)
        return _user_payload(user)


def mark_tier_selection_complete(user_id: int) -> dict:
    _ensure_schema_ready()
    with Session(get_engine()) as session:
        user = session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")
        user.tier_selection_required = False
        session.add(user)
        session.commit()
        session.refresh(user)
        return _user_payload(user)


def current_user_or_401(request: Request) -> dict:
    user = get_user_from_session(request.cookies.get(SESSION_COOKIE_NAME))
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user
