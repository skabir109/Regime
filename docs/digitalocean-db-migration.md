# DigitalOcean Database Migration

This project already uses SQLModel against PostgreSQL. Migrating from Supabase to DigitalOcean is therefore an infrastructure cutover, not an application rewrite.

## Required Connection Strings

Prepare these values before cutover:

- `SOURCE_DATABASE_URL`: the current Supabase PostgreSQL connection string you want to copy from.
- `TARGET_DATABASE_URL`: the new DigitalOcean Managed PostgreSQL connection string you want to copy into.

If you prefer, the migration script will also use `DIGITALOCEAN_DATABASE_URL`, `DIRECT_URL`, or `DATABASE_URL` as the target in that order.

## One-Time Migration

From the repo root:

```bash
cd backend
pip install -r requirements.txt
cd ..

export SOURCE_DATABASE_URL="postgresql://..."
export TARGET_DATABASE_URL="postgresql://..."
python3 migrate_to_digitalocean_postgres.py
```

What the script does:

- initializes the target schema from the backend SQLModel models
- runs lightweight startup migrations on the target database
- truncates target public tables
- copies all overlapping public tables from source to target
- resets target sequences after explicit ID inserts

## DigitalOcean Runtime Configuration

After the copy finishes, point the deployed backend at DigitalOcean instead of Supabase:

- `DATABASE_URL`: DigitalOcean pooled or primary connection string used by the app
- `DIRECT_URL`: DigitalOcean direct connection string used for schema creation and startup migrations

Recommended production settings:

- `APP_ENV=production`
- `REGIME_SESSION_SECURE=true`
- `REGIME_SESSION_SAMESITE=strict`
- `REGIME_CSRF_SECRET=<long-random-secret>`
- `REDIS_URL=<shared-redis-url>`

## Verification

Run these checks after cutover:

```bash
cd backend
python3 -m pytest tests/test_api_protection.py tests/test_csrf_service.py
```

Then validate the deployed app:

- `GET /health`
- `GET /health/security`
- authentication flow
- watchlist read/write
- briefing history read/write

## Cutover Notes

- Stop writes to Supabase before the final copy to avoid drift during migration.
- Keep the old Supabase connection string available until production verification is complete.
- The migration script truncates target tables before copy, so do not run it against a live target with data you need to keep.
