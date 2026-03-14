# Regime Deployment Guide (DigitalOcean App Platform)

This guide provides the exact steps to deploy the Regime full-stack application. We will use **DigitalOcean App Platform** for both the Next.js frontend and the FastAPI backend, with **DigitalOcean Managed PostgreSQL** for persistence.

## Current Architecture
*   **Frontend:** Next.js (React) - `frontend/`
*   **Backend:** FastAPI (Python) - `backend/`
*   **Database:** DigitalOcean Managed PostgreSQL

---

## Pre-Deployment Requirements

### 1. Database Preparation
Create a DigitalOcean Managed PostgreSQL cluster and collect:
*   `DATABASE_URL`: The connection string your app will use at runtime.
*   `DIRECT_URL`: The direct connection string used for schema creation and startup migrations.

If you are cutting over from Supabase, copy the data first with [docs/digitalocean-db-migration.md](/mnt/c/Users/shahk/visual%20studio%20projects/regime/docs/digitalocean-db-migration.md).

### 2. LLM Key
*   You will need your `LLM_API_KEY` (e.g., OpenAI or your custom agent URL) for the production environment.

### 3. Security and Rate-Limit Infrastructure
For production-safe deployment, prepare:
*   `REGIME_CSRF_SECRET`: A long random secret used to sign CSRF tokens.
*   `REDIS_URL`: Shared Redis instance used for cross-instance burst limiting.
*   `REGIME_SESSION_SECURE=true`
*   `REGIME_SESSION_SAMESITE=strict`
*   `APP_ENV=production`

### 4. GitHub Repository
*   Your code must be pushed to a GitHub repository that DigitalOcean can access.

---

## Step 1: Update the DigitalOcean App Spec (`app.yaml`)

The `app.yaml` file in the repo maps **both** the frontend and backend as separate services within a single DigitalOcean app. Provide the managed database connection strings as environment variables during deploy.

*(See the updated `app.yaml` file in the root directory)*

## Step 2: Deployment Process

1.  **Log into DigitalOcean:** Go to the App Platform dashboard.
2.  **Create App:** Click "Create App".
3.  **Connect GitHub:** Select your repository and the `main` branch.
4.  **Upload App Spec:** Instead of configuring components manually through the UI, click the **"Upload App Spec"** link (usually at the bottom or top right) and upload the `app.yaml` file.
5.  **Review Components:** DigitalOcean will automatically read the file and set up two services:
    *   `regime-api` (Python backend)
    *   `regime-web` (Node.js frontend)
6.  **Environment Variables:** DigitalOcean will prompt you to fill in the missing environment variables. You must provide:
    *   `DATABASE_URL` (DigitalOcean PostgreSQL runtime connection string)
    *   `DIRECT_URL` (DigitalOcean PostgreSQL direct connection string)
    *   `LLM_API_KEY` (Your AI key)
    *   `REGIME_CSRF_SECRET` (required in production)
    *   `REDIS_URL` (required for global burst limiting across instances)
    *   `REGIME_SESSION_SECURE=true`
    *   `REGIME_SESSION_SAMESITE=strict`
    *   `APP_ENV=production`

## Step 3: Post-Deployment Verification

1.  **CORS Setup:** Once the app is deployed, DigitalOcean will give you a public URL for your frontend (e.g., `https://regime-web-abcde.ondigitalocean.app`). 
    *   You **must** go to the `regime-api` component settings in DigitalOcean and set the `CORS_ORIGINS` environment variable to match this frontend URL exactly.
2.  **Database Initialization:** When the `regime-api` starts, `SQLModel.metadata.create_all()` will automatically run, creating the tables in your DigitalOcean database if they do not already exist.
3.  **Frontend API Link:** The `app.yaml` automatically sets `NEXT_PUBLIC_API_BASE_URL` in the frontend to point to the internal backend service URL, so they should talk to each other immediately.
4.  **Run Security Preflight:**
    *   `python backend/scripts/security_preflight.py`
    *   Resolve any failures before go-live.
5.  **Check Runtime Security Health Endpoint:**
    *   `GET /health/security`
    *   Ensure status is `ok` in production.

---

## Technologies to Consider Adding Later (Phase 2)

To make this a truly "bulletproof" production application later, you will need:

1.  **A Job Queue (Celery / Redis):**
    *   *Why:* Right now, if 500 users ask for an "AI Drilldown" at the exact same time, the FastAPI server will block and timeout. A background worker (like Celery) is required to handle slow LLM tasks asynchronously.
2.  **Cron Scheduling:**
    *   *Why:* For the "Outbound Delivery" (Emails/Discord), you need a system to run a script every morning at 8:00 AM EST to fetch the data and push the webhooks.
3.  **Sentry (Error Tracking):**
    *   *Why:* To instantly know if your model fails or the API goes down in production.
