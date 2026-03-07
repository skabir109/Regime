#!/usr/bin/env python3
"""Security/deployment readiness preflight checks.

Run from project root:
  python3 backend/scripts/security_preflight.py
"""

from __future__ import annotations

import os
import sys


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _redis_ping(url: str) -> tuple[bool, str]:
    if not url:
        return False, "not-configured"
    try:
        from redis import Redis

        client = Redis.from_url(url, socket_timeout=1.5, socket_connect_timeout=1.5)
        return bool(client.ping()), "ok"
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    app_env = _env("APP_ENV", "development").lower()
    is_prod = app_env in {"production", "prod"}

    csrf_secret = _env("REGIME_CSRF_SECRET")
    session_secure = _env("REGIME_SESSION_SECURE", "true").lower() == "true"
    session_samesite = _env("REGIME_SESSION_SAMESITE", "strict").lower()
    redis_url = _env("REDIS_URL")

    redis_ok, redis_detail = _redis_ping(redis_url)

    failures: list[str] = []
    warnings: list[str] = []

    if not csrf_secret:
        msg = "REGIME_CSRF_SECRET is not set."
        (failures if is_prod else warnings).append(msg)

    if not session_secure:
        msg = "REGIME_SESSION_SECURE=false."
        (failures if is_prod else warnings).append(msg)

    if session_samesite != "strict":
        msg = f"REGIME_SESSION_SAMESITE is '{session_samesite}', expected 'strict'."
        (failures if is_prod else warnings).append(msg)

    if is_prod and not redis_ok:
        failures.append("Redis-backed burst limiting is not active or unreachable.")
    elif not redis_ok:
        warnings.append("Redis-backed burst limiting not active (memory fallback expected in non-prod).")

    print("Security Preflight")
    print(f"- APP_ENV: {app_env}")
    print(f"- Session secure default: {session_secure}")
    print(f"- Session SameSite: {session_samesite}")
    print(f"- CSRF secret configured: {bool(csrf_secret)}")
    print(f"- REDIS_URL configured: {bool(redis_url)}")
    print(f"- Redis connectivity: {redis_ok} ({redis_detail})")

    if warnings:
        print("\nWarnings:")
        for item in warnings:
            print(f"  - {item}")

    if failures:
        print("\nFailures:")
        for item in failures:
            print(f"  - {item}")
        return 2

    print("\nOK: security preflight passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
