from pathlib import Path
import json
import pandas as pd
import numpy as np
import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone

DATA_PATH = Path("data/prices_daily.csv")
MODEL_PATH = Path("model/regime_xgb.joblib")
META_PATH = Path("model/model_meta.json")

app = FastAPI(title="Regime API", version="0.1.0")

class PredictRequest(BaseModel):
    # Optional: provide features explicitly (must match meta["features"])
    features: dict | None = None

def load_artifacts():
    if not MODEL_PATH.exists() or not META_PATH.exists():
        raise RuntimeError("Model artifacts not found. Run training/train.py first.")
    model = joblib.load(MODEL_PATH)
    meta = json.loads(META_PATH.read_text())
    return model, meta

MODEL, META = load_artifacts()

def compute_latest_features() -> dict:
    if not DATA_PATH.exists():
        raise RuntimeError("data/prices_daily.csv not found.")
    prices = pd.read_csv(DATA_PATH, index_col=0, parse_dates=True).sort_index()

    if "SPY" not in prices.columns:
        raise RuntimeError(f"Missing SPY column. Found: {list(prices.columns)}")

    # mimic training features
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
        raise RuntimeError("Not enough data to compute features (need ~20+ rows).")

    latest = feats.iloc[-1]

    # Ensure all expected features exist (fill missing with 0.0 for simplicity)
    out = {}
    for f in META["features"]:
        out[f] = float(latest[f]) if f in latest.index and pd.notna(latest[f]) else 0.0
    return out

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": True}

@app.post("/predict")
def predict(req: PredictRequest):
    try:
        feats = req.features if req.features is not None else compute_latest_features()
        # order features
        x = np.array([[feats.get(f, 0.0) for f in META["features"]]], dtype=float)
        probs = MODEL.predict_proba(x)[0]
        idx = int(np.argmax(probs))
        return {
            "regime": META["classes"][idx],
            "confidence": float(probs[idx]),
            "probs": {META["classes"][i]: float(probs[i]) for i in range(len(META["classes"]))},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
