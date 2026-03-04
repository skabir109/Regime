import time

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import (
    APP_DESCRIPTION,
    APP_TITLE,
    APP_VERSION,
    CORS_ORIGINS,
    DATA_PATH,
    SESSION_COOKIE_NAME,
    SESSION_DURATION_HOURS,
    SESSION_SAMESITE,
    SESSION_SECURE,
    STATIC_DIR,
)
from app.schemas import (
    AlertItem,
    BriefingDeliveryResult,
    BriefingHistoryItem,
    CatalystEvent,
    DeliveryPreferences,
    DeliveryPreferencesRequest,
    ForgotPasswordRequest,
    HealthResponse,
    LoginRequest,
    MarketAssetSnapshot,
    MarketLeader,
    MarketStateSummary,
    MarketTrendPanel,
    MetadataResponse,
    NewsItem,
    NarrativeTimelineItem,
    PredictRequest,
    PredictResponse,
    RegimeDriver,
    RegimeTransition,
    RegimeHistoryPoint,
    ResetPasswordRequest,
    SectorPerformance,
    SharedWorkspace,
    SharedWorkspaceJoinRequest,
    SharedWorkspaceNoteRequest,
    SharedWorkspaceRequest,
    SignalCard,
    StoryBriefing,
    SubscriptionTier,
    SubscriptionUpdateRequest,
    SupabaseSessionRequest,
    TerminalBootstrapResponse,
    PremarketBriefing,
    WorldAffairsBriefing,
    WorldAffairsEvent,
    WorldAffairsRegionSummary,
    VerifyEmailRequest,
    WatchlistDetailResponse,
    WatchlistExposure,
    WatchlistNewsItem,
    WatchlistItem,
    WatchlistInsight,
    WatchlistRequest,
    UserResponse,
    RegisterRequest,
)
from app.services.alerts import build_alerts
from app.services.auth import (
    authenticate_supabase_access_token,
    authenticate_user,
    create_session,
    current_user_or_401,
    delete_session,
    generate_password_reset_token,
    reset_password,
    update_user_tier,
    register_user,
    verify_email,
)
from app.services.audit import log_audit_event
from app.services.db import init_db
from app.services.delivery import send_global_macro_briefing
from app.services.briefing import build_premarket_briefing
from app.services.briefing_history import load_briefing_history
from app.services.calendar import build_trader_calendar
from app.services.inference import predict_from_features, predict_latest
from app.services.features import compute_market_panels, compute_market_snapshot
from app.services.model import load_artifacts
from app.services.news import build_watchlist_news, fetch_market_news
from app.services.preferences import get_delivery_preferences, save_delivery_preferences
from app.services.sectors import fetch_sector_breadth
from app.services.shared_workspace import (
    add_shared_note,
    add_shared_watchlist_item,
    create_shared_workspace,
    get_shared_workspace,
    join_shared_workspace,
    remove_shared_watchlist_item,
    save_shared_briefing_snapshot,
)
from app.services.signals import fetch_trending_signals
from app.services.state import build_market_state_summary, compute_regime_transitions
from app.services.story import build_story_briefing
from app.services.subscriptions import get_tier_config, list_tiers
from app.services.terminal import compute_regime_history
from app.services.watchlist import add_watchlist_item, load_watchlist, remove_watchlist_item
from app.services.watchlist_detail import build_watchlist_detail
from app.services.watchlist_intelligence import build_watchlist_intelligence
from app.services.world_affairs import (
    build_watchlist_exposures,
    build_world_affairs_briefing,
    build_world_affairs_monitor,
    build_world_affairs_regions,
    build_narrative_timeline,
)


app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
init_db()

MODEL, META = load_artifacts()
_CACHE: dict[str, tuple[float, object]] = {}


def _set_session_cookie(response: Response, token: str):
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=SESSION_SECURE,
        samesite=SESSION_SAMESITE,
        max_age=SESSION_DURATION_HOURS * 3600,
        path="/",
    )


def _cached(key: str, ttl_seconds: int, factory):
    now = time.time()
    cached_item = _CACHE.get(key)
    if cached_item and cached_item[0] > now:
        return cached_item[1]

    value = factory()
    _CACHE[key] = (now + ttl_seconds, value)
    return value


def _cached_market_state():
    return _cached("market_state", 20, lambda: build_market_state_summary(MODEL, META))


def _cached_market_panels(window: int):
    return _cached(f"market_panels:{window}", 20, lambda: compute_market_panels(window=window))


def _cached_market_sectors(limit: int):
    return _cached(f"market_sectors:{limit}", 30, lambda: fetch_sector_breadth(limit=limit))


def _cached_news(limit: int):
    return _cached(f"news:{limit}", 60, lambda: fetch_market_news(limit=limit))


def _cached_world_affairs(limit: int):
    return _cached(f"world_affairs:{limit}", 60, lambda: build_world_affairs_monitor(limit=limit))


def _cached_world_regions(limit: int):
    return _cached(f"world_regions:{limit}", 60, lambda: build_world_affairs_regions(limit=limit))


def _cached_world_briefing(limit: int):
    return _cached(f"world_briefing:{limit}", 60, lambda: build_world_affairs_briefing(limit=limit))


def _cached_world_timeline(limit: int):
    return _cached(f"world_timeline:{limit}", 60, lambda: build_narrative_timeline(limit=limit))


def _cached_signals(limit: int):
    return _cached(f"signals:{limit}", 20, lambda: fetch_trending_signals(limit=limit))


def _cached_metadata():
    return _cached(
        "metadata",
        300,
        lambda: MetadataResponse(
            classes=META["classes"],
            features=META["features"],
            thresholds=META.get("thresholds", {}),
            training=META.get("training", {}),
            feature_importance=META.get("feature_importance", {}),
        ),
    )


@app.get("/", tags=["system"])
def root(request: Request):
    if current_user_or_none := request.cookies.get(SESSION_COOKIE_NAME):
        from app.services.auth import get_user_from_session

        if get_user_from_session(current_user_or_none):
            return FileResponse(STATIC_DIR / "index.html")
    return FileResponse(STATIC_DIR / "login.html")


@app.get("/login", tags=["system"])
def login_page():
    return FileResponse(STATIC_DIR / "login.html")


@app.post("/auth/register", response_model=UserResponse, tags=["auth"])
@limiter.limit("5/minute")
def auth_register(request: Request, payload: RegisterRequest, response: Response):
    try:
        user = register_user(payload.email, payload.password, payload.name)
        token = create_session(user["id"])
        _set_session_cookie(response, token)
        log_audit_event("user_registered", user["id"], {"email": payload.email, "ip": request.client.host if request.client else None})
        return user
    except Exception as exc:
        log_audit_event("user_registration_failed", None, {"email": payload.email, "error": str(exc), "ip": request.client.host if request.client else None})
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/auth/login", response_model=UserResponse, tags=["auth"])
@limiter.limit("10/minute")
def auth_login(request: Request, payload: LoginRequest, response: Response):
    try:
        user = authenticate_user(payload.email, payload.password)
        token = create_session(user["id"])
        _set_session_cookie(response, token)
        log_audit_event("user_logged_in", user["id"], {"email": payload.email, "ip": request.client.host if request.client else None})
        return user
    except Exception as exc:
        log_audit_event("user_login_failed", None, {"email": payload.email, "error": str(exc), "ip": request.client.host if request.client else None})
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@app.post("/auth/supabase/session", response_model=UserResponse, tags=["auth"])
@limiter.limit("15/minute")
def auth_supabase_session(request: Request, payload: SupabaseSessionRequest, response: Response):
    try:
        user = authenticate_supabase_access_token(payload.access_token)
        token = create_session(user["id"])
        _set_session_cookie(response, token)
        log_audit_event(
            "user_logged_in_supabase",
            user["id"],
            {"email": user["email"], "ip": request.client.host if request.client else None},
        )
        return user
    except Exception as exc:
        log_audit_event(
            "user_login_supabase_failed",
            None,
            {"error": str(exc), "ip": request.client.host if request.client else None},
        )
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@app.post("/auth/logout", tags=["auth"])
def auth_logout(request: Request, response: Response):
    delete_session(request.cookies.get(SESSION_COOKIE_NAME))
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return {"status": "logged_out"}

@app.post("/auth/verify-email", tags=["auth"])
def auth_verify_email(payload: VerifyEmailRequest):
    try:
        verify_email(payload.token)
        return {"status": "email_verified"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/auth/forgot-password", tags=["auth"])
@limiter.limit("3/minute")
def auth_forgot_password(request: Request, payload: ForgotPasswordRequest):
    try:
        generate_password_reset_token(payload.email)
        log_audit_event("password_reset_requested", None, {"email": payload.email, "ip": request.client.host if request.client else None})
        return {"status": "reset_email_sent_if_exists"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/auth/reset-password", tags=["auth"])
@limiter.limit("5/minute")
def auth_reset_password(request: Request, payload: ResetPasswordRequest):
    try:
        reset_password(payload.token, payload.new_password)
        log_audit_event("password_reset_successful", None, {"ip": request.client.host if request.client else None})
        return {"status": "password_reset"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/auth/me", response_model=UserResponse, tags=["auth"])
def auth_me(current_user: dict = Depends(current_user_or_401)):
    return current_user


@app.get("/billing/tiers", response_model=list[SubscriptionTier], tags=["billing"])
def billing_tiers(current_user: dict = Depends(current_user_or_401)):
    return list_tiers()


@app.put("/billing/tier", response_model=UserResponse, tags=["billing"])
def billing_tier_update(
    payload: SubscriptionUpdateRequest,
    current_user: dict = Depends(current_user_or_401),
):
    try:
        user = update_user_tier(current_user["id"], payload.tier)
        return {
            **user,
            "tier": get_tier_config(user["tier"])["tier"],
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/workspace/shared", response_model=SharedWorkspace | None, tags=["workspace"])
def workspace_shared(current_user: dict = Depends(current_user_or_401)):
    return get_shared_workspace(current_user["id"], MODEL, META)


@app.post("/workspace/shared", response_model=SharedWorkspace, tags=["workspace"])
def workspace_shared_create(
    payload: SharedWorkspaceRequest,
    current_user: dict = Depends(current_user_or_401),
):
    try:
        return create_shared_workspace(current_user["id"], payload.name)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/workspace/shared/join", response_model=SharedWorkspace, tags=["workspace"])
def workspace_shared_join(
    payload: SharedWorkspaceJoinRequest,
    current_user: dict = Depends(current_user_or_401),
):
    try:
        return join_shared_workspace(current_user["id"], payload.invite_code)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/workspace/shared/watchlist", response_model=SharedWorkspace, tags=["workspace"])
def workspace_shared_watchlist_add(
    payload: WatchlistRequest,
    current_user: dict = Depends(current_user_or_401),
):
    try:
        return add_shared_watchlist_item(current_user["id"], payload.symbol, payload.label)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/workspace/shared/watchlist/{symbol}", response_model=SharedWorkspace, tags=["workspace"])
def workspace_shared_watchlist_remove(symbol: str, current_user: dict = Depends(current_user_or_401)):
    try:
        return remove_shared_watchlist_item(current_user["id"], symbol)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/workspace/shared/notes", response_model=SharedWorkspace, tags=["workspace"])
def workspace_shared_note_add(
    payload: SharedWorkspaceNoteRequest,
    current_user: dict = Depends(current_user_or_401),
):
    try:
        return add_shared_note(current_user["id"], payload.content)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/workspace/shared/briefing-snapshot", response_model=SharedWorkspace, tags=["workspace"])
def workspace_shared_briefing_snapshot(current_user: dict = Depends(current_user_or_401)):
    try:
        return save_shared_briefing_snapshot(current_user["id"], MODEL, META)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/terminal", tags=["system"])
def terminal_page(current_user: dict = Depends(current_user_or_401)):
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/app", tags=["system"])
def app_info():
    return {
        "name": APP_TITLE,
        "version": APP_VERSION,
        "docs": "/docs",
        "status": "ready",
    }


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health():
    return HealthResponse(
        status="ok",
        model_loaded=True,
        data_available=DATA_PATH.exists(),
    )


@app.get("/metadata", response_model=MetadataResponse, tags=["model"])
def metadata():
    return _cached_metadata()


@app.get("/terminal/bootstrap", response_model=TerminalBootstrapResponse, tags=["terminal"])
def terminal_bootstrap(current_user: dict = Depends(current_user_or_401)):
    try:
        return TerminalBootstrapResponse(
            me=current_user,
            prediction=predict_latest(MODEL, META),
            market_state=_cached_market_state(),
            transitions=compute_regime_transitions(MODEL, META, limit=8),
            sectors=_cached_market_sectors(8),
            watchlist=load_watchlist(current_user["id"]),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/market/snapshot", response_model=list[MarketAssetSnapshot], tags=["terminal"])
def market_snapshot(current_user: dict = Depends(current_user_or_401)):
    try:
        return compute_market_snapshot()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/market/panels", response_model=list[MarketTrendPanel], tags=["terminal"])
def market_panels(window: int = 20, current_user: dict = Depends(current_user_or_401)):
    try:
        window = min(max(window, 10), 40)
        return _cached_market_panels(window)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/market/sectors", response_model=list[SectorPerformance], tags=["terminal"])
def market_sectors(limit: int = 8, current_user: dict = Depends(current_user_or_401)):
    limit = min(max(limit, 4), 12)
    return _cached_market_sectors(limit)


@app.get("/regime/history", response_model=list[RegimeHistoryPoint], tags=["terminal"])
def regime_history(limit: int = 30, current_user: dict = Depends(current_user_or_401)):
    try:
        return compute_regime_history(MODEL, META, limit=min(max(limit, 5), 90))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/regime/transitions", response_model=list[RegimeTransition], tags=["terminal"])
def regime_transitions(limit: int = 8, current_user: dict = Depends(current_user_or_401)):
    try:
        return compute_regime_transitions(MODEL, META, limit=min(max(limit, 3), 12))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/market/state", response_model=MarketStateSummary, tags=["terminal"])
def market_state(current_user: dict = Depends(current_user_or_401)):
    try:
        return _cached_market_state()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/news", response_model=list[NewsItem], tags=["terminal"])
def news(limit: int = 8, current_user: dict = Depends(current_user_or_401)):
    limit = min(max(limit, 3), 12)
    return _cached_news(limit)


@app.get("/world-affairs/monitor", response_model=list[WorldAffairsEvent], tags=["terminal"])
def world_affairs_monitor(limit: int = 8, current_user: dict = Depends(current_user_or_401)):
    limit = min(max(limit, 4), 12)
    return _cached_world_affairs(limit)


@app.get("/world-affairs/regions", response_model=list[WorldAffairsRegionSummary], tags=["terminal"])
def world_affairs_regions(limit: int = 6, current_user: dict = Depends(current_user_or_401)):
    limit = min(max(limit, 3), 10)
    return _cached_world_regions(limit)


@app.get("/briefing/global-macro", response_model=WorldAffairsBriefing, tags=["terminal"])
def global_macro_briefing(current_user: dict = Depends(current_user_or_401)):
    return _cached_world_briefing(6)


@app.get("/world-affairs/timeline", response_model=list[NarrativeTimelineItem], tags=["terminal"])
def world_affairs_timeline(limit: int = 6, current_user: dict = Depends(current_user_or_401)):
    limit = min(max(limit, 3), 10)
    return _cached_world_timeline(limit)


@app.get("/watchlist/news", response_model=list[WatchlistNewsItem], tags=["terminal"])
def watchlist_news(limit: int = 8, current_user: dict = Depends(current_user_or_401)):
    watchlist = load_watchlist(current_user["id"])
    items = _cached_news(max(limit * 2, 8))
    return build_watchlist_news(items, watchlist, limit=min(max(limit, 3), 12))


@app.get("/signals/trending", response_model=list[SignalCard], tags=["terminal"])
def signals_trending(limit: int = 6, current_user: dict = Depends(current_user_or_401)):
    limit = min(max(limit, 3), 10)
    return _cached_signals(limit)


@app.get("/story/briefing", response_model=StoryBriefing, tags=["terminal"])
def story_briefing(current_user: dict = Depends(current_user_or_401)):
    try:
        return build_story_briefing(MODEL, META)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/briefing/premarket", response_model=PremarketBriefing, tags=["terminal"])
def briefing_premarket(current_user: dict = Depends(current_user_or_401)):
    try:
        return build_premarket_briefing(MODEL, META, current_user["id"])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/briefing/history", response_model=list[BriefingHistoryItem], tags=["terminal"])
def briefing_history(limit: int = 10, current_user: dict = Depends(current_user_or_401)):
    return load_briefing_history(current_user["id"], limit=min(max(limit, 3), 20))


@app.get("/watchlist", response_model=list[WatchlistItem], tags=["terminal"])
def watchlist(current_user: dict = Depends(current_user_or_401)):
    return load_watchlist(current_user["id"])


@app.get("/watchlist/intelligence", response_model=list[WatchlistInsight], tags=["terminal"])
def watchlist_intelligence(current_user: dict = Depends(current_user_or_401)):
    return build_watchlist_intelligence(current_user["id"])


@app.get("/watchlist/exposures", response_model=list[WatchlistExposure], tags=["terminal"])
def watchlist_exposures(current_user: dict = Depends(current_user_or_401)):
    return build_watchlist_exposures(current_user["id"])


@app.get("/watchlist/{symbol}/detail", response_model=WatchlistDetailResponse, tags=["terminal"])
def watchlist_detail(symbol: str, current_user: dict = Depends(current_user_or_401)):
    try:
        return build_watchlist_detail(current_user["id"], symbol, MODEL, META)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/calendar/catalysts", response_model=list[CatalystEvent], tags=["terminal"])
def calendar_catalysts(limit: int = 6, current_user: dict = Depends(current_user_or_401)):
    try:
        state = build_market_state_summary(MODEL, META)
        return build_trader_calendar(state, current_user["id"], limit=min(max(limit, 3), 10))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/settings/delivery", response_model=DeliveryPreferences, tags=["terminal"])
def settings_delivery(current_user: dict = Depends(current_user_or_401)):
    return get_delivery_preferences(current_user["id"])


@app.put("/settings/delivery", response_model=DeliveryPreferences, tags=["terminal"])
def settings_delivery_update(
    payload: DeliveryPreferencesRequest,
    current_user: dict = Depends(current_user_or_401),
):
    try:
        return save_delivery_preferences(
            current_user["id"],
            payload.email_enabled,
            payload.webhook_enabled,
            payload.webhook_url,
            payload.cadence,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/delivery/global-macro/send", response_model=BriefingDeliveryResult, tags=["terminal"])
def delivery_global_macro_send(current_user: dict = Depends(current_user_or_401)):
    try:
        return send_global_macro_briefing(current_user["id"])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/watchlist", response_model=list[WatchlistItem], tags=["terminal"])
def watchlist_add(request: WatchlistRequest, current_user: dict = Depends(current_user_or_401)):
    try:
        return add_watchlist_item(current_user["id"], request.symbol, request.label)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/watchlist/{symbol}", response_model=list[WatchlistItem], tags=["terminal"])
def watchlist_remove(symbol: str, current_user: dict = Depends(current_user_or_401)):
    return remove_watchlist_item(current_user["id"], symbol)


@app.get("/alerts", response_model=list[AlertItem], tags=["terminal"])
def alerts(request: Request, current_user: dict = Depends(current_user_or_401)):
    try:
        user_alerts = build_alerts(MODEL, META, current_user["id"])
        if user_alerts:
            log_audit_event("alerts_generated", current_user["id"], {"count": len(user_alerts), "ip": request.client.host if request.client else None})
        return user_alerts
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/predict", response_model=PredictResponse, tags=["inference"])
def predict(request: PredictRequest, current_user: dict = Depends(current_user_or_401)):
    try:
        if request.features is None:
            return predict_latest(MODEL, META)
        return predict_from_features(
            MODEL,
            META,
            request.features,
            source="custom_payload",
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/predict/latest", response_model=PredictResponse, tags=["inference"])
def predict_latest_endpoint(current_user: dict = Depends(current_user_or_401)):
    try:
        return predict_latest(MODEL, META)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
