from datetime import datetime, timezone
from sqlmodel import Session, select
from app.services.db import get_engine
from app.schemas import WatchlistItemDB, User
from app.services.subscriptions import get_tier_config


def _normalize_added_at(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        raw = value.strip()
        if raw.endswith("+00"):
            raw = f"{raw}:00"
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            return raw
    return value


def load_watchlist(user_id: int) -> list[dict]:
    with Session(get_engine()) as session:
        items = session.exec(
            select(WatchlistItemDB).where(WatchlistItemDB.user_id == user_id).order_by(WatchlistItemDB.added_at.desc())
        ).all()
        return [
            {"symbol": item.symbol, "label": item.label, "added_at": _normalize_added_at(item.added_at)}
            for item in items
        ]


def add_watchlist_item(user_id: int, symbol: str, label: str | None = None) -> list[dict]:
    normalized = symbol.strip().upper()
    if not normalized:
        raise ValueError("Symbol is required.")

    with Session(get_engine()) as session:
        user = session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")
            
        tier = get_tier_config(user.tier)
        count = session.exec(
            select(WatchlistItemDB).where(WatchlistItemDB.user_id == user_id)
        ).all()
        
        if len(count) >= tier["watchlist_limit"]:
            raise ValueError(f"Watchlist limit reached for {tier['label']} tier ({tier['watchlist_limit']} names).")

        existing = session.exec(
            select(WatchlistItemDB).where(
                WatchlistItemDB.user_id == user_id, 
                WatchlistItemDB.symbol == normalized
            )
        ).first()
        
        if not existing:
            item = WatchlistItemDB(
                user_id=user_id,
                symbol=normalized,
                label=(label or normalized).strip(),
                added_at=datetime.now(timezone.utc)
            )
            session.add(item)
            session.commit()
            
    return load_watchlist(user_id)


def remove_watchlist_item(user_id: int, symbol: str) -> list[dict]:
    normalized = symbol.strip().upper()
    with Session(get_engine()) as session:
        item = session.exec(
            select(WatchlistItemDB).where(
                WatchlistItemDB.user_id == user_id, 
                WatchlistItemDB.symbol == normalized
            )
        ).first()
        if item:
            session.delete(item)
            session.commit()
            
    return load_watchlist(user_id)
