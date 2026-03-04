FALLBACK_SECTORS = [
    {"symbol": "XLK", "label": "Technology", "change_1d": 0.012, "change_5d": 0.027, "change_20d": 0.061, "signal": "Leading"},
    {"symbol": "XLY", "label": "Consumer Discretionary", "change_1d": 0.009, "change_5d": 0.018, "change_20d": 0.033, "signal": "Constructive"},
    {"symbol": "XLI", "label": "Industrials", "change_1d": 0.004, "change_5d": 0.011, "change_20d": 0.022, "signal": "Constructive"},
    {"symbol": "XLF", "label": "Financials", "change_1d": -0.002, "change_5d": 0.004, "change_20d": 0.012, "signal": "Mixed"},
    {"symbol": "XLE", "label": "Energy", "change_1d": -0.007, "change_5d": -0.015, "change_20d": -0.024, "signal": "Lagging"},
    {"symbol": "XLU", "label": "Utilities", "change_1d": -0.003, "change_5d": -0.008, "change_20d": -0.014, "signal": "Defensive"},
]

SECTOR_WATCH = [
    ("XLK", "Technology"),
    ("XLY", "Consumer Discretionary"),
    ("XLI", "Industrials"),
    ("XLF", "Financials"),
    ("XLE", "Energy"),
    ("XLV", "Health Care"),
    ("XLP", "Consumer Staples"),
    ("XLU", "Utilities"),
]


def _signal(change_1d: float, change_20d: float | None) -> str:
    medium = change_20d or 0.0
    if change_1d > 0.007 and medium > 0.03:
        return "Leading"
    if change_1d < -0.007 and medium < -0.02:
        return "Lagging"
    if medium > 0:
        return "Constructive"
    if medium < 0:
        return "Defensive"
    return "Mixed"


def fetch_sector_breadth(limit: int = 8) -> list[dict]:
    try:
        import yfinance as yf
    except ImportError:
        return FALLBACK_SECTORS[:limit]

    sectors = []
    try:
        for symbol, label in SECTOR_WATCH:
            history = yf.Ticker(symbol).history(period="6mo", interval="1d", auto_adjust=True)
            if "Close" not in history.columns or history.empty:
                continue
            series = history["Close"].dropna()
            if len(series) < 21:
                continue
            change_1d = float(series.pct_change().iloc[-1])
            change_5d = float(series.pct_change(5).iloc[-1])
            change_20d = float(series.pct_change(20).iloc[-1])
            sectors.append(
                {
                    "symbol": symbol,
                    "label": label,
                    "change_1d": change_1d,
                    "change_5d": change_5d,
                    "change_20d": change_20d,
                    "signal": _signal(change_1d, change_20d),
                }
            )
    except Exception:
        return FALLBACK_SECTORS[:limit]

    if not sectors:
        return FALLBACK_SECTORS[:limit]
    sectors.sort(key=lambda item: item["change_1d"], reverse=True)
    return sectors[:limit]
