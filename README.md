# Regime

Regime is a market regime detection MVP built for the DigitalOcean AI Hackathon. It classifies the current market environment into `RiskOn`, `RiskOff`, or `HighVol` using multi-asset financial features and exposes the result through a FastAPI service.

## MVP Scope

- Train a baseline regime classifier from historical market data
- Compute the latest feature set from stored daily prices
- Serve live inference through a simple API
- Package the service for local development and cloud deployment

## Project Structure

```text
app/
  main.py
  config.py
  schemas.py
  services/
api/
  main.py
data/
model/
training/
docs/
```

## Quick Start

1. Create a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Train or refresh the model with `python3 training/train.py`.
4. Start the API with `uvicorn app.main:app --reload`.
5. Open `http://127.0.0.1:8000/` for the dashboard or `http://127.0.0.1:8000/docs` for the API docs.

## Key Endpoints

- `GET /`
- `GET /app`
- `GET /health`
- `GET /metadata`
- `POST /predict`
- `POST /predict/latest`

## Documentation

- [Product Overview](/mnt/c/Users/shahk/visual studio projects/regime/docs/product-overview.md)
- [Builder Checklist](/mnt/c/Users/shahk/visual studio projects/regime/docs/builder-checklist.md)
- [Original PRD](/mnt/c/Users/shahk/visual studio projects/regime/prd.md)

## Deployment

The included `Dockerfile` packages the inference API for deployment on DigitalOcean App Platform or a container-based Droplet workflow.
