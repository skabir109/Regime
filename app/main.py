from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import APP_DESCRIPTION, APP_TITLE, APP_VERSION, DATA_PATH, STATIC_DIR
from app.schemas import HealthResponse, MetadataResponse, PredictRequest, PredictResponse
from app.services.inference import predict_from_features, predict_latest
from app.services.model import load_artifacts


app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

MODEL, META = load_artifacts()


@app.get("/", tags=["system"])
def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/app", tags=["system"])
def app_info():
    return {
        "name": APP_TITLE,
        "version": APP_VERSION,
        "docs": "/docs",
        "status": "ready",
    }


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health():
    return HealthResponse(
        status="ok",
        model_loaded=True,
        data_available=DATA_PATH.exists(),
    )


@app.get("/metadata", response_model=MetadataResponse, tags=["model"])
def metadata():
    return MetadataResponse(
        classes=META["classes"],
        features=META["features"],
        thresholds=META.get("thresholds", {}),
    )


@app.post("/predict", response_model=PredictResponse, tags=["inference"])
def predict(request: PredictRequest):
    try:
        if request.features is None:
            return predict_latest(MODEL, META)
        return predict_from_features(
            MODEL,
            META,
            request.features,
            source="custom_payload",
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/predict/latest", response_model=PredictResponse, tags=["inference"])
def predict_latest_endpoint():
    try:
        return predict_latest(MODEL, META)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
