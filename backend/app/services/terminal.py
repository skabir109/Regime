import numpy as np

from app.services.features import build_feature_frame, load_prices


def compute_regime_history(model, meta: dict, limit: int = 30) -> list[dict]:
    prices = load_prices()
    features = build_feature_frame(prices)
    if features.empty:
        return []

    ordered = features.reindex(columns=meta["features"]).fillna(0.0)
    probabilities = model.predict_proba(ordered.values)
    best_indices = probabilities.argmax(axis=1)

    history = []
    for idx, timestamp in enumerate(ordered.index[-limit:]):
        row_position = len(ordered.index) - limit + idx if len(ordered.index) > limit else idx
        best_index = int(best_indices[row_position])
        history.append(
            {
                "date": str(timestamp.date()),
                "regime": meta["classes"][best_index],
                "confidence": float(np.max(probabilities[row_position])),
            }
        )

    return history
