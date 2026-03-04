from datetime import datetime, timezone

import numpy as np

from app.schemas import PredictResponse
from app.services.features import compute_latest_features


def predict_from_features(
    model,
    meta: dict,
    features: dict[str, float],
    source: str,
) -> PredictResponse:
    ordered = np.array(
        [[float(features.get(feature, 0.0)) for feature in meta["features"]]],
        dtype=float,
    )
    probabilities = model.predict_proba(ordered)[0]
    best_index = int(np.argmax(probabilities))

    return PredictResponse(
        regime=meta["classes"][best_index],
        confidence=float(probabilities[best_index]),
        probabilities={
            meta["classes"][index]: float(probabilities[index])
            for index in range(len(meta["classes"]))
        },
        timestamp=datetime.now(timezone.utc),
        source=source,
    )


def predict_latest(model, meta: dict) -> PredictResponse:
    features = compute_latest_features(meta["features"])
    return predict_from_features(model, meta, features, source="latest_dataset_snapshot")
