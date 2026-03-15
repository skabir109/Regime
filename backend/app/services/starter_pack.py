from sqlmodel import Session, select

from app.schemas import User, WatchlistItemDB
from app.services.db import get_engine
from app.services.subscriptions import get_tier_config
from app.services.watchlist import load_watchlist


STARTER_PACK_NAME = "Cross-Asset Starter Pack"
STARTER_PACK_ITEMS = [
    {
        "symbol": "SPY",
        "label": "S&P 500",
        "role": "Risk barometer",
        "rationale": "Anchors the broad US equity tape and the core regime signal.",
    },
    {
        "symbol": "QQQ",
        "label": "Nasdaq 100",
        "role": "Growth leadership",
        "rationale": "Shows whether higher-beta growth is confirming or diverging from the main index.",
    },
    {
        "symbol": "GLD",
        "label": "Gold",
        "role": "Defensive hedge",
        "rationale": "Useful for spotting flight-to-safety pressure and real-asset demand.",
    },
    {
        "symbol": "TLT",
        "label": "Treasury Bonds",
        "role": "Rates stress gauge",
        "rationale": "Helps frame duration demand and risk-off pressure across macro cycles.",
    },
    {
        "symbol": "XLE",
        "label": "Energy",
        "role": "Inflation pulse",
        "rationale": "Captures commodity and geopolitics-driven rotation that can pressure the regime.",
    },
]


def get_starter_pack() -> dict:
    return {
        "name": STARTER_PACK_NAME,
        "description": "A default cross-asset workspace for first-run onboarding and demo accounts.",
        "items": [dict(item) for item in STARTER_PACK_ITEMS],
    }


def apply_starter_pack(user_id: int, *, only_if_empty: bool = False) -> dict:
    with Session(get_engine()) as session:
        user = session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")

        existing_items = session.exec(
            select(WatchlistItemDB)
            .where(WatchlistItemDB.user_id == user_id)
            .order_by(WatchlistItemDB.added_at.desc())
        ).all()
        existing_symbols = {item.symbol for item in existing_items}

        if only_if_empty and existing_symbols:
            return {
                **get_starter_pack(),
                "applied_symbols": [],
                "already_seeded": True,
                "watchlist": load_watchlist(user_id),
            }

        tier = get_tier_config(user.tier)
        available_slots = max(int(tier["watchlist_limit"]) - len(existing_symbols), 0)
        to_add = [
            item for item in STARTER_PACK_ITEMS
            if item["symbol"] not in existing_symbols
        ][:available_slots]

        for item in to_add:
            session.add(
                WatchlistItemDB(
                    user_id=user_id,
                    symbol=item["symbol"],
                    label=item["label"],
                )
            )

        if to_add:
            session.commit()

    return {
        **get_starter_pack(),
        "applied_symbols": [item["symbol"] for item in to_add],
        "already_seeded": not bool(to_add),
        "watchlist": load_watchlist(user_id),
    }


def seed_starter_pack_for_user(user_id: int) -> None:
    apply_starter_pack(user_id, only_if_empty=True)
