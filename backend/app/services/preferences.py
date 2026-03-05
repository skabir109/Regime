from datetime import datetime, timezone
from sqlmodel import Session, select
from app.services.db import get_engine
from app.schemas import DeliveryPreferencesDB, User
from app.services.subscriptions import get_tier_config


DEFAULT_PREFERENCES = {
    "email_enabled": False,
    "webhook_enabled": False,
    "webhook_url": "",
    "slack_enabled": False,
    "slack_webhook_url": "",
    "discord_enabled": False,
    "discord_webhook_url": "",
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
            "slack_enabled": prefs.slack_enabled,
            "slack_webhook_url": prefs.slack_webhook_url or "",
            "discord_enabled": prefs.discord_enabled,
            "discord_webhook_url": prefs.discord_webhook_url or "",
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
    slack_enabled: bool = False,
    slack_webhook_url: str | None = None,
    discord_enabled: bool = False,
    discord_webhook_url: str | None = None,
) -> dict:
    cleaned_url = (webhook_url or "").strip()
    cleaned_slack_url = (slack_webhook_url or "").strip()
    cleaned_discord_url = (discord_webhook_url or "").strip()
    cleaned_timezone = (timezone_name or "local").strip() or "local"
    with Session(get_engine()) as session:
        user = session.get(User, user_id)
        if not user:
            raise ValueError("User not found.")
            
        tier = get_tier_config(user.tier)

        if (webhook_enabled or slack_enabled or discord_enabled) and not tier["webhook_delivery"]:
            raise ValueError(f"External delivery features require the {tier['label']} tier.")

        prefs = session.get(DeliveryPreferencesDB, user_id)
        if prefs:
            prefs.email_enabled = email_enabled
            prefs.webhook_enabled = webhook_enabled
            prefs.webhook_url = cleaned_url
            prefs.slack_enabled = slack_enabled
            prefs.slack_webhook_url = cleaned_slack_url
            prefs.discord_enabled = discord_enabled
            prefs.discord_webhook_url = cleaned_discord_url
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
                slack_enabled=slack_enabled,
                slack_webhook_url=cleaned_slack_url,
                discord_enabled=discord_enabled,
                discord_webhook_url=cleaned_discord_url,
                cadence=cadence,
                timezone=cleaned_timezone,
                updated_at=datetime.now(timezone.utc)
            )
            session.add(prefs)
            
        session.commit()
        return get_delivery_preferences(user_id)
