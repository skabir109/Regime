from datetime import datetime, timezone
from sqlmodel import Session, select
from app.services.db import get_engine
from app.schemas import DeliveryPreferencesDB, User
from app.services.subscriptions import get_tier_config


DEFAULT_PREFERENCES = {
    "email_enabled": False,
    "webhook_enabled": False,
    "webhook_url": "",
    "cadence": "premarket",
    "timezone": "local",
}


def get_delivery_preferences(user_id: int) -> dict:
    with Session(get_engine()) as session:
        prefs = session.get(DeliveryPreferencesDB, user_id)
        if not prefs:
            return DEFAULT_PREFERENCES
        return {
            "email_enabled": prefs.email_enabled,
            "webhook_enabled": prefs.webhook_enabled,
            "webhook_url": prefs.webhook_url or "",
            "cadence": prefs.cadence,
            "timezone": prefs.timezone or "local",
        }


def save_delivery_preferences(
    user_id: int,
    email_enabled: bool,
    webhook_enabled: bool,
    webhook_url: str | None,
    cadence: str,
    timezone_name: str | None,
) -> dict:
    cleaned_url = (webhook_url or "").strip()
    cleaned_timezone = (timezone_name or "local").strip() or "local"
    with Session(get_engine()) as session:
        user = session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")
            
        tier = get_tier_config(user.tier)

        if webhook_enabled and not tier["webhook_delivery"]:
            raise ValueError(f"Webhook delivery requires the {tier['label']} tier.")

        prefs = session.get(DeliveryPreferencesDB, user_id)
        if prefs:
            prefs.email_enabled = email_enabled
            prefs.webhook_enabled = webhook_enabled
            prefs.webhook_url = cleaned_url
            prefs.cadence = cadence
            prefs.timezone = cleaned_timezone
            prefs.updated_at = datetime.now(timezone.utc)
            session.add(prefs)
        else:
            prefs = DeliveryPreferencesDB(
                user_id=user_id,
                email_enabled=email_enabled,
                webhook_enabled=webhook_enabled,
                webhook_url=cleaned_url,
                cadence=cadence,
                timezone=cleaned_timezone,
                updated_at=datetime.now(timezone.utc)
            )
            session.add(prefs)
            
        session.commit()
        return get_delivery_preferences(user_id)
