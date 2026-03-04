import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

from app.config import DATA_PATH

LIVE_SYMBOLS = ["SPY", "GLD", "USO", "GBPUSD=X", "VIX", "TLT", "BITO"]

def fetch_live_prices() -> pd.DataFrame:
    """Fetch recent daily prices for core universe using yfinance."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    # Map symbols if needed (yfinance uses different tickers for some)
    # VIX is ^VIX, GBPUSD=X is usually fine
    yf_symbols = [s if s != "VIX" else "^VIX" for s in LIVE_SYMBOLS]
    
    try:
        data = yf.download(yf_symbols, start=start_date, end=end_date, interval="1d", progress=False)
        if data.empty:
            return pd.DataFrame()
            
        # Handle MultiIndex columns from yfinance
        prices = data["Adj Close"] if "Adj Close" in data else data["Close"]
        
        # Rename ^VIX back to VIX
        if "^VIX" in prices.columns:
            prices = prices.rename(columns={"^VIX": "VIX"})
            
        return prices.ffill().dropna()
    except Exception:
        return pd.DataFrame()


def load_prices() -> pd.DataFrame:
    # Try live data first
    live_df = fetch_live_prices()
    if not live_df.empty and "SPY" in live_df.columns:
        return live_df

    if not DATA_PATH.exists():
        raise RuntimeError("data/prices_daily.csv not found and live fetch failed.")

    prices = pd.read_csv(DATA_PATH, index_col=0, parse_dates=True).sort_index().ffill()
    if "SPY" not in prices.columns:
        raise RuntimeError(f"Missing SPY column in CSV. Found: {list(prices.columns)}")
    return prices


def build_feature_frame(prices: pd.DataFrame) -> pd.DataFrame:
    aligned = prices.ffill()
    rets = aligned.pct_change()
    feats = pd.DataFrame(index=prices.index)
    spy_ma_20 = aligned["SPY"].rolling(20).mean()
    spy_ma_50 = aligned["SPY"].rolling(50).mean()
    spy_roll_high_20 = aligned["SPY"].rolling(20).max()
    spy_roll_high_60 = aligned["SPY"].rolling(60).max()

    feats["spy_ret_1d"] = rets["SPY"]
    feats["spy_mom_5d"] = aligned["SPY"].pct_change(5)
    feats["spy_mom_20d"] = aligned["SPY"].pct_change(20)
    feats["spy_mom_60d"] = aligned["SPY"].pct_change(60)
    feats["spy_vol_10d"] = rets["SPY"].rolling(10).std()
    feats["spy_vol_20d"] = rets["SPY"].rolling(20).std()
    feats["spy_trend_gap_20d"] = (aligned["SPY"] / spy_ma_20) - 1.0
    feats["spy_trend_gap_50d"] = (aligned["SPY"] / spy_ma_50) - 1.0
    feats["spy_drawdown_20d"] = (aligned["SPY"] / spy_roll_high_20) - 1.0
    feats["spy_drawdown_60d"] = (aligned["SPY"] / spy_roll_high_60) - 1.0

    if "GLD" in aligned.columns:
        feats["gld_ret_1d"] = rets["GLD"]
        feats["gld_mom_20d"] = aligned["GLD"].pct_change(20)

    if "USO" in aligned.columns:
        feats["uso_ret_1d"] = rets["USO"]
        feats["uso_mom_20d"] = aligned["USO"].pct_change(20)

    if "GBPUSD=X" in aligned.columns:
        feats["gbp_ret_1d"] = rets["GBPUSD=X"]
        feats["gbp_mom_20d"] = aligned["GBPUSD=X"].pct_change(20)

    if "TLT" in aligned.columns:
        feats["tlt_ret_1d"] = rets["TLT"]
        feats["tlt_mom_20d"] = aligned["TLT"].pct_change(20)

    if "BITO" in aligned.columns:
        feats["bito_ret_1d"] = rets["BITO"]
        feats["bito_mom_20d"] = aligned["BITO"].pct_change(20)

    if "VIX" in aligned.columns:
        feats["vix_level"] = aligned["VIX"]
        feats["vix_chg_5d"] = aligned["VIX"].pct_change(5)
        feats["vix_gap_20d"] = (aligned["VIX"] / aligned["VIX"].rolling(20).mean()) - 1.0

    if {"GLD", "SPY"}.issubset(aligned.columns):
        feats["gld_vs_spy_20d"] = aligned["GLD"].pct_change(20) - aligned["SPY"].pct_change(20)
    if {"USO", "SPY"}.issubset(aligned.columns):
        feats["uso_vs_spy_20d"] = aligned["USO"].pct_change(20) - aligned["SPY"].pct_change(20)
    if {"TLT", "SPY"}.issubset(aligned.columns):
        feats["tlt_vs_spy_20d"] = aligned["TLT"].pct_change(20) - aligned["SPY"].pct_change(20)
    if {"VIX", "SPY"}.issubset(aligned.columns):
        feats["vix_spy_stress"] = aligned["VIX"].pct_change(5) - aligned["SPY"].pct_change(5)

    required = [
        "spy_ret_1d",
        "spy_mom_5d",
        "spy_mom_20d",
        "spy_mom_60d",
        "spy_vol_10d",
        "spy_vol_20d",
        "spy_trend_gap_20d",
        "spy_trend_gap_50d",
        "spy_drawdown_20d",
        "spy_drawdown_60d",
    ]
    feats = feats.dropna(subset=required)
    return feats.ffill().fillna(0.0)


def compute_latest_features(expected_features: list[str]) -> dict[str, float]:
    prices = load_prices()
    feats = build_feature_frame(prices)

    feats = feats.dropna()
    if feats.empty:
        raise RuntimeError("Not enough data to compute features. Need at least 20 rows.")

    latest = feats.iloc[-1]
    return {
        feature: float(latest[feature])
        if feature in latest.index and pd.notna(latest[feature])
        else 0.0
        for feature in expected_features
    }


def compute_market_snapshot() -> list[dict]:
    prices = load_prices()
    asset_labels = {
        "SPY": "S&P 500",
        "GLD": "Gold",
        "USO": "Oil",
        "GBPUSD=X": "GBP/USD",
        "VIX": "Volatility",
        "TLT": "Treasury Bonds",
        "BITO": "Bitcoin Strategy",
    }
    snapshot = []

    for symbol, label in asset_labels.items():
        if symbol not in prices.columns:
            continue

        series = prices[symbol].dropna()
        if len(series) < 2:
            continue

        latest = float(series.iloc[-1])
        change_1d = float(series.pct_change().iloc[-1])
        change_5d = float(series.pct_change(5).iloc[-1]) if len(series) >= 6 else None
        snapshot.append(
            {
                "symbol": symbol,
                "label": label,
                "price": latest,
                "change_1d": change_1d,
                "change_5d": change_5d,
            }
        )

    return snapshot


def compute_market_panels(window: int = 20) -> list[dict]:
    prices = load_prices()
    asset_labels = {
        "SPY": "S&P 500",
        "GLD": "Gold",
        "USO": "Oil",
        "GBPUSD=X": "GBP/USD",
        "VIX": "Volatility",
        "TLT": "Treasury Bonds",
        "BITO": "Bitcoin Strategy",
    }
    panels = []

    for symbol, label in asset_labels.items():
        if symbol not in prices.columns:
            continue

        series = prices[symbol].dropna()
        if len(series) < 6:
            continue

        windowed = series.tail(window)
        base = float(windowed.iloc[0])
        if base == 0:
            trend = [0.0 for _ in windowed]
        else:
            trend = [float((value / base) - 1.0) for value in windowed]

        latest = float(series.iloc[-1])
        change_1d = float(series.pct_change().iloc[-1])
        change_5d = float(series.pct_change(5).iloc[-1]) if len(series) >= 6 else None
        change_20d = float(series.pct_change(20).iloc[-1]) if len(series) >= 21 else None

        signal = "Neutral"
        if symbol == "VIX":
            if latest >= 25:
                signal = "Stress"
            elif latest <= 18:
                signal = "Calm"
        else:
            if (change_5d or 0.0) > 0.015 and (change_20d or 0.0) > 0:
                signal = "Bullish"
            elif (change_5d or 0.0) < -0.015 and (change_20d or 0.0) < 0:
                signal = "Bearish"

        panels.append(
            {
                "symbol": symbol,
                "label": label,
                "price": latest,
                "change_1d": change_1d,
                "change_5d": change_5d,
                "change_20d": change_20d,
                "signal": signal,
                "trend": trend,
            }
        )

    return panels
