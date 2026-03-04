from __future__ import annotations

import csv
import io
from datetime import date, timedelta
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlmodel import Session
from app.config import ALPHA_VANTAGE_API_KEY, CALENDAR_PROVIDER
from app.services.db import get_engine
from app.schemas import User
from app.services.catalysts import build_catalyst_calendar
from app.services.subscriptions import get_tier_config
from app.services.watchlist import load_watchlist


def _fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "RegimeTerminal/0.2"})
    with urlopen(request, timeout=5) as response:
        return response.read().decode("utf-8", errors="replace")


def _alpha_vantage_earnings(symbols: list[str], limit: int) -> list[dict]:
    if not ALPHA_VANTAGE_API_KEY:
        return []

    events = []
    today = date.today()
    seen = set()
    for symbol in symbols[:5]:
        params = urlencode(
            {
                "function": "EARNINGS_CALENDAR",
                "symbol": symbol,
                "horizon": "3month",
                "apikey": ALPHA_VANTAGE_API_KEY,
            }
        )
        try:
            payload = _fetch_text(f"https://www.alphavantage.co/query?{params}")
        except (TimeoutError, URLError, ValueError):
            continue

        reader = csv.DictReader(io.StringIO(payload))
        for row in reader:
            report_date = row.get("reportDate") or row.get("report_date") or ""
            if not report_date:
                continue
            key = (symbol, report_date)
            if key in seen:
                continue
            seen.add(key)
            events.append(
                {
                    "title": f"{symbol} earnings",
                    "category": "Earnings",
                    "timing": report_date,
                    "detail": f'Expected report for {row.get("name") or symbol}.',
                    "symbols": [symbol],
                    "source": "Alpha Vantage",
                    "verified": True,
                }
            )
            if len(events) >= limit:
                return events
    return events


def fetch_verified_calendar(symbols: list[str], limit: int = 6) -> list[dict]:
    providers = [CALENDAR_PROVIDER] if CALENDAR_PROVIDER != "auto" else ["alphavantage"]
    for provider in providers:
        if provider == "alphavantage":
            events = _alpha_vantage_earnings(symbols, limit)
        else:
            events = []
        if events:
            return events[:limit]
    return []


def build_trader_calendar(state: dict, user_id: int, limit: int = 8) -> list[dict]:
    watchlist = load_watchlist(user_id)
    symbols = [item["symbol"] for item in watchlist]
    
    with Session(get_engine()) as session:
        user = session.get(User, user_id)
        tier = get_tier_config(user.tier if user else None)

    verified = fetch_verified_calendar(symbols, limit=limit) if tier["verified_calendar"] else []
    session_events = build_catalyst_calendar(state, user_id, limit=limit)

    merged = list(verified)
    seen = {(item["title"], item["timing"]) for item in merged}
    for item in session_events:
        key = (item["title"], item["timing"])
        if key in seen:
            continue
        merged.append(item)
        seen.add(key)
        if len(merged) >= limit:
            break
    return merged[:limit]
