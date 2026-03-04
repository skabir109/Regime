from app.services.news import fetch_market_news, match_related_news
from app.services.signals import FALLBACK_SIGNALS, fetch_signals_for_universe
from app.services.watchlist import load_watchlist
from app.services.world_affairs import build_watchlist_exposures


def _find_signal(symbol: str, signals: list[dict]) -> dict | None:
    for signal in signals:
        if signal["symbol"] == symbol:
            return signal
    return next((signal for signal in FALLBACK_SIGNALS if signal["symbol"] == symbol), None)


def _describe_alignment(regime: str, stance: str) -> str:
    if regime == "RiskOn":
        if stance in {"Bullish", "Constructive"}:
            return "Aligned with the current market regime."
        if stance in {"Bearish", "Defensive"}:
            return "Fighting the current market regime."
        return "Only partially aligned with the current regime."
    if regime in {"RiskOff", "HighVol"}:
        if stance in {"Bearish", "Defensive"}:
            return "Aligned with the current defensive backdrop."
        if stance in {"Bullish", "Constructive"}:
            return "Needs extra confirmation in the current backdrop."
        return "Setup quality depends on catalyst follow-through."
    return "Regime alignment is mixed."


def _trade_implication(regime: str, stance: str, reasons: list[str]) -> str:
    lead_reason = reasons[0] if reasons else "Wait for clearer confirmation."
    if regime == "RiskOn" and stance in {"Bullish", "Constructive"}:
        return f"Bias toward continuation setups if {lead_reason.lower()}"
    if regime in {"RiskOff", "HighVol"} and stance in {"Bullish", "Constructive"}:
        return f"Treat as tactical only and demand tighter risk because {lead_reason.lower()}"
    if stance in {"Bearish", "Defensive"}:
        return f"Works better as a hedge or relative underperformer if {lead_reason.lower()}"
    return lead_reason


def _catalyst_risk(catalyst_item: dict | None, exposure: dict | None) -> str:
    if catalyst_item and exposure:
        return f"Headline risk is active and tied to {', '.join(exposure['themes'][:2])}."
    if catalyst_item:
        return "Headline risk is active for this symbol."
    if exposure:
        return f"Macro sensitivity is elevated through {', '.join(exposure['themes'][:2])}."
    return "No immediate catalyst pressure detected."


def _sector_readthrough(signal: dict | None, exposure: dict | None) -> str:
    links = exposure["market_links"][:2] if exposure else []
    if signal and links:
        return f"{signal['stance']} tone with read-through from {', '.join(links)}."
    if signal:
        return f"{signal['stance']} tone with limited sector context."
    if links:
        return f"Watch sector flow in {', '.join(links)}."
    return "Sector read-through is limited."


def build_watchlist_intelligence(user_id: int, state: dict | None = None) -> list[dict]:
    watchlist = load_watchlist(user_id)
    if not watchlist:
        return []

    state = state or {"regime": "RiskOn"}
    signals = fetch_signals_for_universe(watchlist)
    news = fetch_market_news(limit=10)
    exposures = {item["symbol"]: item for item in build_watchlist_exposures(user_id)}
    insights = []

    for item in watchlist:
        signal = _find_signal(item["symbol"], signals)
        related_news = match_related_news(item["symbol"], item["label"], news, limit=3)
        catalyst_item = related_news[0] if related_news else None
        exposure = exposures.get(item["symbol"])

        if signal:
            summary = (
                f'{signal["stance"]} setup with score {int(signal["score"] * 100)}/100. '
                f'{signal["reasons"][0]}'
            )
            stance = signal["stance"]
        else:
            summary = "This symbol is on watch, but there is not enough live data to score it yet."
            stance = "Monitor"

        insights.append(
            {
                "symbol": item["symbol"],
                "label": item["label"],
                "stance": stance,
                "summary": summary,
                "score": signal["score"] if signal else None,
                "price": signal["price"] if signal else None,
                "change_1d": signal["change_1d"] if signal else None,
                "change_20d": signal["change_20d"] if signal else None,
                "reasons": signal["reasons"][:3] if signal else [],
                "catalyst": catalyst_item["title"] if catalyst_item else None,
                "regime_alignment": _describe_alignment(state["regime"], stance),
                "trade_implication": _trade_implication(state["regime"], stance, signal["reasons"] if signal else []),
                "catalyst_risk": _catalyst_risk(catalyst_item, exposure),
                "sector_readthrough": _sector_readthrough(signal, exposure),
                "related_news": related_news,
            }
        )

    return insights
