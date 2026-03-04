import json
import secrets
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select
from app.services.db import get_engine
from app.schemas import (
    SharedWorkspaceDB,
    SharedWorkspaceMemberDB,
    SharedWatchlistItemDB,
    SharedWorkspaceNoteDB,
    SharedBriefingSnapshotDB,
    User,
    WatchlistItemDB
)
from app.services.subscriptions import get_tier_config
from app.services.briefing import build_premarket_briefing


def _require_desk_tier(session: Session, user_id: int) -> dict:
    user = session.get(User, user_id)
    tier = get_tier_config(user.tier if user else None)
    if tier["tier"] != "desk":
        raise ValueError("Shared workspace features require the Desk tier.")
    return tier


def _load_members(session: Session, workspace_id: int) -> list[dict]:
    statement = select(SharedWorkspaceMemberDB, User).join(User).where(SharedWorkspaceMemberDB.workspace_id == workspace_id)
    results = session.exec(statement).all()
    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "tier": user.tier,
            "role": member.role,
            "joined_at": member.joined_at.isoformat() if isinstance(member.joined_at, datetime) else member.joined_at,
        }
        for member, user in results
    ]


def _load_watchlist(session: Session, workspace_id: int) -> list[dict]:
    statement = select(SharedWatchlistItemDB).where(SharedWatchlistItemDB.workspace_id == workspace_id).order_by(SharedWatchlistItemDB.added_at.desc())
    items = session.exec(statement).all()
    return [
        {
            "symbol": item.symbol,
            "label": item.label,
            "added_at": item.added_at.isoformat() if isinstance(item.added_at, datetime) else item.added_at,
        }
        for item in items
    ]


def _load_notes(session: Session, workspace_id: int, limit: int = 10) -> list[dict]:
    statement = select(SharedWorkspaceNoteDB, User).join(User, SharedWorkspaceNoteDB.author_user_id == User.id).where(SharedWorkspaceNoteDB.workspace_id == workspace_id).order_by(SharedWorkspaceNoteDB.created_at.desc()).limit(limit)
    results = session.exec(statement).all()
    return [
        {
            "id": note.id,
            "content": note.content,
            "created_at": note.created_at.isoformat() if isinstance(note.created_at, datetime) else note.created_at,
            "author_name": user.name,
        }
        for note, user in results
    ]

def _load_briefing_snapshots(session: Session, workspace_id: int, limit: int = 5) -> list[dict]:
    statement = select(SharedBriefingSnapshotDB, User).join(User, SharedBriefingSnapshotDB.author_user_id == User.id).where(SharedBriefingSnapshotDB.workspace_id == workspace_id).order_by(SharedBriefingSnapshotDB.created_at.desc()).limit(limit)
    results = session.exec(statement).all()
    return [
        {
            "id": snapshot.id,
            "headline": snapshot.headline,
            "overview": snapshot.overview,
            "created_at": snapshot.created_at.isoformat() if isinstance(snapshot.created_at, datetime) else snapshot.created_at,
            "author_name": user.name,
        }
        for snapshot, user in results
    ]


def get_shared_workspace(user_id: int, model=None, meta: Optional[dict] = None) -> dict | None:
    with Session(get_engine()) as session:
        member_record = session.exec(select(SharedWorkspaceMemberDB).where(SharedWorkspaceMemberDB.user_id == user_id)).first()
        if not member_record:
            return None
            
        workspace = session.get(SharedWorkspaceDB, member_record.workspace_id)
        if not workspace:
            return None
            
        return {
            "id": workspace.id,
            "name": workspace.name,
            "invite_code": workspace.invite_code,
            "owner_user_id": workspace.owner_user_id,
            "created_at": workspace.created_at.isoformat() if isinstance(workspace.created_at, datetime) else workspace.created_at,
            "members": _load_members(session, workspace.id),
            "watchlist": _load_watchlist(session, workspace.id),
            "notes": _load_notes(session, workspace.id),
            "briefing_snapshots": _load_briefing_snapshots(session, workspace.id)
        }


def create_shared_workspace(user_id: int, name: str) -> dict:
    cleaned_name = name.strip()
    if not cleaned_name:
        raise ValueError("Workspace name is required.")
        
    with Session(get_engine()) as session:
        _require_desk_tier(session, user_id)
        
        existing = session.exec(select(SharedWorkspaceMemberDB).where(SharedWorkspaceMemberDB.user_id == user_id)).first()
        if existing:
            raise ValueError("User is already a member of a shared workspace.")
            
        invite_code = secrets.token_hex(4).upper()
        now = datetime.now(timezone.utc)
        
        workspace = SharedWorkspaceDB(
            owner_user_id=user_id,
            name=cleaned_name,
            invite_code=invite_code,
            created_at=now
        )
        session.add(workspace)
        session.commit()
        session.refresh(workspace)
        
        member = SharedWorkspaceMemberDB(
            workspace_id=workspace.id,
            user_id=user_id,
            role="owner",
            joined_at=now
        )
        session.add(member)
        session.commit()
        
    return get_shared_workspace(user_id)


def join_shared_workspace(user_id: int, invite_code: str) -> dict:
    code = invite_code.strip().upper()
    if not code:
        raise ValueError("Invite code is required.")
        
    with Session(get_engine()) as session:
        _require_desk_tier(session, user_id)
        
        existing = session.exec(select(SharedWorkspaceMemberDB).where(SharedWorkspaceMemberDB.user_id == user_id)).first()
        if existing:
            raise ValueError("User is already a member of a shared workspace.")
            
        workspace = session.exec(select(SharedWorkspaceDB).where(SharedWorkspaceDB.invite_code == code)).first()
        if not workspace:
            raise ValueError("Invite code not found.")
            
        member = SharedWorkspaceMemberDB(
            workspace_id=workspace.id,
            user_id=user_id,
            role="member",
            joined_at=datetime.now(timezone.utc)
        )
        session.add(member)
        session.commit()
        
    return get_shared_workspace(user_id)


def add_shared_watchlist_item(user_id: int, symbol: str, label: str | None = None) -> dict:
    normalized = symbol.strip().upper()
    if not normalized:
        raise ValueError("Symbol is required.")
        
    with Session(get_engine()) as session:
        member_record = session.exec(select(SharedWorkspaceMemberDB).where(SharedWorkspaceMemberDB.user_id == user_id)).first()
        if not member_record:
            raise ValueError("Join or create a shared workspace first.")
            
        existing = session.exec(select(SharedWatchlistItemDB).where(
            SharedWatchlistItemDB.workspace_id == member_record.workspace_id,
            SharedWatchlistItemDB.symbol == normalized
        )).first()
        
        if not existing:
            item = SharedWatchlistItemDB(
                workspace_id=member_record.workspace_id,
                symbol=normalized,
                label=(label or normalized).strip(),
                added_by_user_id=user_id,
                added_at=datetime.now(timezone.utc)
            )
            session.add(item)
            session.commit()
            
    return get_shared_workspace(user_id)


def remove_shared_watchlist_item(user_id: int, symbol: str) -> dict:
    normalized = symbol.strip().upper()
    with Session(get_engine()) as session:
        member_record = session.exec(select(SharedWorkspaceMemberDB).where(SharedWorkspaceMemberDB.user_id == user_id)).first()
        if not member_record:
            raise ValueError("Join or create a shared workspace first.")
            
        item = session.exec(select(SharedWatchlistItemDB).where(
            SharedWatchlistItemDB.workspace_id == member_record.workspace_id,
            SharedWatchlistItemDB.symbol == normalized
        )).first()
        
        if item:
            session.delete(item)
            session.commit()
            
    return get_shared_workspace(user_id)


def add_shared_note(user_id: int, content: str) -> dict:
    cleaned = content.strip()
    if not cleaned:
        raise ValueError("Note content is required.")
        
    with Session(get_engine()) as session:
        member_record = session.exec(select(SharedWorkspaceMemberDB).where(SharedWorkspaceMemberDB.user_id == user_id)).first()
        if not member_record:
            raise ValueError("Join or create a shared workspace first.")
            
        note = SharedWorkspaceNoteDB(
            workspace_id=member_record.workspace_id,
            author_user_id=user_id,
            content=cleaned[:500],
            created_at=datetime.now(timezone.utc)
        )
        session.add(note)
        session.commit()
        
    return get_shared_workspace(user_id)

def save_shared_briefing_snapshot(user_id: int, model, meta: dict) -> dict:
    with Session(get_engine()) as session:
        member_record = session.exec(select(SharedWorkspaceMemberDB).where(SharedWorkspaceMemberDB.user_id == user_id)).first()
        if not member_record:
            raise ValueError("Join or create a shared workspace first.")
            
        briefing = build_premarket_briefing(model, meta, user_id)
        
        snapshot = SharedBriefingSnapshotDB(
            workspace_id=member_record.workspace_id,
            author_user_id=user_id,
            headline=briefing["headline"],
            overview=briefing["overview"],
            payload_json=json.dumps(briefing),
            created_at=datetime.now(timezone.utc)
        )
        session.add(snapshot)
        session.commit()
        
    return get_shared_workspace(user_id)
