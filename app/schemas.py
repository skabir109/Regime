from datetime import datetime

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    features: dict[str, float] | None = Field(
        default=None,
        description="Optional raw feature payload matching the trained model schema.",
    )


class PredictResponse(BaseModel):
    regime: str
    confidence: float
    probabilities: dict[str, float]
    timestamp: datetime
    source: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    data_available: bool


class MetadataResponse(BaseModel):
    classes: list[str]
    features: list[str]
    thresholds: dict[str, float]
