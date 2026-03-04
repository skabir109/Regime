from app.services.features import compute_market_snapshot, compute_market_panels
from app.services.inference import predict_latest
from app.services.news import fetch_market_news


REGIME_NARRATIVES = {
    "RiskOn": "The model sees a supportive environment where trend and participation remain constructive.",
    "RiskOff": "The model sees a defensive environment where capital preservation and caution matter more than upside chase.",
    "HighVol": "The model sees unstable conditions where fast repricing and elevated volatility can dominate slower signals.",
}


def _describe_asset(asset: dict) -> str:
    direction = "up" if asset["change_1d"] >= 0 else "down"
    return f'{asset["label"]} is {direction} {abs(asset["change_1d"]) * 100:.2f}% on the day'


def build_story_briefing(model, meta: dict) -> dict:
    prediction = predict_latest(model, meta)
    snapshot = compute_market_snapshot()
    panels = compute_market_panels()
    news = fetch_market_news(limit=5)

    strongest = max(snapshot, key=lambda item: item["change_1d"], default=None)
    weakest = min(snapshot, key=lambda item: item["change_1d"], default=None)
    stress_panel = next((panel for panel in panels if panel["symbol"] == "VIX"), None)
    top_headlines = [item["title"] for item in news[:3]]

    summary_parts = [REGIME_NARRATIVES.get(prediction.regime, "The model returned a current market state.")]
    if strongest:
        summary_parts.append(f"Leadership is coming from {_describe_asset(strongest)}.")
    if weakest and weakest != strongest:
        summary_parts.append(f"The weakest tape is {_describe_asset(weakest)}.")
    if stress_panel:
        summary_parts.append(f'Volatility signal: {stress_panel["signal"]}.')

    narrative = " ".join(summary_parts)

    action_items = [
        "Use the regime classification as a top-down filter before adding risk.",
        "Cross-check the market panel for confirmation across equities, commodities, FX, and volatility.",
        "Scan the news tape for catalysts that could validate or disrupt the current setup.",
    ]
    risks = [
        "Model confidence is not a guarantee of directional follow-through.",
        "Headline risk can cause regime changes faster than daily features update.",
        "Signal quality weakens when cross-asset confirmation breaks down.",
    ]

    key_points = []
    if strongest:
        key_points.append(
            f'Strongest asset today: {strongest["label"]} ({strongest["change_1d"] * 100:.2f}%).'
        )
    if weakest:
        key_points.append(
            f'Weakest asset today: {weakest["label"]} ({weakest["change_1d"] * 100:.2f}%).'
        )
    key_points.append(f"Model confidence is {prediction.confidence * 100:.1f}%.")
    if top_headlines:
        key_points.append(f"Lead headline: {top_headlines[0]}")

    return {
        "headline": f"{prediction.regime} regime with {prediction.confidence * 100:.0f}% confidence",
        "summary": narrative,
        "narrative": (
            f"{REGIME_NARRATIVES.get(prediction.regime, '')} "
            "Market internals and the headline tape should be reviewed together before acting on the call."
        ).strip(),
        "key_points": key_points,
        "action_items": action_items,
        "risks": risks,
        "top_headlines": top_headlines,
    }
