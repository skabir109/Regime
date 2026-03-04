import json
from datetime import datetime, timezone
from sqlmodel import Session
from app.services.db import get_engine
from app.schemas import AuditLogDB


def log_audit_event(event_type: str, user_id: int | None, details: dict) -> None:
    with Session(get_engine()) as session:
        log = AuditLogDB(
            event_type=event_type,
            user_id=user_id,
            details=json.dumps(details),
            created_at=datetime.now(timezone.utc)
        )
        session.add(log)
        session.commit()
