import pandas as pd

from app.config import DATA_PATH


def load_prices() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise RuntimeError("data/prices_daily.csv not found.")

    prices = pd.read_csv(DATA_PATH, index_col=0, parse_dates=True).sort_index()
    if "SPY" not in prices.columns:
        raise RuntimeError(f"Missing SPY column. Found: {list(prices.columns)}")
    return prices


def compute_latest_features(expected_features: list[str]) -> dict[str, float]:
    prices = load_prices()
    rets = prices.pct_change()
    feats = pd.DataFrame(index=prices.index)

    feats["spy_ret_1d"] = rets["SPY"]
    feats["spy_mom_5d"] = prices["SPY"].pct_change(5)
    feats["spy_mom_20d"] = prices["SPY"].pct_change(20)
    feats["spy_vol_10d"] = rets["SPY"].rolling(10).std()
    feats["spy_vol_20d"] = rets["SPY"].rolling(20).std()

    if "GLD" in prices.columns:
        feats["gld_ret_1d"] = rets["GLD"]
        feats["gld_mom_20d"] = prices["GLD"].pct_change(20)

    if "USO" in prices.columns:
        feats["uso_ret_1d"] = rets["USO"]
        feats["uso_mom_20d"] = prices["USO"].pct_change(20)

    if "GBPUSD=X" in prices.columns:
        feats["gbp_ret_1d"] = rets["GBPUSD=X"]
        feats["gbp_mom_20d"] = prices["GBPUSD=X"].pct_change(20)

    if "VIX" in prices.columns:
        feats["vix_level"] = prices["VIX"]
        feats["vix_chg_5d"] = prices["VIX"].pct_change(5)

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
