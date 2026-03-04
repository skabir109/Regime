import json
from datetime import datetime, timezone

from app.services.db import get_connection


def log_audit_event(event_type: str, user_id: int | None, details: dict) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO audit_logs (event_type, user_id, details, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                event_type,
                user_id,
                json.dumps(details),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
