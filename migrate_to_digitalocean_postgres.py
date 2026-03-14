import os
import sys
from pathlib import Path
from typing import Iterable

import psycopg

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional for minimal environments
    def load_dotenv(*_args, **_kwargs):
        return False


ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

# Parent tables first so inserts satisfy foreign keys.
TABLE_COPY_ORDER = [
    "users",
    "sessions",
    "watchlist_items",
    "briefing_history",
    "delivery_preferences",
    "audit_logs",
    "api_usage_counters",
    "shared_workspaces",
    "shared_workspace_members",
    "shared_watchlist_items",
    "shared_workspace_notes",
    "shared_briefing_snapshots",
]


def _load_env() -> None:
    load_dotenv(ROOT_DIR / ".env")
    load_dotenv(BACKEND_DIR / ".env")


def _normalize_sqlalchemy_url(db_url: str) -> str:
    if db_url.startswith("postgres://"):
        return "postgresql+psycopg://" + db_url[len("postgres://"):]
    if db_url.startswith("postgresql://"):
        return "postgresql+psycopg://" + db_url[len("postgresql://"):]
    return db_url


def _normalize_psycopg_url(db_url: str) -> str:
    if db_url.startswith("postgresql+psycopg://"):
        return "postgresql://" + db_url[len("postgresql+psycopg://"):]
    return db_url


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _fetch_public_tables(conn: psycopg.Connection) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT tablename
            FROM pg_catalog.pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
            """
        )
        return [row[0] for row in cur.fetchall()]


def _ordered_tables(source_tables: Iterable[str], target_tables: Iterable[str]) -> list[str]:
    available = set(source_tables) & set(target_tables)
    ordered = [table for table in TABLE_COPY_ORDER if table in available]
    ordered.extend(sorted(table for table in available if table not in ordered))
    return ordered


def _fetch_columns(conn: psycopg.Connection, table_name: str) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
            """,
            (table_name,),
        )
        return [row[0] for row in cur.fetchall()]


def _truncate_tables(conn: psycopg.Connection, tables: list[str]) -> None:
    if not tables:
        return
    quoted_tables = ", ".join(f'public.{_quote_ident(table)}' for table in tables)
    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE TABLE {quoted_tables} RESTART IDENTITY CASCADE")


def _copy_table(
    source_conn: psycopg.Connection,
    target_conn: psycopg.Connection,
    table_name: str,
    batch_size: int = 500,
) -> int:
    columns = _fetch_columns(source_conn, table_name)
    if not columns:
        return 0

    quoted_columns = ", ".join(_quote_ident(column) for column in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    select_sql = f'SELECT {quoted_columns} FROM public.{_quote_ident(table_name)}'
    insert_sql = (
        f'INSERT INTO public.{_quote_ident(table_name)} ({quoted_columns}) '
        f"VALUES ({placeholders})"
    )

    copied_rows = 0
    with source_conn.cursor() as source_cur, target_conn.cursor() as target_cur:
        source_cur.execute(select_sql)
        while True:
            rows = source_cur.fetchmany(batch_size)
            if not rows:
                break
            target_cur.executemany(insert_sql, rows)
            copied_rows += len(rows)

    return copied_rows


def _reset_sequences(conn: psycopg.Connection, tables: Iterable[str]) -> None:
    with conn.cursor() as cur:
        for table_name in tables:
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = %s
                  AND (
                    column_default LIKE 'nextval%%'
                    OR is_identity = 'YES'
                  )
                ORDER BY ordinal_position
                """,
                (table_name,),
            )
            for (column_name,) in cur.fetchall():
                cur.execute(
                    f"""
                    SELECT setval(
                        pg_get_serial_sequence(%s, %s),
                        COALESCE(MAX({_quote_ident(column_name)}), 1),
                        MAX({_quote_ident(column_name)}) IS NOT NULL
                    )
                    FROM public.{_quote_ident(table_name)}
                    """,
                    (f"public.{table_name}", column_name),
                )


def _prepare_target_schema(target_url: str) -> None:
    os.environ["DATABASE_URL"] = target_url
    os.environ["DIRECT_URL"] = target_url

    sys.path.insert(0, str(BACKEND_DIR))
    from app.services.db import init_db

    init_db()


def main() -> int:
    _load_env()

    source_url = _normalize_psycopg_url(_require_env("SOURCE_DATABASE_URL"))
    target_url = _normalize_psycopg_url(
        os.getenv("TARGET_DATABASE_URL", "").strip()
        or os.getenv("DIGITALOCEAN_DATABASE_URL", "").strip()
        or os.getenv("DIRECT_URL", "").strip()
        or _require_env("DATABASE_URL")
    )

    print("Preparing DigitalOcean PostgreSQL schema from SQLModel metadata...")
    _prepare_target_schema(_normalize_sqlalchemy_url(target_url))

    with psycopg.connect(source_url) as source_conn, psycopg.connect(target_url) as target_conn:
        source_tables = _fetch_public_tables(source_conn)
        target_tables = _fetch_public_tables(target_conn)
        tables = _ordered_tables(source_tables, target_tables)

        if not tables:
            print("No overlapping public tables found between source and target databases.")
            return 1

        print(f"Copying {len(tables)} public tables into DigitalOcean PostgreSQL...")
        _truncate_tables(target_conn, tables)

        copied_summary: list[tuple[str, int]] = []
        for table_name in tables:
            copied_rows = _copy_table(source_conn, target_conn, table_name)
            copied_summary.append((table_name, copied_rows))
            print(f"  {table_name}: {copied_rows} rows")

        _reset_sequences(target_conn, tables)
        target_conn.commit()

    print("Database migration complete.")
    print("Source: SOURCE_DATABASE_URL")
    print("Target: TARGET_DATABASE_URL or DIGITALOCEAN_DATABASE_URL or DIRECT_URL/DATABASE_URL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
