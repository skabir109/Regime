import time
from threading import Lock
import numpy as np

from app.services.features import build_feature_frame, compute_market_panels, compute_market_snapshot, load_prices
from app.services.inference import predict_latest
from app.services.llm import generate_executive_summary
from app.services.news import fetch_market_news
from app.services.playbook import get_playbook_for_regime
from app.services.sectors import fetch_sector_breadth

_SUMMARY_CACHE = {"text": "", "timestamp": 0.0}
_SUMMARY_REFRESH_LOCK = Lock()
_SUMMARY_REFRESH_INFLIGHT = False


def _refresh_executive_summary_async(regime: str, confidence: float, headlines: list[str]) -> None:
    global _SUMMARY_REFRESH_INFLIGHT
    with _SUMMARY_REFRESH_LOCK:
        if _SUMMARY_REFRESH_INFLIGHT:
            return
        _SUMMARY_REFRESH_INFLIGHT = True

    def _worker():
        global _SUMMARY_REFRESH_INFLIGHT
        try:
            text = generate_executive_summary(regime, confidence, headlines)
            if text:
                _SUMMARY_CACHE["text"] = text
                _SUMMARY_CACHE["timestamp"] = time.time()
        finally:
            _SUMMARY_REFRESH_INFLIGHT = False

    import threading
    threading.Thread(target=_worker, daemon=True).start()


def _tone_from_value(value: float, positive_threshold: float, negative_threshold: float) -> str:
    if value >= positive_threshold:
        return "positive"
    if value <= negative_threshold:
        return "negative"
    return "neutral"


def build_market_state_summary(model, meta: dict, prediction=None, sectors=None, news=None) -> dict:
    prediction = prediction or predict_latest(model, meta)
    prices = load_prices()
    feats = build_feature_frame(prices)
    latest = feats.iloc[-1]
    previous = feats.iloc[-2] if len(feats) > 1 else latest
    panels = compute_market_panels()
    snapshot = compute_market_snapshot()
    sectors = sectors if sectors is not None else fetch_sector_breadth(limit=8)
    news = news if news is not None else fetch_market_news(limit=6)

    bullish_count = len([panel for panel in panels if panel["signal"] in {"Bullish", "Calm"}])
    bearish_count = len([panel for panel in panels if panel["signal"] in {"Bearish", "Stress"}])
    breadth_score = bullish_count - bearish_count
    sector_leaders = len([sector for sector in sectors if sector["signal"] in {"Leading", "Constructive"}])
    sector_laggards = len([sector for sector in sectors if sector["signal"] in {"Lagging", "Defensive"}])

    if breadth_score >= 2 and sector_leaders >= sector_laggards:
        breadth = "Broad participation"
    elif breadth_score <= -2 and sector_laggards > sector_leaders:
        breadth = "Defensive participation"
    else:
        breadth = "Mixed participation"

    vix_level = float(latest["vix_level"]) if "vix_level" in latest.index else 0.0
    if vix_level >= 25:
        volatility_state = "Elevated volatility"
    elif vix_level >= 18:
        volatility_state = "Moderate volatility"
    else:
        volatility_state = "Contained volatility"

    spy_mom_20d = float(latest["spy_mom_20d"])
    if spy_mom_20d >= 0.06:
        trend_strength = "Strong uptrend"
    elif spy_mom_20d > 0:
        trend_strength = "Positive trend"
    elif spy_mom_20d <= -0.06:
        trend_strength = "Strong downtrend"
    else:
        trend_strength = "Weak trend"

    confirmation_pairs = 0
    total_pairs = 0
    for feature in ("gld_mom_20d", "uso_mom_20d", "gbp_mom_20d"):
        if feature in latest.index:
            total_pairs += 1
            if np.sign(float(latest[feature])) == np.sign(spy_mom_20d):
                confirmation_pairs += 1
    if total_pairs == 0:
        cross_asset_confirmation = "Limited confirmation"
    elif confirmation_pairs == total_pairs:
        cross_asset_confirmation = "Strong confirmation"
    elif confirmation_pairs == 0:
        cross_asset_confirmation = "Cross-asset divergence"
    else:
        cross_asset_confirmation = "Partial confirmation"

    drivers = [
        {
            "label": "SPY 20D Momentum",
            "value": f"{spy_mom_20d * 100:.2f}%",
            "tone": _tone_from_value(spy_mom_20d, 0.0, 0.0),
        },
        {
            "label": "SPY 20D Volatility",
            "value": f'{float(latest["spy_vol_20d"]) * 100:.2f}%',
            "tone": "negative" if float(latest["spy_vol_20d"]) >= 0.02 else "positive",
        },
        {
            "label": "VIX Level",
            "value": f"{vix_level:.2f}",
            "tone": "negative" if vix_level >= 25 else ("neutral" if vix_level >= 18 else "positive"),
        },
        {
            "label": "Breadth",
            "value": breadth,
            "tone": "positive" if breadth_score > 0 else ("negative" if breadth_score < 0 else "neutral"),
        },
    ]

    warnings = []
    if volatility_state == "Elevated volatility":
        warnings.append("Volatility conditions are high enough to distort slower trend signals.")
    if cross_asset_confirmation == "Cross-asset divergence":
        warnings.append("Cross-asset confirmation is weak. The regime call is less trustworthy when assets disagree.")
    if prediction.confidence >= 0.95:
        warnings.append("Model confidence is extreme because the current training labels are rule-derived, not because uncertainty is fully resolved.")
    tag_counts = {}
    for item in news:
        for tag in item.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    if tag_counts:
        dominant_tag = max(tag_counts, key=tag_counts.get)
        warnings.append(f"Headline flow is currently dominated by {dominant_tag.lower()} catalysts.")

    supporting_signals = []
    conflicting_signals = []
    bull_case = []
    bear_case = []

    if spy_mom_20d > 0:
        supporting_signals.append("S&P 500 medium-term momentum remains positive.")
        bull_case.append("Index momentum is still pointing up, which supports continuation if breadth holds.")
    else:
        conflicting_signals.append("S&P 500 medium-term momentum is not supportive.")
        bear_case.append("Index momentum is not supportive, so rallies may have weaker follow-through.")

    if breadth == "Broad participation":
        supporting_signals.append("Cross-asset breadth is broad enough to support the current state.")
        bull_case.append("Participation is broad enough to support stronger follow-through across risk assets.")
    elif breadth == "Defensive participation":
        conflicting_signals.append("Participation is defensive rather than broad.")
        bear_case.append("Participation is defensive, which usually weakens aggressive upside setups.")
    else:
        conflicting_signals.append("Participation is mixed, so the regime is less clean.")
        bear_case.append("Mixed participation means the tape can look stronger on the surface than it really is.")

    if cross_asset_confirmation == "Strong confirmation":
        supporting_signals.append("Other tracked assets are broadly confirming the direction of SPY.")
        bull_case.append("Cross-asset confirmation is strong enough to trust directional follow-through more.")
    elif cross_asset_confirmation in {"Cross-asset divergence", "Limited confirmation"}:
        conflicting_signals.append("Cross-asset confirmation is weak or divergent.")
        bear_case.append("Cross-asset divergence raises the odds of failed continuation and faster reversals.")

    if volatility_state == "Contained volatility":
        supporting_signals.append("Volatility is contained, which supports cleaner trend following.")
        bull_case.append("Contained volatility supports cleaner trend execution and more orderly risk-taking.")
    elif volatility_state == "Elevated volatility":
        conflicting_signals.append("Volatility is elevated enough to challenge trend reliability.")
        bear_case.append("Elevated volatility can overpower the base regime and force faster trade management.")

    if sectors:
        top_sector = sectors[0]
        weak_sector = sectors[-1]
        if top_sector["signal"] in {"Leading", "Constructive"}:
            supporting_signals.append(
                f'{top_sector["label"]} is helping lead on a sector basis.'
            )
            bull_case.append(f'{top_sector["label"]} leadership is reinforcing the broader market tone.')
        if weak_sector["signal"] in {"Lagging", "Defensive"}:
            conflicting_signals.append(
                f'{weak_sector["label"]} is lagging and may weaken the tape.'
            )
            bear_case.append(f'{weak_sector["label"]} weakness is a drag that could undermine the current regime.')

    changes_since_yesterday = []
    current_confidence = prediction.confidence
    ordered_prev = np.array([[float(previous.get(feature, 0.0)) for feature in meta["features"]]], dtype=float)
    prev_probs = model.predict_proba(ordered_prev)[0]
    prev_regime = meta["classes"][int(prev_probs.argmax())]
    prev_confidence = float(prev_probs.max())

    if prev_regime != prediction.regime:
        changes_since_yesterday.append(
            f"Regime changed from {prev_regime} to {prediction.regime}."
        )
    else:
        changes_since_yesterday.append(
            f"Regime is unchanged since the prior session: {prediction.regime}."
        )

    confidence_delta = current_confidence - prev_confidence
    if abs(confidence_delta) >= 0.05:
        direction = "higher" if confidence_delta > 0 else "lower"
        changes_since_yesterday.append(
            f"Model confidence is {abs(confidence_delta) * 100:.1f} points {direction} than yesterday."
        )

    vol_delta = float(latest["spy_vol_20d"] - previous["spy_vol_20d"])
    if abs(vol_delta) > 0.001:
        direction = "rising" if vol_delta > 0 else "easing"
        changes_since_yesterday.append(f"Realized volatility is {direction}.")

    momentum_delta = float(latest["spy_mom_5d"] - previous["spy_mom_5d"])
    if abs(momentum_delta) > 0.005:
        direction = "improving" if momentum_delta > 0 else "deteriorating"
        changes_since_yesterday.append(f"Short-term momentum is {direction}.")

    if tag_counts:
        changes_since_yesterday.append(f"Headline focus is clustered around {dominant_tag.lower()} themes.")

    sorted_snapshot = sorted(snapshot, key=lambda item: item["change_1d"])
    laggards = sorted_snapshot[:2]
    leaders = sorted_snapshot[-2:][::-1]

    summary = (
        f'{prediction.regime} with {prediction.confidence * 100:.0f}% confidence. '
        f'{trend_strength}, {volatility_state.lower()}, and {breadth.lower()}. '
        f'Cross-asset picture: {cross_asset_confirmation.lower()}.'
    )

    what_matters_now = []
    if bull_case:
        what_matters_now.append(bull_case[0])
    elif supporting_signals:
        what_matters_now.append(supporting_signals[0])

    if bear_case:
        what_matters_now.append(bear_case[0])
    elif conflicting_signals:
        what_matters_now.append(conflicting_signals[0])

    if changes_since_yesterday:
        what_matters_now.append(changes_since_yesterday[0])
    elif warnings:
        what_matters_now.append(warnings[0])

    next_steps = [
        "Read the bull and bear case before trusting the regime at face value.",
        "Open Signals to see which watchlist names are aligned or fighting the current backdrop.",
        "Use World Affairs to confirm whether headline flow supports or threatens the current tape.",
    ]

    # Executive Summary uses stale-while-revalidate so request path never blocks on LLM/network.
    global _SUMMARY_CACHE
    now_ts = time.time()
    headline_texts = [n["title"] for n in news]
    fallback_exec_summary = (
        f'{prediction.regime} regime ({prediction.confidence * 100:.0f}% confidence). '
        "Watch cross-asset confirmation and top headline catalysts before increasing risk."
    )
    if not _SUMMARY_CACHE["text"]:
        _SUMMARY_CACHE["text"] = fallback_exec_summary
        _SUMMARY_CACHE["timestamp"] = now_ts
        _refresh_executive_summary_async(prediction.regime, prediction.confidence, headline_texts)
    elif now_ts - _SUMMARY_CACHE["timestamp"] > 300:
        _refresh_executive_summary_async(prediction.regime, prediction.confidence, headline_texts)

    return {
        "regime": prediction.regime,
        "confidence": prediction.confidence,
        "breadth": breadth,
        "volatility_state": volatility_state,
        "trend_strength": trend_strength,
        "cross_asset_confirmation": cross_asset_confirmation,
        "summary": summary,
        "executive_summary": _SUMMARY_CACHE["text"],
        "playbook": get_playbook_for_regime(prediction.regime),
        "drivers": drivers,
        "warnings": warnings,
        "leaders": [
            {
                "symbol": item["symbol"],
                "label": item["label"],
                "metric": "1D return",
                "value": item["change_1d"],
            }
            for item in leaders
        ],
        "laggards": [
            {
                "symbol": item["symbol"],
                "label": item["label"],
                "metric": "1D return",
                "value": item["change_1d"],
            }
            for item in laggards
        ],
        "supporting_signals": supporting_signals[:5],
        "conflicting_signals": conflicting_signals[:5],
        "changes_since_yesterday": changes_since_yesterday[:5],
        "what_matters_now": what_matters_now[:3],
        "bull_case": bull_case[:4],
        "bear_case": bear_case[:4],
        "next_steps": next_steps,
    }


def compute_regime_transitions(model, meta: dict, lookback: int = 120, limit: int = 8) -> list[dict]:
    prices = load_prices()
    features = build_feature_frame(prices)
    if features.empty:
        return []

    ordered = features.reindex(columns=meta["features"]).fillna(0.0).tail(lookback)
    probabilities = model.predict_proba(ordered.values)
    best_indices = probabilities.argmax(axis=1)
    dates = list(ordered.index)

    segments = []
    start_idx = 0
    current_regime = meta["classes"][int(best_indices[0])]

    for idx in range(1, len(dates)):
        next_regime = meta["classes"][int(best_indices[idx])]
        if next_regime != current_regime:
            window = probabilities[start_idx:idx]
            segments.append(
                {
                    "regime": current_regime,
                    "started_at": str(dates[start_idx].date()),
                    "ended_at": str(dates[idx - 1].date()),
                    "duration_days": idx - start_idx,
                    "average_confidence": float(window.max(axis=1).mean()),
                }
            )
            start_idx = idx
            current_regime = next_regime

    window = probabilities[start_idx:]
    segments.append(
        {
            "regime": current_regime,
            "started_at": str(dates[start_idx].date()),
            "ended_at": str(dates[-1].date()),
            "duration_days": len(dates) - start_idx,
            "average_confidence": float(window.max(axis=1).mean()),
        }
    )

    return segments[-limit:][::-1]
