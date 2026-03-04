from datetime import datetime, timezone

from app.services.db import get_connection
from app.services.subscriptions import get_tier_config


DEFAULT_PREFERENCES = {
    "email_enabled": False,
    "webhook_enabled": False,
    "webhook_url": "",
    "cadence": "premarket",
}


def get_delivery_preferences(user_id: int) -> dict:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT email_enabled, webhook_enabled, webhook_url, cadence
            FROM delivery_preferences
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
    if not row:
        return DEFAULT_PREFERENCES.copy()
    return {
        "email_enabled": bool(row["email_enabled"]),
        "webhook_enabled": bool(row["webhook_enabled"]),
        "webhook_url": row["webhook_url"] or "",
        "cadence": row["cadence"],
    }


def save_delivery_preferences(
    user_id: int,
    email_enabled: bool,
    webhook_enabled: bool,
    webhook_url: str | None,
    cadence: str,
) -> dict:
    if cadence not in {"premarket", "intraday", "eod"}:
        raise ValueError("Cadence must be one of: premarket, intraday, eod.")
    cleaned_url = (webhook_url or "").strip()
    with get_connection() as connection:
        user = connection.execute(
            "SELECT tier FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        tier = get_tier_config(user["tier"] if user else None)
        if webhook_enabled and not tier["webhook_delivery"]:
            raise ValueError(f'Webhook delivery requires the {get_tier_config("pro")["label"]} tier or higher.')
        connection.execute(
            """
            INSERT INTO delivery_preferences (user_id, email_enabled, webhook_enabled, webhook_url, cadence, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                email_enabled = excluded.email_enabled,
                webhook_enabled = excluded.webhook_enabled,
                webhook_url = excluded.webhook_url,
                cadence = excluded.cadence,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                int(email_enabled),
                int(webhook_enabled),
                cleaned_url,
                cadence,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
    return get_delivery_preferences(user_id)
