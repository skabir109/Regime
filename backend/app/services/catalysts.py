from datetime import datetime

from app.services.news import build_watchlist_news, fetch_market_news
from app.services.watchlist import load_watchlist


def _market_session_windows(now: datetime) -> list[dict]:
    session_date = now.strftime("%Y-%m-%d")
    return [
        {
            "title": "Opening Drive Check",
            "category": "Market Structure",
            "timing": f"{session_date} 09:30 ET",
            "detail": "Reassess breadth, volatility, and watchlist leadership during the opening rotation.",
            "symbols": [],
        },
        {
            "title": "Midday Regime Recheck",
            "category": "Market Structure",
            "timing": f"{session_date} 12:00 ET",
            "detail": "Check whether the opening move held or faded before adding intraday risk.",
            "symbols": [],
        },
        {
            "title": "Closing Risk Review",
            "category": "Market Structure",
            "timing": f"{session_date} 15:30 ET",
            "detail": "Review whether leaders held into the close and whether risk should be carried overnight.",
            "symbols": [],
        },
    ]


def build_catalyst_calendar(state: dict, user_id: int, limit: int = 6) -> list[dict]:
    now = datetime.now()
    news = fetch_market_news(limit=12)
    watchlist = load_watchlist(user_id)
    watchlist_news = build_watchlist_news(news, watchlist, limit=6)
    events = []

    if state["volatility_state"] == "Elevated volatility":
        events.append(
            {
                "title": "Volatility Control Window",
                "category": "Risk",
                "timing": "Current session",
                "detail": "Volatility is elevated. Confirm position sizing and avoid assuming smooth continuation.",
                "symbols": ["VIX"],
            }
        )

    if state["conflicting_signals"]:
        events.append(
            {
                "title": "Conflict Review",
                "category": "Regime",
                "timing": "Before new positions",
                "detail": state["conflicting_signals"][0],
                "symbols": [],
            }
        )

    for article in watchlist_news:
        if "Earnings" in article["tags"]:
            events.append(
                {
                    "title": f'Earnings Catalyst: {", ".join(article["matched_symbols"])}',
                    "category": "Earnings",
                    "timing": "Headline-driven",
                    "detail": article["title"],
                    "symbols": article["matched_symbols"],
                }
            )
        else:
            events.append(
                {
                    "title": f'Watchlist Catalyst: {", ".join(article["matched_symbols"])}',
                    "category": "Watchlist",
                    "timing": "Current session",
                    "detail": article["title"],
                    "symbols": article["matched_symbols"],
                }
            )
        if len(events) >= limit:
            break

    if len(events) < limit:
        for article in news:
            if "Rates" in article.get("tags", []):
                events.append(
                    {
                        "title": "Rates Headline Monitor",
                        "category": "Macro",
                        "timing": "Current session",
                        "detail": article["title"],
                        "symbols": [],
                    }
                )
                break

    for window in _market_session_windows(now):
        if len(events) >= limit:
            break
        events.append(window)

    return events[:limit]
