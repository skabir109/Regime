from app.services.inference import predict_latest
from app.services.news import fetch_market_news
from app.services.watchlist import load_watchlist
from app.services.world_affairs import build_world_affairs_monitor


def build_alert_context(
    alert: dict,
    prediction,
    market_state,
    watchlist: list[dict],
    news: list[dict],
) -> dict:
    return {
        "alert": {
            "title": alert.get("title"),
            "severity": alert.get("severity"),
            "message": alert.get("message"),
            "symbol": alert.get("symbol"),
            "details": alert.get("details", []),
        },
        "prediction": {
            "regime": getattr(prediction, "regime", None),
            "confidence": getattr(prediction, "confidence", None),
            "probabilities": getattr(prediction, "probabilities", {}),
        },
        "market_state": {
            "regime": getattr(market_state, "regime", None),
            "breadth": getattr(market_state, "breadth", None),
            "volatility_state": getattr(market_state, "volatility_state", None),
            "trend_strength": getattr(market_state, "trend_strength", None),
            "cross_asset_confirmation": getattr(market_state, "cross_asset_confirmation", None),
            "supporting_signals": getattr(market_state, "supporting_signals", []),
            "conflicting_signals": getattr(market_state, "conflicting_signals", []),
        },
        "watchlist": [item.get("symbol", "").upper() for item in watchlist if item.get("symbol")],
        "headlines": [
            {
                "title": item.get("title"),
                "source": item.get("source"),
                "tags": item.get("tags", []),
            }
            for item in (news or [])[:5]
        ],
    }


def build_alerts_for_watchlist(model, meta: dict, watchlist: list[dict]) -> list[dict]:
    alerts = []
    prediction = predict_latest(model, meta)
    watch_symbols = {item["symbol"] for item in watchlist if item.get("symbol")}
    news = fetch_market_news(limit=4)
    world_events = build_world_affairs_monitor(limit=3)

    if prediction.regime == "HighVol":
        alerts.append(
            {
                "title": "Volatility Regime Active",
                "severity": "high",
                "message": "The model is flagging unstable market conditions. Risk should be sized more carefully.",
                "symbol": "VIX",
                "details": [
                    f"Model confidence: {prediction.confidence * 100:.1f}%",
                    "Volatility is high enough to distort standard trend signals.",
                    "Expect wider ranges and faster rotations.",
                ],
            }
        )
    elif prediction.regime == "RiskOff":
        alerts.append(
            {
                "title": "Defensive Regime",
                "severity": "medium",
                "message": "Top-down market conditions are risk-off. Treat long signals more selectively.",
                "symbol": None,
                "details": [
                    f"Model confidence: {prediction.confidence * 100:.1f}%",
                    "Defensive assets are leading while cyclicals are lagging.",
                    "Consider reducing exposure or tightening stop-losses.",
                ],
            }
        )

    if watch_symbols and prediction.regime in {"RiskOff", "HighVol"}:
        focus_symbol = sorted(watch_symbols)[0]
        alerts.append(
            {
                "title": f"{focus_symbol} Risk Context",
                "severity": "medium",
                "message": "Top-down regime is defensive. Treat single-name momentum with tighter risk controls.",
                "symbol": focus_symbol,
                "details": [
                    f"Current regime: {prediction.regime}",
                    "Confirm setup quality with broader market participation before sizing up.",
                ],
            }
        )

    if news:
        alerts.append(
            {
                "title": "Headline Catalyst Check",
                "severity": "low",
                "message": news[0]["title"],
                "symbol": None,
                "details": [
                    f"Source: {news[0]['source']}",
                    f"Tags: {', '.join(news[0]['tags'])}",
                ],
            }
        )

    if world_events:
        lead_event = world_events[0]
        alerts.append(
            {
                "title": f'{lead_event["theme"]} Monitor',
                "severity": "high" if lead_event["severity"] == "high" else "medium",
                "message": f'{lead_event["why_it_matters"]} Watch: {", ".join(lead_event["affected_assets"][:3])}.',
                "symbol": None,
            }
        )

    return alerts[:6]


def build_alerts(model, meta: dict, user_id: int) -> list[dict]:
    return build_alerts_for_watchlist(model, meta, load_watchlist(user_id))
