from app.services.calendar import build_trader_calendar
from app.services.news import build_watchlist_news, fetch_market_news
from app.services.state import build_market_state_summary
from app.services.watchlist import load_watchlist
from app.services.watchlist_intelligence import build_watchlist_intelligence
from app.services.world_affairs import build_narrative_timeline, build_watchlist_exposures, build_world_affairs_monitor


def build_watchlist_detail(user_id: int, symbol: str, model, meta: dict) -> dict:
    normalized = symbol.strip().upper()
    watchlist = load_watchlist(user_id)
    item = next((entry for entry in watchlist if entry["symbol"] == normalized), None)
    if not item:
        raise ValueError("Watchlist symbol not found.")

    state = build_market_state_summary(model, meta)
    insights = build_watchlist_intelligence(user_id, state=state)
    detail = next((entry for entry in insights if entry["symbol"] == normalized), None)
    news = build_watchlist_news(fetch_market_news(limit=12), [item], limit=6)
    calendar = [
        event
        for event in build_trader_calendar(state, user_id, limit=10)
        if not event.get("symbols") or normalized in event.get("symbols", [])
    ]
    exposures = build_watchlist_exposures(user_id)
    exposure = next((entry for entry in exposures if entry["symbol"] == normalized), None)
    world_events = [
        event
        for event in build_world_affairs_monitor(limit=8)
        if not exposure or any(theme in event["theme"] for theme in exposure["themes"]) or any(theme == event["theme"] for theme in exposure["themes"])
    ]
    timeline = [
        item
        for item in build_narrative_timeline(limit=8)
        if not exposure or item["theme"] in exposure["themes"]
    ]

    if detail:
        return {
            **detail,
            "exposures": exposure["themes"] if exposure else [],
            "regime_alignment": detail.get("regime_alignment", ""),
            "trade_implication": detail.get("trade_implication", ""),
            "catalyst_risk": detail.get("catalyst_risk", ""),
            "sector_readthrough": detail.get("sector_readthrough", ""),
            "related_news": news,
            "world_affairs": world_events[:4],
            "narrative_timeline": timeline[:4],
            "calendar_events": calendar[:6],
        }

    return {
        "symbol": item["symbol"],
        "label": item["label"],
        "stance": "Monitor",
        "summary": "This symbol is saved, but live intelligence is not available yet.",
        "score": None,
        "price": None,
        "change_1d": None,
        "change_20d": None,
        "reasons": [],
        "exposures": exposure["themes"] if exposure else [],
        "regime_alignment": "",
        "trade_implication": "",
        "catalyst_risk": "",
        "sector_readthrough": "",
        "related_news": news,
        "world_affairs": world_events[:4],
        "narrative_timeline": timeline[:4],
        "calendar_events": calendar[:6],
    }
