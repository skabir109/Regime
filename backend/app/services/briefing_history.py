import json
from datetime import datetime, timezone
from sqlmodel import Session, select
from app.services.db import get_engine
from app.schemas import BriefingHistoryDB, User
from app.services.subscriptions import get_tier_config


def save_briefing_history(user_id: int, briefing: dict) -> None:
    briefing_date = datetime.now(timezone.utc).date().isoformat()
    payload = json.dumps(briefing)
    
    with Session(get_engine()) as session:
        user = session.get(User, user_id)
        if not user:
            return
            
        tier = get_tier_config(user.tier)
        
        # Upsert
        existing = session.exec(
            select(BriefingHistoryDB).where(
                BriefingHistoryDB.user_id == user_id,
                BriefingHistoryDB.briefing_date == briefing_date
            )
        ).first()
        
        if existing:
            existing.headline = briefing["headline"]
            existing.overview = briefing["overview"]
            existing.payload_json = payload
            session.add(existing)
        else:
            new_history = BriefingHistoryDB(
                user_id=user_id,
                briefing_date=briefing_date,
                headline=briefing["headline"],
                overview=briefing["overview"],
                payload_json=payload,
                created_at=datetime.now(timezone.utc)
            )
            session.add(new_history)
        
        session.commit()

        # Enforce history limit
        all_history = session.exec(
            select(BriefingHistoryDB).where(BriefingHistoryDB.user_id == user_id).order_by(BriefingHistoryDB.briefing_date.desc())
        ).all()
        
        if len(all_history) > tier["briefing_history_limit"]:
            to_delete = all_history[tier["briefing_history_limit"]:]
            for item in to_delete:
                session.delete(item)
            session.commit()


def load_briefing_history(user_id: int, limit: int = 10) -> list[dict]:
    with Session(get_engine()) as session:
        rows = session.exec(
            select(BriefingHistoryDB).where(BriefingHistoryDB.user_id == user_id)
            .order_by(BriefingHistoryDB.briefing_date.desc())
            .limit(limit)
        ).all()
        
        return [
            {
                "briefing_date": row.briefing_date,
                "headline": row.headline,
                "overview": row.overview,
            }
            for row in rows
        ]
