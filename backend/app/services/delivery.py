import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from sqlmodel import Session
from app.services.audit import log_audit_event
from app.services.preferences import get_delivery_preferences
from app.services.db import get_engine
from app.schemas import User
from app.services.subscriptions import get_tier_config
from app.services.world_affairs import build_world_affairs_briefing


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

    email_status = "disabled"
    if preferences["email_enabled"] and tier.get("email_delivery", False):
        email_status = "queued"
        channels.append("email")
        log_audit_event("global_macro_email_queued", user_id, payload)
    elif preferences["email_enabled"] and not tier.get("email_delivery", False):
        email_status = "restricted"

    webhook_status = "disabled"
    webhook_url = preferences.get("webhook_url", "").strip()
    if preferences["webhook_enabled"] and webhook_url:
        request = Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "RegimeTerminal/0.2"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=4) as response:
                webhook_status = f"sent:{response.status}"
                channels.append("webhook")
                log_audit_event("global_macro_webhook_sent", user_id, {"status": response.status, **payload})
        except (TimeoutError, URLError, ValueError) as exc:
            webhook_status = f"failed:{exc.__class__.__name__}"
            log_audit_event("global_macro_webhook_failed", user_id, {"error": str(exc), **payload})

    return {
        "headline": payload["headline"],
        "cadence": payload["cadence"],
        "email_status": email_status,
        "webhook_status": webhook_status,
        "delivery_channels": channels,
    }
