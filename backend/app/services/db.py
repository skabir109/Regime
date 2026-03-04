import sqlite3
from urllib.parse import urlparse

from app.config import DATABASE_URL, DIRECT_URL, DB_PATH


def is_postgres_configured() -> bool:
    return DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")

class PostgresRow:
    def __init__(self, cursor, row):
        self._row = row
        self._keys = [desc[0] for desc in cursor.description]
    def __getitem__(self, key):
        if isinstance(key, int):
            return self._row[key]
        try:
            return self._row[self._keys.index(key)]
        except ValueError:
            raise KeyError(key)
    def keys(self):
        return self._keys

class PostgresCursorWrapper:
    def __init__(self, cursor):
        self.cursor = cursor
    def execute(self, sql, params=()):
        sql = sql.replace("?", "%s")
        self.cursor.execute(sql, params)
        return self
    def fetchone(self):
        row = self.cursor.fetchone()
        return PostgresRow(self.cursor, row) if row else None
    def fetchall(self):
        return [PostgresRow(self.cursor, row) for row in self.cursor.fetchall()]
    @property
    def lastrowid(self):
        # Extremely hacky approximation for lastrowid if not using RETURNING
        try:
            self.cursor.execute("SELECT LASTVAL()")
            return self.cursor.fetchone()[0]
        except:
            return None

class PostgresConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn
    def execute(self, sql, params=()):
        cursor = self.conn.cursor()
        sql = sql.replace("?", "%s")
        cursor.execute(sql, params)
        return PostgresCursorWrapper(cursor)
    def executescript(self, sql):
        cursor = self.conn.cursor()
        for statement in sql.split(";"):
            if statement.strip():
                cursor.execute(statement)
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.conn.close()

def get_connection(use_direct: bool = False):
    db_url = DIRECT_URL if use_direct and is_postgres_configured() else DATABASE_URL
    if is_postgres_configured():
        import psycopg2
        url = urlparse(db_url)
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        return PostgresConnectionWrapper(conn)
    else:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(DB_PATH)
        connection.row_factory = sqlite3.Row
        return connection

def init_db():
    schema = """
        CREATE TABLE IF NOT EXISTS users (
            id {PK_TYPE},
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
            id {PK_TYPE},
            user_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS watchlist_items (
            id {PK_TYPE},
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            label TEXT NOT NULL,
            added_at TEXT NOT NULL,
            UNIQUE(user_id, symbol),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS briefing_history (
            id {PK_TYPE},
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
            id {PK_TYPE},
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
            id {PK_TYPE},
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
            id {PK_TYPE},
            workspace_id INTEGER NOT NULL,
            author_user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (workspace_id) REFERENCES shared_workspaces (id) ON DELETE CASCADE,
            FOREIGN KEY (author_user_id) REFERENCES users (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS shared_briefing_snapshots (
            id {PK_TYPE},
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
            id {PK_TYPE},
            event_type TEXT NOT NULL,
            user_id INTEGER,
            details TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
        );
    """
    
    pk_type = "SERIAL PRIMARY KEY" if is_postgres_configured() else "INTEGER PRIMARY KEY AUTOINCREMENT"
    schema = schema.replace("{PK_TYPE}", pk_type)
    
    with get_connection(use_direct=True) as connection:
        connection.executescript(schema)
        
        # Add columns if sqlite, postgres would need its own migration but we assume clean slate or existing for now.
        if not is_postgres_configured():
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(users)").fetchall()
            }
            if "tier" not in columns:
                connection.execute("ALTER TABLE users ADD COLUMN tier TEXT NOT NULL DEFAULT 'free'")
            if "is_verified" not in columns:
                connection.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER NOT NULL DEFAULT 0")
            if "verification_token" not in columns:
                connection.execute("ALTER TABLE users ADD COLUMN verification_token TEXT")
            if "reset_token" not in columns:
                connection.execute("ALTER TABLE users ADD COLUMN reset_token TEXT")
            if "reset_token_expires_at" not in columns:
                connection.execute("ALTER TABLE users ADD COLUMN reset_token_expires_at TEXT")
