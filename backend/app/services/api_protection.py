from collections import defaultdict, deque
from datetime import datetime, timezone
from threading import Lock
import secrets
import time

from sqlmodel import Session, select
try:
    from redis import Redis
    from redis.exceptions import RedisError
except Exception:  # pragma: no cover - fallback when redis package is unavailable
    Redis = None  # type: ignore[assignment]

    class RedisError(Exception):
        pass

from app.config import REDIS_KEY_PREFIX, REDIS_URL
from app.schemas import APIUsageCounterDB
from app.services.db import get_engine


_BURST_LOCK = Lock()
_BURST_WINDOWS: dict[str, deque[float]] = defaultdict(deque)
_REDIS_LOCK = Lock()
_REDIS_CLIENT: Redis | None = None

_BURST_LUA = """
local key = KEYS[1]
local now_ms = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])
local member = ARGV[3]
local window_start = now_ms - 60000

redis.call("ZREMRANGEBYSCORE", key, 0, window_start)
local current = redis.call("ZCARD", key)
if current >= limit then
  return {0, current}
end
redis.call("ZADD", key, now_ms, member)
redis.call("EXPIRE", key, 120)
return {1, current + 1}
"""


class APILimitError(ValueError):
    pass


def _utc_day_bucket() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _redis_client() -> Redis | None:
    global _REDIS_CLIENT
    if Redis is None:
        return None
    if not REDIS_URL:
        return None
    if _REDIS_CLIENT is not None:
        return _REDIS_CLIENT
    with _REDIS_LOCK:
        if _REDIS_CLIENT is None:
            _REDIS_CLIENT = Redis.from_url(REDIS_URL, socket_timeout=1.5, socket_connect_timeout=1.5)
    return _REDIS_CLIENT


def rate_limit_backend_status() -> dict[str, object]:
    configured = bool(REDIS_URL)
    client = _redis_client()
    redis_ok = False
    mode = "memory"
    if client is not None:
        try:
            redis_ok = bool(client.ping())
            mode = "redis" if redis_ok else "memory"
        except RedisError:
            redis_ok = False
            mode = "memory"
    return {
        "configured": configured,
        "mode": mode,
        "redis_ok": redis_ok,
        "key_prefix": REDIS_KEY_PREFIX,
    }


def _enforce_burst_limit_redis(user_id: int, endpoint: str, limit_per_minute: int) -> bool:
    client = _redis_client()
    if client is None:
        return False

    now_ms = int(time.time() * 1000)
    member = f"{now_ms}:{secrets.token_hex(4)}"
    key = f"{REDIS_KEY_PREFIX}:rate:{endpoint}:{user_id}"
    try:
        allowed, _count = client.eval(_BURST_LUA, 1, key, now_ms, limit_per_minute, member)
        if int(allowed) != 1:
            raise APILimitError("Per-minute API limit reached. Please wait and retry.")
        return True
    except RedisError:
        # Fail open to local in-memory limiter if Redis is unavailable.
        return False


def enforce_burst_limit(user_id: int, endpoint: str, limit_per_minute: int) -> None:
    if limit_per_minute <= 0:
        raise APILimitError("This endpoint is not available for your plan.")

    if _enforce_burst_limit_redis(user_id, endpoint, limit_per_minute):
        return

    now_ts = datetime.now(timezone.utc).timestamp()
    key = f"{user_id}:{endpoint}"

    with _BURST_LOCK:
        window = _BURST_WINDOWS[key]
        while window and now_ts - window[0] > 60:
            window.popleft()
        if len(window) >= limit_per_minute:
            raise APILimitError("Per-minute API limit reached. Please wait and retry.")
        window.append(now_ts)


def enforce_daily_limit(user_id: int, endpoint: str, limit_per_day: int) -> dict[str, int]:
    if limit_per_day <= 0:
        raise APILimitError("This endpoint is not available for your plan.")

    bucket = _utc_day_bucket()
    now_utc = datetime.now(timezone.utc)
    with Session(get_engine()) as session:
        counter = session.exec(
            select(APIUsageCounterDB).where(
                APIUsageCounterDB.user_id == user_id,
                APIUsageCounterDB.endpoint == endpoint,
                APIUsageCounterDB.bucket == bucket,
            )
        ).first()

        if not counter:
            counter = APIUsageCounterDB(
                user_id=user_id,
                endpoint=endpoint,
                bucket=bucket,
                count=0,
                updated_at=now_utc,
            )

        if counter.count >= limit_per_day:
            raise APILimitError("Daily API quota reached for this endpoint.")

        counter.count += 1
        counter.updated_at = now_utc
        session.add(counter)
        session.commit()

        remaining = max(0, limit_per_day - counter.count)
        return {
            "limit": limit_per_day,
            "used": counter.count,
            "remaining": remaining,
        }
