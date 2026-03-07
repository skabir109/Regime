from datetime import datetime, timezone
from urllib.parse import urlparse
from sqlmodel import Session, select
from app.services.db import get_engine
from app.schemas import DeliveryPreferencesDB, User
from app.services.subscriptions import get_tier_config
from app.services.secrets import decrypt_secret, encrypt_secret


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
        webhook_url = decrypt_secret(getattr(prefs, "webhook_url_enc", None)) or (prefs.webhook_url or "")
        slack_url = decrypt_secret(getattr(prefs, "slack_webhook_url_enc", None)) or (prefs.slack_webhook_url or "")
        discord_url = decrypt_secret(getattr(prefs, "discord_webhook_url_enc", None)) or (prefs.discord_webhook_url or "")
        return {
            "email_enabled": prefs.email_enabled,
            "webhook_enabled": prefs.webhook_enabled,
            "webhook_url": webhook_url,
            "slack_enabled": prefs.slack_enabled,
            "slack_webhook_url": slack_url,
            "discord_enabled": prefs.discord_enabled,
            "discord_webhook_url": discord_url,
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

    if cleaned_slack_url:
        parsed = urlparse(cleaned_slack_url)
        if parsed.netloc not in {"hooks.slack.com"}:
            raise ValueError("Slack webhook URL must use hooks.slack.com.")
    if cleaned_discord_url:
        parsed = urlparse(cleaned_discord_url)
        if parsed.netloc not in {"discord.com", "discordapp.com"}:
            raise ValueError("Discord webhook URL must use discord.com.")

    enc_webhook = encrypt_secret(cleaned_url)
    enc_slack = encrypt_secret(cleaned_slack_url)
    enc_discord = encrypt_secret(cleaned_discord_url)

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
            prefs.webhook_url = None
            prefs.webhook_url_enc = enc_webhook or None
            prefs.slack_enabled = slack_enabled
            prefs.slack_webhook_url = None
            prefs.slack_webhook_url_enc = enc_slack or None
            prefs.discord_enabled = discord_enabled
            prefs.discord_webhook_url = None
            prefs.discord_webhook_url_enc = enc_discord or None
            prefs.cadence = cadence
            prefs.timezone = cleaned_timezone
            prefs.updated_at = datetime.now(timezone.utc)
            session.add(prefs)
        else:
            prefs = DeliveryPreferencesDB(
                user_id=user_id,
                email_enabled=email_enabled,
                webhook_enabled=webhook_enabled,
                webhook_url=None,
                webhook_url_enc=enc_webhook or None,
                slack_enabled=slack_enabled,
                slack_webhook_url=None,
                slack_webhook_url_enc=enc_slack or None,
                discord_enabled=discord_enabled,
                discord_webhook_url=None,
                discord_webhook_url_enc=enc_discord or None,
                cadence=cadence,
                timezone=cleaned_timezone,
                updated_at=datetime.now(timezone.utc)
            )
            session.add(prefs)
            
        session.commit()
        return get_delivery_preferences(user_id)
