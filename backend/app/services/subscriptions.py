TIERS = {
    "free": {
        "label": "Free",
        "description": "Starter market terminal with core monitoring and light personalization.",
        "watchlist_limit": 5,
        "email_delivery": False,
        "verified_calendar": False,
        "webhook_delivery": False,
        "briefing_history_limit": 7,
        "ai_daily_limit": 0,
        "ai_minute_limit": 0,
    },
    "pro": {
        "label": "Pro",
        "description": "Expanded trader workflow with larger watchlists and verified event coverage.",
        "watchlist_limit": 25,
        "email_delivery": True,
        "verified_calendar": True,
        "webhook_delivery": True,
        "briefing_history_limit": 30,
        "ai_daily_limit": 120,
        "ai_minute_limit": 10,
    },
    "desk": {
        "label": "Desk",
        "description": "Team-oriented tier for heavier monitoring and shared desk-style usage.",
        "watchlist_limit": 100,
        "email_delivery": True,
        "verified_calendar": True,
        "webhook_delivery": True,
        "briefing_history_limit": 90,
        "ai_daily_limit": 400,
        "ai_minute_limit": 25,
    },
}

DEFAULT_TIER = "free"


def normalize_tier(tier: str | None) -> str:
    if not tier:
        return DEFAULT_TIER
    normalized = tier.strip().lower()
    return normalized if normalized in TIERS else DEFAULT_TIER


def get_tier_config(tier: str | None) -> dict:
    normalized = normalize_tier(tier)
    return {"tier": normalized, **TIERS[normalized]}


def list_tiers() -> list[dict]:
    return [get_tier_config(name) for name in TIERS]
