import os
from urllib.parse import urlparse
import psycopg2

def load_env(path):
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value.strip("\"'")

load_env(".env")
direct_url = os.getenv("DIRECT_URL")

if not direct_url:
    print("DIRECT_URL not found in .env")
    exit(1)

print(f"Connecting to: {direct_url.split('@')[-1]}")
url = urlparse(direct_url)
conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

schema = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        tier TEXT NOT NULL DEFAULT 'free',
        created_at TEXT NOT NULL,
        is_verified INTEGER NOT NULL DEFAULT 0,
        verification_token TEXT,
        reset_token TEXT,
        reset_token_expires_at TEXT
    );

    CREATE TABLE IF NOT EXISTS sessions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        token_hash TEXT NOT NULL UNIQUE,
        expires_at TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS watchlist_items (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        label TEXT NOT NULL,
        added_at TEXT NOT NULL,
        UNIQUE(user_id, symbol),
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS briefing_history (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        briefing_date TEXT NOT NULL,
        headline TEXT NOT NULL,
        overview TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(user_id, briefing_date),
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS delivery_preferences (
        user_id INTEGER PRIMARY KEY,
        email_enabled INTEGER NOT NULL DEFAULT 0,
        webhook_enabled INTEGER NOT NULL DEFAULT 0,
        webhook_url TEXT,
        cadence TEXT NOT NULL DEFAULT 'premarket',
        updated_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS shared_workspaces (
        id SERIAL PRIMARY KEY,
        owner_user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        invite_code TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL,
        FOREIGN KEY (owner_user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS shared_workspace_members (
        workspace_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL UNIQUE,
        role TEXT NOT NULL,
        joined_at TEXT NOT NULL,
        PRIMARY KEY (workspace_id, user_id),
        FOREIGN KEY (workspace_id) REFERENCES shared_workspaces (id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS shared_watchlist_items (
        id SERIAL PRIMARY KEY,
        workspace_id INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        label TEXT NOT NULL,
        added_by_user_id INTEGER NOT NULL,
        added_at TEXT NOT NULL,
        UNIQUE(workspace_id, symbol),
        FOREIGN KEY (workspace_id) REFERENCES shared_workspaces (id) ON DELETE CASCADE,
        FOREIGN KEY (added_by_user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS shared_workspace_notes (
        id SERIAL PRIMARY KEY,
        workspace_id INTEGER NOT NULL,
        author_user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (workspace_id) REFERENCES shared_workspaces (id) ON DELETE CASCADE,
        FOREIGN KEY (author_user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS shared_briefing_snapshots (
        id SERIAL PRIMARY KEY,
        workspace_id INTEGER NOT NULL,
        author_user_id INTEGER NOT NULL,
        headline TEXT NOT NULL,
        overview TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (workspace_id) REFERENCES shared_workspaces (id) ON DELETE CASCADE,
        FOREIGN KEY (author_user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id SERIAL PRIMARY KEY,
        event_type TEXT NOT NULL,
        user_id INTEGER,
        details TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
    );
"""

with conn.cursor() as cur:
    cur.execute(schema)
    conn.commit()
    print("Successfully pushed tables to Supabase.")
    
    cur.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'")
    print("Tables in public schema:", [row[0] for row in cur.fetchall()])

conn.close()
