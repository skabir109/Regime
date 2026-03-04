import json
import secrets
from datetime import datetime, timezone

from app.services.alerts import build_alerts_for_watchlist
from app.services.db import get_connection
from app.services.state import build_market_state_summary
from app.services.subscriptions import get_tier_config


def _require_desk_tier(connection, user_id: int) -> dict:
    row = connection.execute("SELECT tier, name FROM users WHERE id = ?", (user_id,)).fetchone()
    tier = get_tier_config(row["tier"] if row else None)
    if tier["tier"] != "desk":
        raise ValueError("Shared workspace features require the Desk tier.")
    return tier


def _workspace_row(connection, user_id: int):
    return connection.execute(
        """
        SELECT sw.id, sw.name, sw.invite_code, sw.owner_user_id, sw.created_at
        FROM shared_workspaces sw
        JOIN shared_workspace_members swm ON swm.workspace_id = sw.id
        WHERE swm.user_id = ?
        """,
        (user_id,),
    ).fetchone()


def _load_members(connection, workspace_id: int) -> list[dict]:
    rows = connection.execute(
        """
        SELECT u.id, u.name, u.email, u.tier, swm.role, swm.joined_at
        FROM shared_workspace_members swm
        JOIN users u ON u.id = swm.user_id
        WHERE swm.workspace_id = ?
        ORDER BY swm.joined_at ASC
        """,
        (workspace_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _load_watchlist(connection, workspace_id: int) -> list[dict]:
    rows = connection.execute(
        """
        SELECT symbol, label, added_at
        FROM shared_watchlist_items
        WHERE workspace_id = ?
        ORDER BY added_at DESC
        """,
        (workspace_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _load_notes(connection, workspace_id: int, limit: int = 10) -> list[dict]:
    rows = connection.execute(
        """
        SELECT swn.id, swn.content, swn.created_at, u.name AS author_name
        FROM shared_workspace_notes swn
        JOIN users u ON u.id = swn.author_user_id
        WHERE swn.workspace_id = ?
        ORDER BY swn.created_at DESC
        LIMIT ?
        """,
        (workspace_id, limit),
    ).fetchall()
    return [dict(row) for row in rows]


def _load_briefing_snapshots(connection, workspace_id: int, limit: int = 6) -> list[dict]:
    rows = connection.execute(
        """
        SELECT sbs.id, sbs.headline, sbs.overview, sbs.created_at, u.name AS author_name
        FROM shared_briefing_snapshots sbs
        JOIN users u ON u.id = sbs.author_user_id
        WHERE sbs.workspace_id = ?
        ORDER BY sbs.created_at DESC
        LIMIT ?
        """,
        (workspace_id, limit),
    ).fetchall()
    return [dict(row) for row in rows]


def get_shared_workspace(user_id: int, model=None, meta: dict | None = None) -> dict | None:
    with get_connection() as connection:
        workspace = _workspace_row(connection, user_id)
        if not workspace:
            return None
        watchlist = _load_watchlist(connection, workspace["id"])
        return {
            **dict(workspace),
            "members": _load_members(connection, workspace["id"]),
            "watchlist": watchlist,
            "notes": _load_notes(connection, workspace["id"]),
            "alerts": build_alerts_for_watchlist(model, meta, watchlist) if model is not None and meta is not None else [],
            "briefing_snapshots": _load_briefing_snapshots(connection, workspace["id"]),
        }


def create_shared_workspace(user_id: int, name: str) -> dict:
    cleaned_name = name.strip()
    if not cleaned_name:
        raise ValueError("Workspace name is required.")
    with get_connection() as connection:
        _require_desk_tier(connection, user_id)
        existing = _workspace_row(connection, user_id)
        if existing:
            raise ValueError("User is already a member of a shared workspace.")
        invite_code = secrets.token_hex(4).upper()
        created_at = datetime.now(timezone.utc).isoformat()
        cursor = connection.execute(
            """
            INSERT INTO shared_workspaces (owner_user_id, name, invite_code, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, cleaned_name, invite_code, created_at),
        )
        workspace_id = cursor.lastrowid
        connection.execute(
            """
            INSERT INTO shared_workspace_members (workspace_id, user_id, role, joined_at)
            VALUES (?, ?, 'owner', ?)
            """,
            (workspace_id, user_id, created_at),
        )
    return get_shared_workspace(user_id)


def join_shared_workspace(user_id: int, invite_code: str) -> dict:
    code = invite_code.strip().upper()
    if not code:
        raise ValueError("Invite code is required.")
    with get_connection() as connection:
        _require_desk_tier(connection, user_id)
        existing = _workspace_row(connection, user_id)
        if existing:
            raise ValueError("User is already a member of a shared workspace.")
        workspace = connection.execute(
            "SELECT id FROM shared_workspaces WHERE invite_code = ?",
            (code,),
        ).fetchone()
        if not workspace:
            raise ValueError("Invite code not found.")
        connection.execute(
            """
            INSERT INTO shared_workspace_members (workspace_id, user_id, role, joined_at)
            VALUES (?, ?, 'member', ?)
            """,
            (workspace["id"], user_id, datetime.now(timezone.utc).isoformat()),
        )
    return get_shared_workspace(user_id)


def add_shared_watchlist_item(user_id: int, symbol: str, label: str | None = None) -> dict:
    normalized = symbol.strip().upper()
    if not normalized:
        raise ValueError("Symbol is required.")
    with get_connection() as connection:
        workspace = _workspace_row(connection, user_id)
        if not workspace:
            raise ValueError("Join or create a shared workspace first.")
        connection.execute(
            """
            INSERT OR IGNORE INTO shared_watchlist_items (workspace_id, symbol, label, added_by_user_id, added_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                workspace["id"],
                normalized,
                label.strip() if label else normalized,
                user_id,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
    return get_shared_workspace(user_id)


def remove_shared_watchlist_item(user_id: int, symbol: str) -> dict:
    normalized = symbol.strip().upper()
    with get_connection() as connection:
        workspace = _workspace_row(connection, user_id)
        if not workspace:
            raise ValueError("Join or create a shared workspace first.")
        connection.execute(
            "DELETE FROM shared_watchlist_items WHERE workspace_id = ? AND symbol = ?",
            (workspace["id"], normalized),
        )
    return get_shared_workspace(user_id)


def add_shared_note(user_id: int, content: str) -> dict:
    cleaned = content.strip()
    if not cleaned:
        raise ValueError("Note content is required.")
    with get_connection() as connection:
        workspace = _workspace_row(connection, user_id)
        if not workspace:
            raise ValueError("Join or create a shared workspace first.")
        connection.execute(
            """
            INSERT INTO shared_workspace_notes (workspace_id, author_user_id, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (workspace["id"], user_id, cleaned[:500], datetime.now(timezone.utc).isoformat()),
        )
    return get_shared_workspace(user_id)


def save_shared_briefing_snapshot(user_id: int, model, meta: dict) -> dict:
    with get_connection() as connection:
        workspace = _workspace_row(connection, user_id)
        if not workspace:
            raise ValueError("Join or create a shared workspace first.")
        watchlist = _load_watchlist(connection, workspace["id"])
        state = build_market_state_summary(model, meta)
        alerts = build_alerts_for_watchlist(model, meta, watchlist)
        snapshot = {
            "headline": f'{workspace["name"]}: {state["regime"]} desk briefing',
            "overview": state["summary"],
            "top_alerts": alerts[:3],
            "watchlist": watchlist[:8],
        }
        connection.execute(
            """
            INSERT INTO shared_briefing_snapshots (workspace_id, author_user_id, headline, overview, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                workspace["id"],
                user_id,
                snapshot["headline"],
                snapshot["overview"],
                json.dumps(snapshot),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
    return get_shared_workspace(user_id, model, meta)
