import json

import joblib

from app.config import META_PATH, MODEL_PATH


def load_artifacts():
    if not MODEL_PATH.exists() or not META_PATH.exists():
        raise RuntimeError("Model artifacts not found. Run training/train.py first.")

    model = joblib.load(MODEL_PATH)
    meta = json.loads(META_PATH.read_text())
    return model, meta
