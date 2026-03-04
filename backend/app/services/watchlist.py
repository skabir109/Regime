from datetime import datetime, timezone

from app.services.db import get_connection
from app.services.subscriptions import get_tier_config


def load_watchlist(user_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT symbol, label, added_at
            FROM watchlist_items
            WHERE user_id = ?
            ORDER BY added_at DESC
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def add_watchlist_item(user_id: int, symbol: str, label: str | None = None) -> list[dict]:
    normalized = symbol.strip().upper()
    if not normalized:
        raise ValueError("Symbol is required.")
    display_label = label.strip() if label else normalized

    with get_connection() as connection:
        user = connection.execute(
            "SELECT tier FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        tier = get_tier_config(user["tier"] if user else None)
        current_count = connection.execute(
            "SELECT COUNT(*) AS count FROM watchlist_items WHERE user_id = ?",
            (user_id,),
        ).fetchone()["count"]
        exists = connection.execute(
            "SELECT 1 FROM watchlist_items WHERE user_id = ? AND symbol = ?",
            (user_id, normalized),
        ).fetchone()
        if not exists and current_count >= tier["watchlist_limit"]:
            raise ValueError(
                f'{tier["label"]} tier supports up to {tier["watchlist_limit"]} watchlist symbols.'
            )
        connection.execute(
            """
            INSERT OR IGNORE INTO watchlist_items (user_id, symbol, label, added_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, normalized, display_label, datetime.now(timezone.utc).isoformat()),
        )
    return load_watchlist(user_id)


def remove_watchlist_item(user_id: int, symbol: str) -> list[dict]:
    normalized = symbol.strip().upper()
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM watchlist_items WHERE user_id = ? AND symbol = ?",
            (user_id, normalized),
        )
    return load_watchlist(user_id)
