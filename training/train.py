from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from xgboost import XGBClassifier
import joblib

DATA_PATH = Path("data/prices_daily.csv")
MODEL_DIR = Path("model")
MODEL_PATH = MODEL_DIR / "regime_xgb.joblib"
META_PATH = MODEL_DIR / "model_meta.json"

# --- Regime labeling rules (simple, hackathon-safe) ---
# HighVol: VIX is high OR SPY rolling vol is high
# RiskOn: SPY trend positive
# RiskOff: otherwise
VIX_HIGH = 25.0              # threshold; adjust if needed
SPY_VOL_HIGH = 0.02          # ~2% daily vol (rolling std of returns)

def load_prices() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, index_col=0, parse_dates=True)
    df = df.sort_index()
    return df

def make_features(prices: pd.DataFrame) -> pd.DataFrame:
    col_spy = "SPY"
    col_gld = "GLD" if "GLD" in prices.columns else None
    col_uso = "USO" if "USO" in prices.columns else None
    col_vix = "VIX" if "VIX" in prices.columns else ("VIX" if "VIX" in prices.columns else None)
    col_gbp = "GBPUSD=X" if "GBPUSD=X" in prices.columns else ("GBPUSD=X" if "GBPUSD=X" in prices.columns else None)

    if col_spy not in prices.columns:
        raise ValueError(f"Missing SPY column. Found columns: {list(prices.columns)}")

    rets = prices.pct_change()

    feats = pd.DataFrame(index=prices.index)

    feats["spy_ret_1d"] = rets[col_spy]
    feats["spy_mom_5d"] = prices[col_spy].pct_change(5)
    feats["spy_mom_20d"] = prices[col_spy].pct_change(20)
    feats["spy_vol_10d"] = rets[col_spy].rolling(10).std()
    feats["spy_vol_20d"] = rets[col_spy].rolling(20).std()

    if col_gld:
        feats["gld_ret_1d"] = rets[col_gld]
        feats["gld_mom_20d"] = prices[col_gld].pct_change(20)

    if col_uso:
        feats["uso_ret_1d"] = rets[col_uso]
        feats["uso_mom_20d"] = prices[col_uso].pct_change(20)

    if col_gbp:
        feats["gbp_ret_1d"] = rets[col_gbp]
        feats["gbp_mom_20d"] = prices[col_gbp].pct_change(20)

    if col_vix and col_vix in prices.columns:
        feats["vix_level"] = prices[col_vix]
        feats["vix_chg_5d"] = prices[col_vix].pct_change(5)

    feats = feats.dropna()
    return feats


def label_regimes(prices: pd.DataFrame, feats: pd.DataFrame) -> pd.Series:
    """
    Label using the *same cleaned index* as feats to avoid NaNs from rolling windows.
    """
    y = pd.Series(index=feats.index, dtype="object")

    # HighVol if VIX high OR SPY rolling vol high
    highvol = pd.Series(False, index=feats.index)

    if "vix_level" in feats.columns:
        highvol = highvol | (feats["vix_level"] >= VIX_HIGH)

    # feats already contains spy_vol_20d and spy_mom_20d (non-NaN after dropna)
    highvol = highvol | (feats["spy_vol_20d"] >= SPY_VOL_HIGH)

    y[highvol] = "HighVol"
    y[(~highvol) & (feats["spy_mom_20d"] > 0)] = "RiskOn"
    y[(~highvol) & (feats["spy_mom_20d"] <= 0)] = "RiskOff"

    return y

def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    prices = load_prices()
    feats = make_features(prices)
    y = label_regimes(prices, feats)

    # Encode labels
    classes = ["RiskOff", "RiskOn", "HighVol"]
    y_cat = pd.Categorical(y, categories=classes)
    if y_cat.isna().any():
        raise RuntimeError("Labeling produced NaNs; check thresholds and data alignment.")
    y_enc = y_cat.codes

    X = feats.values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.2, shuffle=False
    )

    model = XGBClassifier(
        n_estimators=400,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="multi:softprob",
        num_class=len(classes),
        reg_lambda=1.0,
        random_state=42,
        n_jobs=4,
        eval_metric="mlogloss",
    )

    model.fit(X_train, y_train)

    probs = model.predict_proba(X_test)
    preds = probs.argmax(axis=1)

    print("Classification report:")
    print(classification_report(y_test, preds, target_names=classes))

    joblib.dump(model, MODEL_PATH)

    meta = {
        "classes": classes,
        "features": feats.columns.tolist(),
        "thresholds": {
            "VIX_HIGH": VIX_HIGH,
            "SPY_VOL_HIGH": SPY_VOL_HIGH
        }
    }
    META_PATH.write_text(json.dumps(meta, indent=2))
    print(f"Saved model to {MODEL_PATH}")
    print(f"Saved meta to {META_PATH}")


if __name__ == "__main__":
    main()
