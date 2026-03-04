import json
from datetime import datetime, timezone

from app.services.db import get_connection
from app.services.subscriptions import get_tier_config


def save_briefing_history(user_id: int, briefing: dict) -> None:
    briefing_date = datetime.now(timezone.utc).date().isoformat()
    payload = json.dumps(briefing)
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO briefing_history (user_id, briefing_date, headline, overview, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, briefing_date) DO UPDATE SET
                headline = excluded.headline,
                overview = excluded.overview,
                payload_json = excluded.payload_json,
                created_at = excluded.created_at
            """,
            (
                user_id,
                briefing_date,
                briefing["headline"],
                briefing["overview"],
                payload,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        user = connection.execute("SELECT tier FROM users WHERE id = ?", (user_id,)).fetchone()
        tier = get_tier_config(user["tier"] if user else None)
        connection.execute(
            """
            DELETE FROM briefing_history
            WHERE user_id = ?
              AND id NOT IN (
                SELECT id
                FROM briefing_history
                WHERE user_id = ?
                ORDER BY briefing_date DESC
                LIMIT ?
              )
            """,
            (user_id, user_id, tier["briefing_history_limit"]),
        )


def load_briefing_history(user_id: int, limit: int = 10) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT briefing_date, headline, overview
            FROM briefing_history
            WHERE user_id = ?
            ORDER BY briefing_date DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]
