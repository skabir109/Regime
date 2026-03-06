from __future__ import annotations


FALLBACK_SIGNALS = [
    {
        "symbol": "NVDA",
        "label": "NVIDIA",
        "stance": "Bullish",
        "score": 0.86,
        "price": 0.0,
        "change_1d": 0.021,
        "change_20d": 0.118,
        "reasons": [
            "Price remains above short and medium trend references.",
            "20-day momentum is positive.",
            "Leadership behavior is consistent with risk-on participation.",
        ],
    },
    {
        "symbol": "AAPL",
        "label": "Apple",
        "stance": "Neutral",
        "score": 0.53,
        "price": 0.0,
        "change_1d": -0.002,
        "change_20d": 0.019,
        "reasons": [
            "Trend remains intact, but short-term momentum is mixed.",
            "Signal strength is not broad enough for a strong directional call.",
        ],
    },
    {
        "symbol": "TSLA",
        "label": "Tesla",
        "stance": "Bearish",
        "score": 0.24,
        "price": 0.0,
        "change_1d": -0.031,
        "change_20d": -0.094,
        "reasons": [
            "Short-term price action is deteriorating.",
            "20-day momentum remains negative.",
            "Volatility profile suggests unstable participation.",
        ],
    },
]

DEFAULT_SIGNAL_UNIVERSE = [
    ("AAPL", "Apple"),
    ("MSFT", "Microsoft"),
    ("NVDA", "NVIDIA"),
    ("AMZN", "Amazon"),
    ("META", "Meta"),
    ("TSLA", "Tesla"),
    ("AMD", "AMD"),
    ("GOOGL", "Alphabet"),
]


def _build_monitor_card(symbol: str, label: str) -> dict:
    return {
        "symbol": symbol,
        "label": label,
        "stance": "Monitor",
        "score": 0.5,
        "price": None,
        "change_1d": None,
        "change_20d": None,
        "reasons": [
            "Live price history is unavailable for this symbol right now.",
            "Keep the name on watch until enough data is available for a directional read.",
        ],
    }


def _score_series(series) -> dict:
    close = series.dropna()
    if len(close) < 60:
        raise ValueError("Not enough data to score series.")

    latest = float(close.iloc[-1])
    ma_20 = float(close.rolling(20).mean().iloc[-1])
    ma_50 = float(close.rolling(50).mean().iloc[-1])
    change_1d = float(close.pct_change().iloc[-1])
    change_20d = float(close.pct_change(20).iloc[-1])
    realized_vol = float(close.pct_change().rolling(20).std().iloc[-1])

    trend_gap_20 = ((latest / ma_20) - 1.0) if ma_20 else 0.0
    trend_gap_50 = ((latest / ma_50) - 1.0) if ma_50 else 0.0

    components = [
        1.0 if latest > ma_20 else 0.0,
        1.0 if latest > ma_50 else 0.0,
        max(min(change_20d / 0.15, 1.0), -1.0),
        max(min((0.035 - realized_vol) / 0.035, 1.0), -1.0),
        max(min(trend_gap_20 / 0.08, 1.0), -1.0),
        max(min(trend_gap_50 / 0.12, 1.0), -1.0),
    ]
    normalized = (sum(components) + len(components)) / (len(components) * 2.0)

    if normalized >= 0.66:
        stance = "Bullish"
    elif normalized <= 0.38:
        stance = "Bearish"
    else:
        stance = "Neutral"

    reasons = []
    reasons.append(
        "Price is above the 20-day average." if latest > ma_20 else "Price is below the 20-day average."
    )
    reasons.append(
        "Price is above the 50-day average." if latest > ma_50 else "Price is below the 50-day average."
    )
    reasons.append(
        "20-day momentum is positive." if change_20d > 0 else "20-day momentum is negative."
    )
    reasons.append(
        "Realized volatility is contained." if realized_vol < 0.035 else "Realized volatility is elevated."
    )
    reasons.append(
        "Price is extended above the 20-day trend." if trend_gap_20 > 0.03 else "Price is not materially extended above the 20-day trend."
    )

    return {
        "stance": stance,
        "score": round(float(normalized), 2),
        "price": latest,
        "change_1d": change_1d,
        "change_20d": change_20d,
        "reasons": reasons[:4],
    }


def _normalize_universe(items: list[tuple[str, str]] | list[dict]) -> list[tuple[str, str]]:
    normalized = []
    seen = set()
    for item in items:
        if isinstance(item, dict):
            symbol = str(item.get("symbol", "")).strip().upper()
            label = str(item.get("label") or symbol).strip() or symbol
        else:
            symbol = str(item[0]).strip().upper()
            label = str(item[1]).strip() if len(item) > 1 else symbol
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        normalized.append((symbol, label))
    return normalized


def _fallback_card(symbol: str, label: str) -> dict:
    match = next((item for item in FALLBACK_SIGNALS if item["symbol"] == symbol), None)
    if match:
        return {
            **match,
            "label": label or match["label"],
        }
    return _build_monitor_card(symbol, label)


def _extract_close_series(frame, ticker: str):
    if frame is None or getattr(frame, "empty", True):
        return None
    # MultiIndex path: columns like ("Close", "AAPL")
    if hasattr(frame.columns, "nlevels") and frame.columns.nlevels > 1:
        if ("Close", ticker) in frame.columns:
            return frame[("Close", ticker)].dropna()
        if (ticker, "Close") in frame.columns:
            return frame[(ticker, "Close")].dropna()
    # Single ticker fallback
    if "Close" in frame.columns:
        return frame["Close"].dropna()
    return None


def fetch_signals_for_universe(
    items: list[tuple[str, str]] | list[dict],
    limit: int | None = None,
    sort_by_score: bool = False,
) -> list[dict]:
    universe = _normalize_universe(items)
    if not universe:
        return []

    try:
        import yfinance as yf
    except ImportError:
        cards = [_fallback_card(symbol, label) for symbol, label in universe]
        return cards[:limit] if limit else cards

    cards = []
    failures = set()
    tickers = [ticker for ticker, _ in universe]
    try:
        history = yf.download(
            tickers=tickers,
            period="3mo",
            interval="1d",
            auto_adjust=True,
            progress=False,
            group_by="column",
            threads=True,
            timeout=2,
        )
        for ticker, label in universe:
            close_series = _extract_close_series(history, ticker)
            if close_series is None or close_series.empty:
                failures.add(ticker)
                continue
            scored = _score_series(close_series)
            cards.append(
                {
                    "symbol": ticker,
                    "label": label,
                    **scored,
                }
            )
    except Exception:
        cards = [_fallback_card(symbol, label) for symbol, label in universe]
        return cards[:limit] if limit else cards

    for ticker, label in universe:
        if ticker in failures:
            cards.append(_fallback_card(ticker, label))

    if sort_by_score:
        cards.sort(key=lambda card: card["score"], reverse=True)

    return cards[:limit] if limit else cards


def fetch_trending_signals(limit: int = 6) -> list[dict]:
    cards = fetch_signals_for_universe(DEFAULT_SIGNAL_UNIVERSE, sort_by_score=True)
    if not cards:
        return FALLBACK_SIGNALS[:limit]

    bullish = [card for card in cards if card["stance"] == "Bullish"]
    bearish = sorted([card for card in cards if card["stance"] == "Bearish"], key=lambda card: card["score"])
    neutral = [card for card in cards if card["stance"] not in {"Bullish", "Bearish"}]
    ordered = bullish[: max(1, limit // 2)] + bearish[: max(1, limit // 3)] + neutral
    return ordered[:limit]
