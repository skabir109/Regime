# Regime Monorepo

Regime is an AI-native market intelligence product with a separated frontend and backend architecture.

## Repository Layout

```text
backend/
  app/
  api/
  data/
  model/
  training/
  Dockerfile
  requirements.txt
frontend/
  app/
  lib/
  package.json
docs/
FEATURES.md
BACKLOG.md
```

## Stack

- Frontend: Next.js
- Backend: FastAPI
- Primary database direction: PostgreSQL
- Current local fallback database: SQLite

## Current State

- `backend/` contains the working market intelligence API, auth, watchlists, alerts, subscriptions, and desk collaboration logic.
- `frontend/` now contains the new Next.js product shell and login flow foundation.
- The legacy terminal UI still exists inside the backend during migration, so product work can continue without blocking on the frontend rewrite.

## Local Development

### Backend

1. Create a Python virtual environment.
2. Install backend dependencies:

```bash
cd backend
pip install -r requirements.txt
```

3. Start the API:

```bash
uvicorn app.main:app --reload
```

### Frontend

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Copy env settings:

```bash
cp .env.example .env.local
```

3. Start the Next.js app:

```bash
npm run dev
```

## Hosting Direction

- Frontend: deploy `frontend/` to DigitalOcean App Platform as a Next.js app
- Backend: deploy `backend/` to DigitalOcean App Platform as a FastAPI service
- Database: move from local SQLite to PostgreSQL for hosted environments

## Environment Notes

### Backend

- `DATABASE_URL`
- `FRONTEND_ORIGIN`
- `CORS_ORIGINS`
- `REGIME_SESSION_SECURE`
- `REGIME_SESSION_SAMESITE`
- `ALPHA_VANTAGE_API_KEY`

### Frontend

- `NEXT_PUBLIC_API_BASE_URL`

## Product References

- [Feature Inventory](/mnt/c/Users/shahk/visual%20studio%20projects/regime/FEATURES.md)
- [Backlog](/mnt/c/Users/shahk/visual%20studio%20projects/regime/BACKLOG.md)
- [Product Overview](/mnt/c/Users/shahk/visual%20studio%20projects/regime/docs/product-overview.md)
