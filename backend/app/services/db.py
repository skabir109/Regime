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

