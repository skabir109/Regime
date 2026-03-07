from sqlalchemy import inspect, text
from sqlmodel import SQLModel, create_engine, Session
from app.config import DATABASE_URL, DIRECT_URL


def is_postgres_configured() -> bool:
    return (
        DATABASE_URL.startswith("postgresql://")
        or DATABASE_URL.startswith("postgres://")
        or DATABASE_URL.startswith("postgresql+psycopg://")
    )


def _normalize_postgres_driver(db_url: str) -> str:
    if db_url.startswith("postgres://"):
        return "postgresql+psycopg://" + db_url[len("postgres://"):]
    if db_url.startswith("postgresql://"):
        return "postgresql+psycopg://" + db_url[len("postgresql://"):]
    return db_url

def get_engine(use_direct: bool = False):
    db_url = DIRECT_URL if use_direct and is_postgres_configured() else DATABASE_URL
    db_url = _normalize_postgres_driver(db_url)
    
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
    user_columns = {column["name"]: column for column in inspector.get_columns("users")}
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

    if "stripe_customer_id" not in existing:
        statements.append("ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(128) NULL")

    if "stripe_subscription_id" not in existing:
        statements.append("ALTER TABLE users ADD COLUMN stripe_subscription_id VARCHAR(128) NULL")

    if "tier_selection_required" not in existing:
        if dialect == "postgresql":
            statements.append(
                "ALTER TABLE users ADD COLUMN tier_selection_required BOOLEAN NOT NULL DEFAULT FALSE"
            )
        else:
            statements.append(
                "ALTER TABLE users ADD COLUMN tier_selection_required BOOLEAN NOT NULL DEFAULT 0"
            )

    # Legacy schema compatibility: older bootstrap scripts created this as INTEGER.
    if dialect == "postgresql" and "is_verified" in user_columns:
        is_verified_type = str(user_columns["is_verified"]["type"]).lower()
        if "bool" not in is_verified_type:
            statements.extend(
                [
                    "ALTER TABLE users ALTER COLUMN is_verified DROP DEFAULT",
                    "ALTER TABLE users ALTER COLUMN is_verified TYPE BOOLEAN USING (is_verified <> 0)",
                    "ALTER TABLE users ALTER COLUMN is_verified SET DEFAULT FALSE",
                ]
            )

    if statements:
        with engine.begin() as connection:
            for stmt in statements:
                connection.execute(text(stmt))

    # delivery_preferences table migrations
    if not inspector.has_table("delivery_preferences"):
        return

    delivery_columns = {column["name"]: column for column in inspector.get_columns("delivery_preferences")}
    delivery_existing = set(delivery_columns.keys())
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

    # Legacy schema compatibility: older bootstrap scripts created boolean flags as INTEGER.
    if dialect == "postgresql":
        for flag_column in ("email_enabled", "webhook_enabled", "slack_enabled", "discord_enabled"):
            if flag_column not in delivery_columns:
                continue
            flag_type = str(delivery_columns[flag_column]["type"]).lower()
            if "bool" in flag_type:
                continue
            delivery_statements.extend(
                [
                    f"ALTER TABLE delivery_preferences ALTER COLUMN {flag_column} DROP DEFAULT",
                    f"ALTER TABLE delivery_preferences ALTER COLUMN {flag_column} TYPE BOOLEAN USING ({flag_column} <> 0)",
                    f"ALTER TABLE delivery_preferences ALTER COLUMN {flag_column} SET DEFAULT FALSE",
                ]
            )

    if not delivery_statements:
        return

    with engine.begin() as connection:
        for stmt in delivery_statements:
            connection.execute(text(stmt))
