from app.services.alerts import build_alerts
from app.services.briefing_history import save_briefing_history
from app.services.calendar import build_trader_calendar
from app.services.news import fetch_market_news
from app.services.state import build_market_state_summary
from app.services.watchlist import load_watchlist
from app.services.watchlist_intelligence import build_watchlist_intelligence


def build_premarket_briefing(
    model,
    meta: dict,
    user_id: int,
    state: dict | None = None,
    alerts: list[dict] | None = None,
    headlines: list[dict] | None = None,
    watchlist: list[dict] | None = None,
    watchlist_insights: list[dict] | None = None,
    catalyst_calendar: list[dict] | None = None,
) -> dict:
    state = state if state is not None else build_market_state_summary(model, meta)
    alerts = alerts if alerts is not None else build_alerts(model, meta, user_id)
    headlines = headlines if headlines is not None else fetch_market_news(limit=5)
    watchlist = watchlist if watchlist is not None else load_watchlist(user_id)
    watchlist_insights = watchlist_insights if watchlist_insights is not None else build_watchlist_intelligence(user_id, state=state)
    catalyst_calendar = catalyst_calendar if catalyst_calendar is not None else build_trader_calendar(state, user_id, limit=5)

    focus_items = []
    if watchlist_insights:
        focus_items.extend(
            [
                f'{item["symbol"]}: {item["stance"]} - {item["summary"]}'
                for item in watchlist_insights[:3]
            ]
        )
    elif watchlist:
        focus_items.append("Watchlist names are saved, but no active intelligence was generated yet.")
    else:
        focus_items.append("No watchlist names saved yet. Add symbols to personalize the briefing.")

    checklist = [
        f'Start with the regime: {state["regime"]}. {state["summary"]}',
        f'Check breadth and confirmation: {state["breadth"]}, {state["cross_asset_confirmation"]}.',
        "Review sector breadth before focusing on single-name trades.",
        "Review the catalyst tape for headlines that support or conflict with the current setup.",
    ]

    if alerts:
        checklist.append(f'Highest-priority alert: {alerts[0]["title"]}.')

    risks = list(state["warnings"][:3])
    if headlines:
        risks.append(f'Lead catalyst: {headlines[0]["title"]}')

    briefing = {
        "headline": f'{state["regime"]} pre-market briefing',
        "overview": state["summary"],
        "checklist": checklist[:5],
        "focus_items": focus_items[:5],
        "risks": risks[:5],
        "catalyst_calendar": [f'{item["timing"]}: {item["title"]} - {item["detail"]}' for item in catalyst_calendar[:5]],
    }
    save_briefing_history(user_id, briefing)
    return briefing
