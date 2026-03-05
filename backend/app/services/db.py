from sqlalchemy import inspect, text
from sqlmodel import SQLModel, create_engine, Session
from app.config import DATABASE_URL, DIRECT_URL


def is_postgres_configured() -> bool:
    return DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")

def get_engine(use_direct: bool = False):
    db_url = DIRECT_URL if use_direct and is_postgres_configured() else DATABASE_URL
    
    # Handle the pgbouncer=true case for SQLModel/SQLAlchemy
    connect_args = {}
    if "pgbouncer=true" in db_url.lower():
        connect_args = {"prepare_threshold": None}
        # Remove pgbouncer parameter from URL as psycopg2 doesn't recognize it
        if "?" in db_url:
            base_url, query = db_url.split("?", 1)
            params = [p for p in query.split("&") if not p.lower().startswith("pgbouncer=")]
            db_url = f"{base_url}?{'&'.join(params)}" if params else base_url
        
    return create_engine(db_url, connect_args=connect_args)

def get_session():
    engine = get_engine()
    with Session(engine) as session:
        yield session

def init_db():
    # Use DIRECT_URL for schema creation to bypass pgbouncer issues
    engine = get_engine(use_direct=True)
    SQLModel.metadata.create_all(engine)
    _run_lightweight_migrations(engine)


def _run_lightweight_migrations(engine) -> None:
    """
    Small, idempotent startup migrations for local/dev environments.
    Uses direct ALTER TABLE checks so existing DBs do not break when columns are added.
    """
    inspector = inspect(engine)
    if not inspector.has_table("users"):
        return

    existing = {column["name"] for column in inspector.get_columns("users")}
    statements: list[str] = []
    dialect = engine.dialect.name

    if "failed_login_attempts" not in existing:
        statements.append(
            "ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0"
        )

    if "locked_until" not in existing:
        if dialect == "postgresql":
            statements.append("ALTER TABLE users ADD COLUMN locked_until TIMESTAMPTZ NULL")
        else:
            statements.append("ALTER TABLE users ADD COLUMN locked_until DATETIME NULL")

    if statements:
        with engine.begin() as connection:
            for stmt in statements:
                connection.execute(text(stmt))

    # delivery_preferences table migrations
    if not inspector.has_table("delivery_preferences"):
        return

    delivery_existing = {column["name"] for column in inspector.get_columns("delivery_preferences")}
    delivery_statements: list[str] = []
    if "slack_enabled" not in delivery_existing:
        delivery_statements.append(
            "ALTER TABLE delivery_preferences ADD COLUMN slack_enabled BOOLEAN NOT NULL DEFAULT FALSE"
        )
    if "slack_webhook_url" not in delivery_existing:
        delivery_statements.append(
            "ALTER TABLE delivery_preferences ADD COLUMN slack_webhook_url VARCHAR(512) NULL"
        )
    if "discord_enabled" not in delivery_existing:
        delivery_statements.append(
            "ALTER TABLE delivery_preferences ADD COLUMN discord_enabled BOOLEAN NOT NULL DEFAULT FALSE"
        )
    if "discord_webhook_url" not in delivery_existing:
        delivery_statements.append(
            "ALTER TABLE delivery_preferences ADD COLUMN discord_webhook_url VARCHAR(512) NULL"
        )
    if "timezone" not in delivery_existing:
        delivery_statements.append(
            "ALTER TABLE delivery_preferences ADD COLUMN timezone VARCHAR(64) NOT NULL DEFAULT 'local'"
        )

    if not delivery_statements:
        return

    with engine.begin() as connection:
        for stmt in delivery_statements:
            connection.execute(text(stmt))
