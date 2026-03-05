import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.error import URLError
from urllib.request import Request, urlopen

from sqlmodel import Session
from app.services.audit import log_audit_event
from app.services.preferences import get_delivery_preferences
from app.services.db import get_engine
from app.schemas import User
from app.services.subscriptions import get_tier_config
from app.services.world_affairs import build_world_affairs_briefing
from app.config import (
    APP_TITLE,
    # Add these to config later if needed, for now use env placeholders
)
import os

def _send_http_post(url: str, payload: dict, channel_name: str, user_id: int) -> str:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "RegimeTerminal/0.2"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=5) as response:
            status = f"sent:{response.status}"
            log_audit_event(f"delivery_{channel_name}_sent", user_id, {"status": response.status})
            return status
    except (TimeoutError, URLError, ValueError) as exc:
        log_audit_event(f"delivery_{channel_name}_failed", user_id, {"error": str(exc)})
        return f"failed:{exc.__class__.__name__}"

def _send_slack_notification(webhook_url: str, message: str, user_id: int) -> str:
    payload = {"text": message}
    return _send_http_post(webhook_url, payload, "slack", user_id)

def _send_discord_notification(webhook_url: str, message: str, user_id: int) -> str:
    payload = {"content": message}
    return _send_http_post(webhook_url, payload, "discord", user_id)

def _send_email_notification(to_email: str, subject: str, body: str, user_id: int) -> str:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    from_email = os.getenv("SMTP_FROM", f"alerts@regime.app")

    if not all([smtp_host, smtp_user, smtp_pass]):
        log_audit_event("delivery_email_skipped", user_id, {"reason": "SMTP not configured"})
        return "skipped:config_missing"

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        log_audit_event("delivery_email_sent", user_id, {"to": to_email})
        return "sent:200"
    except Exception as exc:
        log_audit_event("delivery_email_failed", user_id, {"error": str(exc)})
        return f"failed:{exc.__class__.__name__}"

def _build_delivery_payload(user_id: int) -> dict:
    briefing = build_world_affairs_briefing(limit=6)
    preferences = get_delivery_preferences(user_id)
    return {
        "headline": briefing["headline"],
        "summary": briefing["summary"],
        "key_themes": briefing["key_themes"],
        "market_implications": briefing["market_implications"],
        "watchpoints": briefing["watchpoints"],
        "cadence": preferences["cadence"],
    }

def send_global_macro_briefing(user_id: int) -> dict:
    preferences = get_delivery_preferences(user_id)
    payload = _build_delivery_payload(user_id)
    channels = []
    
    with Session(get_engine()) as session:
        user = session.get(User, user_id)
        tier = get_tier_config(user.tier if user else None)

    message_text = f"🚨 {payload['headline']}\n\n{payload['summary']}\n\nKey Themes:\n" + "\n".join([f"- {t}" for h, t in zip(range(3), payload['key_themes'])])
    email_body = f"{message_text}\n\nView full report at: https://regime.app/terminal"

    email_status = "disabled"
    if preferences["email_enabled"] and tier.get("email_delivery", False):
        email_status = _send_email_notification(user.email, f"Market Brief: {payload['headline']}", email_body, user_id)
        if "sent" in email_status:
            channels.append("email")
    elif preferences["email_enabled"] and not tier.get("email_delivery", False):
        email_status = "restricted"

    webhook_status = "disabled"
    webhook_url = preferences.get("webhook_url", "").strip()
    if preferences["webhook_enabled"] and webhook_url:
        webhook_status = _send_http_post(webhook_url, payload, "generic_webhook", user_id)
        if "sent" in webhook_status:
            channels.append("webhook")

    slack_status = "disabled"
    slack_url = preferences.get("slack_webhook_url", "").strip()
    if preferences["slack_enabled"] and slack_url:
        slack_status = _send_slack_notification(slack_url, message_text, user_id)
        if "sent" in slack_status:
            channels.append("slack")

    discord_status = "disabled"
    discord_url = preferences.get("discord_webhook_url", "").strip()
    if preferences["discord_enabled"] and discord_url:
        discord_status = _send_discord_notification(discord_url, message_text, user_id)
        if "sent" in discord_status:
            channels.append("discord")

    return {
        "headline": payload["headline"],
        "cadence": payload["cadence"],
        "email_status": email_status,
        "webhook_status": webhook_status,
        "slack_status": slack_status,
        "discord_status": discord_status,
        "delivery_channels": channels,
    }
