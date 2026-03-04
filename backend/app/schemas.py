from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SQLField, Relationship


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = SQLField(default=None, primary_key=True)
    email: str = SQLField(unique=True, index=True)
    name: str
    password_hash: str
    tier: str = SQLField(default="free")
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    is_verified: bool = SQLField(default=False)
    verification_token: Optional[str] = None
    reset_token: Optional[str] = None
    reset_token_expires_at: Optional[datetime] = None

    sessions: List["DBSession"] = Relationship(back_populates="user")
    watchlist_items: List["WatchlistItemDB"] = Relationship(back_populates="user")
    delivery_preferences: Optional["DeliveryPreferencesDB"] = Relationship(back_populates="user")


class DBSession(SQLModel, table=True):
    __tablename__ = "sessions"
    id: Optional[int] = SQLField(default=None, primary_key=True)
    user_id: int = SQLField(foreign_key="users.id", ondelete="CASCADE")
    token_hash: str = SQLField(unique=True, index=True)
    expires_at: datetime
    created_at: datetime = SQLField(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="sessions")


class WatchlistItemDB(SQLModel, table=True):
    __tablename__ = "watchlist_items"
    id: Optional[int] = SQLField(default=None, primary_key=True)
    user_id: int = SQLField(foreign_key="users.id", ondelete="CASCADE")
    symbol: str
    label: str
    added_at: datetime = SQLField(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="watchlist_items")


class BriefingHistoryDB(SQLModel, table=True):
    __tablename__ = "briefing_history"
    id: Optional[int] = SQLField(default=None, primary_key=True)
    user_id: int = SQLField(foreign_key="users.id", ondelete="CASCADE")
    briefing_date: str
    headline: str
    overview: str
    payload_json: str
    created_at: datetime = SQLField(default_factory=datetime.utcnow)


class DeliveryPreferencesDB(SQLModel, table=True):
    __tablename__ = "delivery_preferences"
    user_id: int = SQLField(primary_key=True, foreign_key="users.id", ondelete="CASCADE")
    email_enabled: bool = SQLField(default=False)
    webhook_enabled: bool = SQLField(default=False)
    webhook_url: Optional[str] = None
    cadence: str = SQLField(default="premarket")
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="delivery_preferences")


class AuditLogDB(SQLModel, table=True):
    __tablename__ = "audit_logs"
    id: Optional[int] = SQLField(default=None, primary_key=True)
    event_type: str
    user_id: Optional[int] = SQLField(default=None, foreign_key="users.id", ondelete="SET NULL")
    details: str
    created_at: datetime = SQLField(default_factory=datetime.utcnow)


class SharedWorkspaceDB(SQLModel, table=True):
    __tablename__ = "shared_workspaces"
    id: Optional[int] = SQLField(default=None, primary_key=True)
    owner_user_id: int = SQLField(foreign_key="users.id", ondelete="CASCADE")
    name: str
    invite_code: str = SQLField(unique=True)
    created_at: datetime = SQLField(default_factory=datetime.utcnow)


class SharedWorkspaceMemberDB(SQLModel, table=True):
    __tablename__ = "shared_workspace_members"
    workspace_id: int = SQLField(primary_key=True, foreign_key="shared_workspaces.id", ondelete="CASCADE")
    user_id: int = SQLField(primary_key=True, foreign_key="users.id", ondelete="CASCADE")
    role: str
    joined_at: datetime = SQLField(default_factory=datetime.utcnow)


class SharedWatchlistItemDB(SQLModel, table=True):
    __tablename__ = "shared_watchlist_items"
    id: Optional[int] = SQLField(default=None, primary_key=True)
    workspace_id: int = SQLField(foreign_key="shared_workspaces.id", ondelete="CASCADE")
    symbol: str
    label: str
    added_by_user_id: int = SQLField(foreign_key="users.id", ondelete="CASCADE")
    added_at: datetime = SQLField(default_factory=datetime.utcnow)


class SharedWorkspaceNoteDB(SQLModel, table=True):
    __tablename__ = "shared_workspace_notes"
    id: Optional[int] = SQLField(default=None, primary_key=True)
    workspace_id: int = SQLField(foreign_key="shared_workspaces.id", ondelete="CASCADE")
    author_user_id: int = SQLField(foreign_key="users.id", ondelete="CASCADE")
    content: str
    created_at: datetime = SQLField(default_factory=datetime.utcnow)


class SharedBriefingSnapshotDB(SQLModel, table=True):
    __tablename__ = "shared_briefing_snapshots"
    id: Optional[int] = SQLField(default=None, primary_key=True)
    workspace_id: int = SQLField(foreign_key="shared_workspaces.id", ondelete="CASCADE")
    author_user_id: int = SQLField(foreign_key="users.id", ondelete="CASCADE")
    headline: str
    overview: str
    payload_json: str
    created_at: datetime = SQLField(default_factory=datetime.utcnow)


class PredictRequest(BaseModel):
    features: dict[str, float] | None = Field(
        default=None,
        description="Optional raw feature payload matching the trained model schema.",
    )


class PredictResponse(BaseModel):
    regime: str
    confidence: float
    probabilities: dict[str, float]
    timestamp: datetime
    source: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    data_available: bool


class MetadataResponse(BaseModel):
    classes: list[str]
    features: list[str]
    thresholds: dict[str, float]
    training: dict[str, object] = {}
    feature_importance: dict[str, float] = {}


class MarketAssetSnapshot(BaseModel):
    symbol: str
    label: str
    price: float
    change_1d: float
    change_5d: float | None = None


class RegimeHistoryPoint(BaseModel):
    date: str
    regime: str
    confidence: float


class NewsItem(BaseModel):
    title: str
    source: str
    published_at: str
    url: str
    summary: str | None = None
    tags: list[str] = []


class WorldAffairsEvent(BaseModel):
    title: str
    source: str
    published_at: str
    url: str
    summary: str | None = None
    theme: str
    region: str
    urgency: str
    severity: str
    sentiment: str = "Neutral"
    directional_bias: str = "Mixed"
    affected_assets: list[str] = []
    market_view: list[str] = []
    second_order_effects: list[str] = []
    why_it_matters: str


class WorldAffairsBriefing(BaseModel):
    headline: str
    summary: str
    key_themes: list[str]
    market_implications: list[str]
    watchpoints: list[str]


class NarrativeTimelineItem(BaseModel):
    title: str
    theme: str
    region: str
    published_at: str
    event_summary: str
    market_reaction: str
    follow_through: str
    current_implication: str
    affected_assets: list[str] = []


class WorldAffairsRegionSummary(BaseModel):
    region: str
    theme_count: int
    active_themes: list[str] = []
    affected_assets: list[str] = []
    headline: str


class HeadlineReference(BaseModel):
    title: str
    source: str
    url: str


class WatchlistNewsItem(BaseModel):
    title: str
    source: str
    published_at: str
    url: str
    summary: str | None = None
    tags: list[str] = []
    matched_symbols: list[str] = []


class CatalystEvent(BaseModel):
    title: str
    category: str
    timing: str
    detail: str
    symbols: list[str] = []
    source: str | None = None
    verified: bool = False


class MarketTrendPanel(BaseModel):
    symbol: str
    label: str
    price: float
    change_1d: float
    change_5d: float | None = None
    change_20d: float | None = None
    signal: str
    trend: list[float]


class SignalCard(BaseModel):
    symbol: str
    label: str
    stance: str
    score: float
    price: float | None = None
    change_1d: float | None = None
    change_20d: float | None = None
    reasons: list[str]


class StoryBriefing(BaseModel):
    headline: str
    summary: str
    narrative: str
    key_points: list[str]
    action_items: list[str]
    risks: list[str]
    top_headlines: list[str]


class WatchlistItem(BaseModel):
    symbol: str
    label: str
    added_at: datetime


class WatchlistRequest(BaseModel):
    symbol: str
    label: str | None = None


class AlertItem(BaseModel):
    title: str
    severity: str
    message: str
    symbol: str | None
    details: list[str] = []


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    tier: str
    created_at: datetime


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class SupabaseSessionRequest(BaseModel):
    access_token: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class VerifyEmailRequest(BaseModel):
    token: str


class RegimeDriver(BaseModel):
    label: str
    value: str
    tone: str


class RegimeTransition(BaseModel):
    regime: str
    started_at: str
    ended_at: str
    duration_days: int
    average_confidence: float


class MarketLeader(BaseModel):
    symbol: str
    label: str
    metric: str
    value: float


class MarketStateSummary(BaseModel):
    regime: str
    confidence: float
    breadth: str
    volatility_state: str
    trend_strength: str
    cross_asset_confirmation: str
    summary: str
    drivers: list[RegimeDriver] = []
    warnings: list[str] = []
    leaders: list[MarketLeader] = []
    laggards: list[MarketLeader] = []
    supporting_signals: list[str] = []
    conflicting_signals: list[str] = []
    changes_since_yesterday: list[str] = []
    what_matters_now: list[str] = []
    bull_case: list[str] = []
    bear_case: list[str] = []
    next_steps: list[str] = []


class SectorPerformance(BaseModel):
    symbol: str
    label: str
    change_1d: float
    change_5d: float | None = None
    change_20d: float | None = None
    signal: str


class WatchlistInsight(BaseModel):
    symbol: str
    label: str
    stance: str
    summary: str
    score: float | None = None
    price: float | None = None
    change_1d: float | None = None
    change_20d: float | None = None
    reasons: list[str] = []
    catalyst: str | None = None
    regime_alignment: str = ""
    trade_implication: str = ""
    catalyst_risk: str = ""
    sector_readthrough: str = ""
    related_news: list[HeadlineReference] = []


class WatchlistExposure(BaseModel):
    symbol: str
    label: str
    sensitivity: str
    sentiment: str = ""
    directional_bias: str = ""
    themes: list[str] = []
    drivers: list[str] = []
    market_links: list[str] = []


class PremarketBriefing(BaseModel):
    headline: str
    overview: str
    checklist: list[str]
    focus_items: list[str]
    risks: list[str]
    catalyst_calendar: list[str] = []


class WatchlistDetailResponse(BaseModel):
    symbol: str
    label: str
    stance: str
    summary: str
    score: float | None = None
    price: float | None = None
    change_1d: float | None = None
    change_20d: float | None = None
    reasons: list[str] = []
    exposures: list[str] = []
    regime_alignment: str = ""
    trade_implication: str = ""
    catalyst_risk: str = ""
    sector_readthrough: str = ""
    related_news: list[WatchlistNewsItem] = []
    world_affairs: list[WorldAffairsEvent] = []
    narrative_timeline: list[NarrativeTimelineItem] = []
    calendar_events: list[CatalystEvent] = []


class BriefingHistoryItem(BaseModel):
    briefing_date: str
    headline: str
    overview: str


class DeliveryPreferences(BaseModel):
    email_enabled: bool
    webhook_enabled: bool
    webhook_url: str
    cadence: str


class DeliveryPreferencesRequest(BaseModel):
    email_enabled: bool
    webhook_enabled: bool
    webhook_url: str | None = None
    cadence: str


class BriefingDeliveryResult(BaseModel):
    headline: str
    cadence: str
    email_status: str
    webhook_status: str
    delivery_channels: list[str] = []


class SubscriptionTier(BaseModel):
    tier: str
    label: str
    description: str
    watchlist_limit: int
    email_delivery: bool
    verified_calendar: bool
    webhook_delivery: bool
    briefing_history_limit: int


class SubscriptionUpdateRequest(BaseModel):
    tier: str


class SharedWorkspaceMember(BaseModel):
    id: int
    name: str
    email: str
    tier: str
    role: str
    joined_at: str


class SharedWorkspaceNote(BaseModel):
    id: int
    content: str
    created_at: str
    author_name: str


class SharedWorkspaceBriefingSnapshot(BaseModel):
    id: int
    headline: str
    overview: str
    created_at: str
    author_name: str


class SharedWorkspace(BaseModel):
    id: int
    name: str
    invite_code: str
    owner_user_id: int
    created_at: str
    members: list[SharedWorkspaceMember]
    watchlist: list[WatchlistItem]
    notes: list[SharedWorkspaceNote]
    alerts: list[AlertItem] = []
    briefing_snapshots: list[SharedWorkspaceBriefingSnapshot] = []


class SharedWorkspaceRequest(BaseModel):
    name: str


class SharedWorkspaceJoinRequest(BaseModel):
    invite_code: str


class SharedWorkspaceNoteRequest(BaseModel):
    content: str


class TerminalBootstrapResponse(BaseModel):
    me: UserResponse
    prediction: PredictResponse
    market_state: MarketStateSummary
    transitions: list[RegimeTransition]
    sectors: list[SectorPerformance] = []
    watchlist: list[WatchlistItem] = []
