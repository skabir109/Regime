import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import time
from threading import Lock, Thread
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import (
    APP_ENV,
    APP_DESCRIPTION,
    APP_TITLE,
    APP_VERSION,
    CORS_ORIGINS,
    CSRF_COOKIE_NAME,
    CSRF_HEADER_NAME,
    CSRF_SECRET,
    DATA_PATH,
    SESSION_COOKIE_NAME,
    SESSION_DURATION_HOURS,
    SESSION_SAMESITE,
    SESSION_SECURE,
    REGIME_BILLING_TOKEN,
)
from app.schemas import (
    AIAnalyzeRequest,
    AIAnalyzeResponse,
    AlertItem,
    BriefingDeliveryResult,
    BriefingHistoryItem,
    CatalystEvent,
    DeliveryPreferences,
    DeliveryPreferencesRequest,
    DeliveryChannelTestRequest,
    DeliveryChannelTestResult,
    ForgotPasswordRequest,
    HealthResponse,
    SecurityHealthResponse,
    SystemDiagnosticsResponse,
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
    BillingCheckoutRequest,
    BillingIntentResponse,
    BillingSessionResponse,
    ClerkSessionRequest,
    SubscriptionTier,
    SubscriptionUpdateRequest,
    StarterPackResponse,
    TerminalBootstrapResponse,
    StressTestResult,
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
from app.services.db import init_db
from app.services.auth import (
    authenticate_clerk_session_token,
    authenticate_user,
    create_session,
    current_user_or_401,
    delete_session,
    generate_password_reset_token,
    get_user_from_session,
    reset_password,
    update_user_tier,
    register_user,
    mark_tier_selection_complete,
    verify_email,
)
from app.services.audit import log_audit_event
from app.services.api_protection import APILimitError, enforce_burst_limit, enforce_daily_limit
from app.services.api_protection import rate_limit_backend_status
from app.services.csrf import allowed_origin_set, extract_origin_from_referer, generate_csrf_token, validate_csrf_token
from app.services.delivery import send_global_macro_briefing
from app.services.delivery import send_test_channel_message
from app.services.briefing import build_premarket_briefing
from app.services.briefing_history import load_briefing_history
from app.services.billing import (
    create_checkout_session,
    create_customer_portal_session,
    create_subscription_payment_intent,
    process_stripe_webhook,
)
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
from app.services.signals import fetch_signals_for_universe, fetch_trending_signals
from app.services.starter_pack import apply_starter_pack, get_starter_pack
from app.services.state import build_market_state_summary, compute_regime_transitions
from app.services.system_status import build_system_status
from app.services.story import build_story_briefing
from app.services.subscriptions import get_tier_config, list_tiers
from app.services.terminal import compute_regime_history
from app.services.watchlist import add_watchlist_item, load_watchlist, remove_watchlist_item
from app.services.watchlist_detail import build_watchlist_detail_with_data
from app.services.watchlist_intelligence import build_watchlist_intelligence_with_data
from app.services.world_affairs import (
    build_watchlist_exposures,
    build_world_affairs_briefing,
    build_world_affairs_monitor,
    build_world_affairs_regions,
    build_narrative_timeline,
    build_stress_test,
)
from app.services.llm import generate_analysis


app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
)

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
_CSRF_EXEMPT_PATHS = {
    "/auth/register",
    "/auth/login",
    "/auth/clerk/session",
    "/auth/forgot-password",
    "/auth/reset-password",
    "/auth/verify-email",
    "/billing/stripe/webhook",
}
_ALLOWED_ORIGINS = allowed_origin_set()
if not _ALLOWED_ORIGINS:
    _ALLOWED_ORIGINS = {
        origin.lower()
        for origin in CORS_ORIGINS
        if "://" in origin
    }

@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    # Limit request body to 1MB
    if request.method in ("POST", "PUT", "PATCH"):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 1 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Request entity too large")
    
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def csrf_protect(request: Request, call_next):
    method = request.method.upper()
    if method in {"GET", "HEAD", "OPTIONS"}:
        return await call_next(request)

    path = request.url.path
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_token:
        return await call_next(request)
    if path in _CSRF_EXEMPT_PATHS:
        return await call_next(request)

    # Origin/referer checks reduce cross-site request forgery risk on cookie-authenticated mutations.
    origin = (request.headers.get("origin") or "").strip().lower()
    referer_origin = extract_origin_from_referer(request.headers.get("referer"))
    if origin and origin not in _ALLOWED_ORIGINS:
        raise HTTPException(status_code=403, detail="Origin is not allowed.")
    if not origin and referer_origin and referer_origin not in _ALLOWED_ORIGINS:
        raise HTTPException(status_code=403, detail="Referer is not allowed.")

    csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
    csrf_header = request.headers.get(CSRF_HEADER_NAME)
    if not csrf_cookie or not csrf_header:
        raise HTTPException(status_code=403, detail="Missing CSRF token.")
    if csrf_cookie != csrf_header:
        raise HTTPException(status_code=403, detail="CSRF token mismatch.")
    if not validate_csrf_token(csrf_cookie):
        raise HTTPException(status_code=403, detail="Invalid CSRF token.")

    return await call_next(request)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https:; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'; "
        "form-action 'self'"
    )
    return response


@app.middleware("http")
async def capture_security_status_codes(request: Request, call_next):
    response = await call_next(request)
    if response.status_code in {401, 403, 429}:
        _record_security_metric(f"http_{response.status_code}")
    return response

init_db()

MODEL, META = load_artifacts()
_CACHE: dict[str, tuple[float, object]] = {}
_USER_WARMING_LOCK = Lock()
_USER_WARMING: set[int] = set()
_SECURITY_METRICS_LOCK = Lock()
_SECURITY_METRICS: dict[str, int] = {
    "http_401": 0,
    "http_403": 0,
    "http_429": 0,
    "quota_denied": 0,
}


def _record_security_metric(name: str, amount: int = 1) -> None:
    with _SECURITY_METRICS_LOCK:
        _SECURITY_METRICS[name] = int(_SECURITY_METRICS.get(name, 0)) + amount


def _security_metric_snapshot() -> dict[str, int]:
    with _SECURITY_METRICS_LOCK:
        return dict(_SECURITY_METRICS)


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


def _set_csrf_cookie(response: Response, token: str):
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=token,
        httponly=False,
        secure=SESSION_SECURE,
        samesite=SESSION_SAMESITE,
        max_age=SESSION_DURATION_HOURS * 3600,
        path="/",
    )


def _clear_auth_cookies(response: Response):
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    response.delete_cookie(CSRF_COOKIE_NAME, path="/")

def _require_paid_tier(current_user: dict, feature_name: str) -> None:
    tier = get_tier_config(current_user.get("tier"))
    if tier["tier"] == "free":
        raise HTTPException(
            status_code=402,
            detail=f"{feature_name} requires a paid plan.",
        )


def _cached(key: str, ttl_seconds: int, factory):
    now = time.time()
    cached_item = _CACHE.get(key)
    if cached_item and cached_item[0] > now:
        return cached_item[1]

    value = factory()
    _CACHE[key] = (now + ttl_seconds, value)
    return value


def _invalidate_cache(*prefixes: str):
    if not prefixes:
        _CACHE.clear()
        return
    keys = [key for key in list(_CACHE.keys()) if any(key.startswith(prefix) for prefix in prefixes)]
    for key in keys:
        _CACHE.pop(key, None)


def _invalidate_user_terminal_cache(user_id: int):
    _invalidate_cache(
        f"terminal_bootstrap:{user_id}",
        f"workspace_shared:{user_id}",
        f"alerts:{user_id}",
        f"watchlist_intelligence:{user_id}",
        f"watchlist_exposures:{user_id}",
        f"watchlist_news:{user_id}",
        f"watchlist_detail:{user_id}",
        f"briefing_premarket:{user_id}",
        f"calendar:{user_id}",
    )


def _warm_user_caches_async(user_id: int, first_symbol: str | None = None) -> None:
    with _USER_WARMING_LOCK:
        if user_id in _USER_WARMING:
            return
        _USER_WARMING.add(user_id)

    def _worker():
        try:
            _cached_alerts(user_id)
            _cached_world_affairs(12)
            _cached_world_regions(8)
            _cached_world_briefing(6)
            _cached_world_timeline(8)
            _cached_watchlist_exposures(user_id)
            _cached_watchlist_intelligence(user_id)
            _cached_watchlist_news(user_id, 8)
            _cached_calendar_catalysts(user_id, 8)
            _cached_premarket_briefing(user_id)
            if first_symbol:
                _cached_watchlist_detail(user_id, first_symbol)
        except Exception:
            # Best-effort warm path should never fail user-facing requests.
            return
        finally:
            with _USER_WARMING_LOCK:
                _USER_WARMING.discard(user_id)

    Thread(target=_worker, daemon=True).start()


def _cached_market_state():
    return _cached(
        "market_state",
        20,
        lambda: build_market_state_summary(
            MODEL,
            META,
            prediction=_cached_prediction_latest(),
            sectors=_cached_market_sectors(8),
            news=_cached_news(6),
        ),
    )


def _cached_prediction_latest():
    return _cached("predict_latest", 10, lambda: predict_latest(MODEL, META))


def _cached_regime_transitions(limit: int):
    return _cached(
        f"regime_transitions:{limit}",
        60,
        lambda: compute_regime_transitions(MODEL, META, limit=limit),
    )


def _cached_market_panels(window: int):
    return _cached(f"market_panels:{window}", 20, lambda: compute_market_panels(window=window))


def _cached_market_sectors(limit: int):
    return _cached(f"market_sectors:{limit}", 30, lambda: fetch_sector_breadth(limit=limit))


def _cached_news(limit: int):
    # Fetch once with a shared higher cap, then slice for callers.
    rows = _cached("news_shared", 45, lambda: fetch_market_news(limit=24))
    return rows[:limit]


def _cached_world_affairs(limit: int):
    return _cached(f"world_affairs:{limit}", 20, lambda: build_world_affairs_monitor(limit=limit))


def _cached_world_regions(limit: int):
    return _cached(
        f"world_regions:{limit}",
        20,
        lambda: build_world_affairs_regions(limit=limit, events=_cached_world_affairs(max(limit * 2, 10))),
    )


def _cached_world_briefing(limit: int):
    return _cached(
        f"world_briefing:{limit}",
        20,
        lambda: build_world_affairs_briefing(limit=limit, events=_cached_world_affairs(max(limit * 2, 10))),
    )


def _cached_world_timeline(limit: int):
    return _cached(
        f"world_timeline:{limit}",
        20,
        lambda: build_narrative_timeline(limit=limit, events=_cached_world_affairs(max(limit * 2, 10))),
    )


def _cached_signals(limit: int):
    return _cached(f"signals:{limit}", 20, lambda: fetch_trending_signals(limit=limit))


def _watchlist_signature(user_id: int) -> str:
    items = load_watchlist(user_id)
    symbols = sorted(str(item.get("symbol", "")).upper() for item in items if item.get("symbol"))
    return ",".join(symbols) if symbols else "empty"


def _cached_watchlist_intelligence(user_id: int):
    signature = _watchlist_signature(user_id)
    def _build_intelligence():
        watchlist = load_watchlist(user_id)
        signals = _cached_watchlist_signals(user_id)
        news = _cached_news(10)
        exposures = _cached_watchlist_exposures(user_id)
        state = _cached_market_state()
        return build_watchlist_intelligence_with_data(
            user_id,
            watchlist=watchlist,
            state=state,
            signals=signals,
            news=news,
            exposures=exposures,
        )
    return _cached(
        f"watchlist_intelligence:{user_id}:{signature}",
        30,
        _build_intelligence,
    )


def _cached_watchlist_exposures(user_id: int):
    signature = _watchlist_signature(user_id)
    def _build_exposures():
        watchlist = load_watchlist(user_id)
        events = _cached_world_affairs(8)
        return build_watchlist_exposures(user_id, watchlist=watchlist, events=events)
    return _cached(
        f"watchlist_exposures:{user_id}:{signature}",
        30,
        _build_exposures,
    )


def _cached_watchlist_signals(user_id: int):
    signature = _watchlist_signature(user_id)
    def _build_signals():
        watchlist = load_watchlist(user_id)
        return fetch_signals_for_universe(watchlist) if watchlist else []
    return _cached(
        f"watchlist_signals:{user_id}:{signature}",
        45,
        _build_signals,
    )


def _cached_watchlist_news(user_id: int, limit: int):
    signature = _watchlist_signature(user_id)
    return _cached(
        f"watchlist_news:{user_id}:{signature}:{limit}",
        45,
        lambda: build_watchlist_news(
            _cached_news(max(limit * 2, 8)),
            load_watchlist(user_id),
            limit=limit,
        ),
    )


def _cached_watchlist_detail(user_id: int, symbol: str):
    signature = _watchlist_signature(user_id)
    normalized_symbol = symbol.strip().upper()
    def _build_detail():
        watchlist = load_watchlist(user_id)
        state = _cached_market_state()
        insights = _cached_watchlist_intelligence(user_id)
        news = _cached_news(12)
        calendar_events = _cached_calendar_catalysts(user_id, 10)
        exposures = _cached_watchlist_exposures(user_id)
        world_events = _cached_world_affairs(8)
        timeline = _cached_world_timeline(8)
        return build_watchlist_detail_with_data(
            user_id,
            normalized_symbol,
            MODEL,
            META,
            watchlist=watchlist,
            state=state,
            insights=insights,
            news=news,
            calendar_events=calendar_events,
            exposures=exposures,
            world_events=world_events,
            timeline=timeline,
        )
    return _cached(
        f"watchlist_detail:{user_id}:{signature}:{normalized_symbol}",
        20,
        _build_detail,
    )


def _cached_alerts(user_id: int):
    signature = _watchlist_signature(user_id)
    def _build_user_alerts():
        watchlist = load_watchlist(user_id)
        prediction = _cached_prediction_latest()
        news = _cached_news(6)
        world_events = _cached_world_affairs(6)
        return build_alerts(
            MODEL,
            META,
            user_id,
            watchlist=watchlist,
            prediction=prediction,
            news=news,
            world_events=world_events,
        )
    return _cached(
        f"alerts:{user_id}:{signature}",
        20,
        _build_user_alerts,
    )


def _cached_premarket_briefing(user_id: int):
    signature = _watchlist_signature(user_id)
    def _build_briefing():
        state = _cached_market_state()
        alerts = _cached_alerts(user_id)
        headlines = _cached_news(5)
        watchlist = load_watchlist(user_id)
        watchlist_insights = _cached_watchlist_intelligence(user_id)
        catalyst_calendar = _cached_calendar_catalysts(user_id, 5)
        return build_premarket_briefing(
            MODEL,
            META,
            user_id,
            state=state,
            alerts=alerts,
            headlines=headlines,
            watchlist=watchlist,
            watchlist_insights=watchlist_insights,
            catalyst_calendar=catalyst_calendar,
        )
    return _cached(
        f"briefing_premarket:{user_id}:{signature}",
        45,
        _build_briefing,
    )


def _cached_calendar_catalysts(user_id: int, limit: int):
    signature = _watchlist_signature(user_id)
    def _build_calendar():
        state = _cached_market_state()
        watchlist = load_watchlist(user_id)
        news = _cached_news(12)
        return build_trader_calendar(state, user_id, limit=limit, watchlist=watchlist, news=news)
    return _cached(
        f"calendar:{user_id}:{signature}:{limit}",
        45,
        _build_calendar,
    )


def _cached_workspace_shared(user_id: int):
    return _cached(
        f"workspace_shared:{user_id}",
        20,
        lambda: get_shared_workspace(user_id, MODEL, META),
    )


def _cached_terminal_bootstrap(current_user: dict):
    user_id = current_user["id"]
    user_tier = str(current_user.get("tier", "free"))

    def _build_bootstrap_payload():
        with ThreadPoolExecutor(max_workers=5) as pool:
            prediction_f = pool.submit(_cached_prediction_latest)
            transitions_f = pool.submit(_cached_regime_transitions, 8)
            sectors_f = pool.submit(_cached_market_sectors, 8)
            watchlist_f = pool.submit(load_watchlist, user_id)
            news_f = pool.submit(_cached_news, 6)
            prediction = prediction_f.result()
            sectors = sectors_f.result()
            news = news_f.result()
            market_state = build_market_state_summary(
                MODEL,
                META,
                prediction=prediction,
                sectors=sectors,
                news=news,
            )
            watchlist = watchlist_f.result()
            first_symbol = watchlist[0]["symbol"] if watchlist else None
            _warm_user_caches_async(user_id, first_symbol=first_symbol)
            return TerminalBootstrapResponse(
                me=current_user,
                prediction=prediction,
                market_state=market_state,
                transitions=transitions_f.result(),
                sectors=sectors,
                watchlist=watchlist,
                # Keep bootstrap lean; world timeline is loaded by the world view endpoint.
                world_timeline=[],
            )

    return _cached(
        f"terminal_bootstrap:{user_id}:{user_tier}",
        10,
        _build_bootstrap_payload,
    )


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
def root():
    return {"name": APP_TITLE, "version": APP_VERSION, "status": "api"}


@app.post("/auth/register", response_model=UserResponse, tags=["auth"])
@limiter.limit("5/minute")
def auth_register(request: Request, payload: RegisterRequest, response: Response):
    try:
        user = register_user(payload.email, payload.password, payload.name)
        token = create_session(user["id"])
        csrf_token = generate_csrf_token()
        _set_session_cookie(response, token)
        _set_csrf_cookie(response, csrf_token)
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
        csrf_token = generate_csrf_token()
        _set_session_cookie(response, token)
        _set_csrf_cookie(response, csrf_token)
        log_audit_event("user_logged_in", user["id"], {"email": payload.email, "ip": request.client.host if request.client else None})
        return user
    except Exception as exc:
        log_audit_event("user_login_failed", None, {"email": payload.email, "error": str(exc), "ip": request.client.host if request.client else None})
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@app.post("/auth/clerk/session", response_model=UserResponse, tags=["auth"])
@limiter.limit("20/minute")
def auth_clerk_session(request: Request, payload: ClerkSessionRequest, response: Response):
    try:
        user = authenticate_clerk_session_token(payload.session_token)
        token = create_session(user["id"])
        csrf_token = generate_csrf_token()
        _set_session_cookie(response, token)
        _set_csrf_cookie(response, csrf_token)
        log_audit_event(
            "user_logged_in_clerk",
            user["id"],
            {"email": user["email"], "ip": request.client.host if request.client else None},
        )
        return user
    except Exception as exc:
        log_audit_event(
            "user_login_clerk_failed",
            None,
            {"error": str(exc), "ip": request.client.host if request.client else None},
        )
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@app.post("/auth/logout", tags=["auth"])
@limiter.limit("20/minute")
def auth_logout(request: Request, response: Response):
    delete_session(request.cookies.get(SESSION_COOKIE_NAME))
    _clear_auth_cookies(response)
    return {"status": "logged_out"}


@app.get("/auth/csrf", tags=["auth"])
def auth_csrf(response: Response, current_user: dict = Depends(current_user_or_401)):
    token = generate_csrf_token()
    _set_csrf_cookie(response, token)
    return {"csrf_token": token, "user_id": current_user["id"]}

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


@app.post("/billing/checkout/session", response_model=BillingSessionResponse, tags=["billing"])
@limiter.limit("10/minute")
def billing_checkout_session(
    request: Request,
    payload: BillingCheckoutRequest,
    current_user: dict = Depends(current_user_or_401),
):
    try:
        url = create_checkout_session(current_user["id"], payload.tier)
        return {"url": url}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/billing/portal/session", response_model=BillingSessionResponse, tags=["billing"])
@limiter.limit("10/minute")
def billing_portal_session(request: Request, current_user: dict = Depends(current_user_or_401)):
    try:
        url = create_customer_portal_session(current_user["id"])
        return {"url": url}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/billing/subscription/intent", response_model=BillingIntentResponse, tags=["billing"])
@limiter.limit("10/minute")
def billing_subscription_intent(
    request: Request,
    payload: BillingCheckoutRequest,
    current_user: dict = Depends(current_user_or_401),
):
    try:
        intent = create_subscription_payment_intent(current_user["id"], payload.tier)
        return intent
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/billing/select-free", response_model=UserResponse, tags=["billing"])
@limiter.limit("10/minute")
def billing_select_free(request: Request, current_user: dict = Depends(current_user_or_401)):
    try:
        update_user_tier(current_user["id"], "free", allow_upgrade=True)
        user = mark_tier_selection_complete(current_user["id"])
        _invalidate_user_terminal_cache(current_user["id"])
        return user
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/billing/stripe/webhook", tags=["billing"])
@limiter.limit("120/minute")
async def billing_stripe_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    try:
        result = process_stripe_webhook(payload, signature)
        return {"status": "ok", **result}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/billing/tier", response_model=UserResponse, tags=["billing"])
def billing_tier_update(
    request: Request,
    payload: SubscriptionUpdateRequest,
    current_user: dict = Depends(current_user_or_401),
):
    try:
        current_tier = get_tier_config(current_user["tier"])["tier"]
        requested_tier = get_tier_config(payload.tier)["tier"]

        # Prevent client-side self-upgrades: only allow free-tier downgrade by users.
        billing_token = request.headers.get("x-billing-token", "").strip()
        has_billing_auth = bool(REGIME_BILLING_TOKEN) and billing_token == REGIME_BILLING_TOKEN
        if not has_billing_auth and requested_tier not in {"free", current_tier}:
            raise HTTPException(
                status_code=402,
                detail="Tier upgrades require billing confirmation.",
            )

        user = update_user_tier(
            current_user["id"],
            requested_tier,
            allow_upgrade=has_billing_auth,
        )
        user = mark_tier_selection_complete(current_user["id"])
        _invalidate_user_terminal_cache(current_user["id"])
        return {
            **user,
            "tier": get_tier_config(user["tier"])["tier"],
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/workspace/shared", response_model=SharedWorkspace | None, tags=["workspace"])
def workspace_shared(current_user: dict = Depends(current_user_or_401)):
    return _cached_workspace_shared(current_user["id"])


@app.post("/workspace/shared", response_model=SharedWorkspace, tags=["workspace"])
@limiter.limit("20/minute")
def workspace_shared_create(
    request: Request,
    payload: SharedWorkspaceRequest,
    current_user: dict = Depends(current_user_or_401),
):
    try:
        workspace = create_shared_workspace(current_user["id"], payload.name)
        _invalidate_user_terminal_cache(current_user["id"])
        return workspace
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/workspace/shared/join", response_model=SharedWorkspace, tags=["workspace"])
@limiter.limit("20/minute")
def workspace_shared_join(
    request: Request,
    payload: SharedWorkspaceJoinRequest,
    current_user: dict = Depends(current_user_or_401),
):
    try:
        workspace = join_shared_workspace(current_user["id"], payload.invite_code)
        _invalidate_user_terminal_cache(current_user["id"])
        return workspace
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/workspace/shared/watchlist", response_model=SharedWorkspace, tags=["workspace"])
@limiter.limit("30/minute")
def workspace_shared_watchlist_add(
    request: Request,
    payload: WatchlistRequest,
    current_user: dict = Depends(current_user_or_401),
):
    try:
        workspace = add_shared_watchlist_item(current_user["id"], payload.symbol, payload.label)
        _invalidate_user_terminal_cache(current_user["id"])
        return workspace
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/workspace/shared/watchlist/{symbol}", response_model=SharedWorkspace, tags=["workspace"])
@limiter.limit("30/minute")
def workspace_shared_watchlist_remove(request: Request, symbol: str, current_user: dict = Depends(current_user_or_401)):
    try:
        workspace = remove_shared_watchlist_item(current_user["id"], symbol)
        _invalidate_user_terminal_cache(current_user["id"])
        return workspace
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/workspace/shared/notes", response_model=SharedWorkspace, tags=["workspace"])
@limiter.limit("30/minute")
def workspace_shared_note_add(
    request: Request,
    payload: SharedWorkspaceNoteRequest,
    current_user: dict = Depends(current_user_or_401),
):
    try:
        workspace = add_shared_note(current_user["id"], payload.content)
        _invalidate_user_terminal_cache(current_user["id"])
        return workspace
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/workspace/shared/briefing-snapshot", response_model=SharedWorkspace, tags=["workspace"])
@limiter.limit("15/minute")
def workspace_shared_briefing_snapshot(request: Request, current_user: dict = Depends(current_user_or_401)):
    try:
        workspace = save_shared_briefing_snapshot(current_user["id"], MODEL, META)
        _invalidate_user_terminal_cache(current_user["id"])
        return workspace
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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


@app.get("/health/security", response_model=SecurityHealthResponse, tags=["system"])
def health_security():
    warnings: list[str] = []
    csrf_secret_configured = bool(CSRF_SECRET)
    if APP_ENV in {"production", "prod"} and not csrf_secret_configured:
        warnings.append("REGIME_CSRF_SECRET is missing in production mode.")
    if not SESSION_SECURE:
        warnings.append("REGIME_SESSION_SECURE is false.")
    if str(SESSION_SAMESITE).lower() != "strict":
        warnings.append("REGIME_SESSION_SAMESITE is not strict.")

    redis_status = rate_limit_backend_status()
    if APP_ENV in {"production", "prod"} and redis_status.get("mode") != "redis":
        warnings.append("Redis-backed burst limiting is not active.")

    return SecurityHealthResponse(
        status="ok" if not warnings else "degraded",
        app_env=APP_ENV,
        session_secure_default=SESSION_SECURE,
        session_samesite=SESSION_SAMESITE,
        csrf_secret_configured=csrf_secret_configured,
        redis=redis_status,
        security_events=_security_metric_snapshot(),
        warnings=warnings,
    )


@app.get("/ops/status", response_model=SystemDiagnosticsResponse, tags=["system"])
def ops_status(current_user: dict = Depends(current_user_or_401)):
    try:
        return build_system_status()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/metadata", response_model=MetadataResponse, tags=["model"])
def metadata():
    return _cached_metadata()


@app.get("/terminal/bootstrap", response_model=TerminalBootstrapResponse, tags=["terminal"])
def terminal_bootstrap(current_user: dict = Depends(current_user_or_401)):
    try:
        return _cached_terminal_bootstrap(current_user)
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
        return _cached_regime_transitions(limit=min(max(limit, 3), 12))
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


@app.websocket("/ws/world-affairs")
async def ws_world_affairs(websocket: WebSocket):
    token = websocket.cookies.get(SESSION_COOKIE_NAME)
    user = get_user_from_session(token)
    if not user:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    last_signature = ""
    try:
        while True:
            payload = {
                "world_affairs": _cached_world_affairs(8),
                "world_regions": _cached_world_regions(6),
                "world_briefing": _cached_world_briefing(6),
                "world_timeline": _cached_world_timeline(6),
            }
            signature = json.dumps(payload, sort_keys=True, default=str)
            if signature != last_signature:
                await websocket.send_json(
                    {
                        "type": "world_update",
                        "as_of": datetime.now(timezone.utc).isoformat(),
                        **payload,
                    }
                )
                last_signature = signature
            await asyncio.sleep(6)
    except WebSocketDisconnect:
        return
    except Exception:
        await websocket.close(code=1011)


@app.get("/watchlist/news", response_model=list[WatchlistNewsItem], tags=["terminal"])
def watchlist_news(limit: int = 8, current_user: dict = Depends(current_user_or_401)):
    return _cached_watchlist_news(current_user["id"], limit=min(max(limit, 3), 12))


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
        return _cached_premarket_briefing(current_user["id"])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/briefing/history", response_model=list[BriefingHistoryItem], tags=["terminal"])
def briefing_history(limit: int = 10, current_user: dict = Depends(current_user_or_401)):
    return load_briefing_history(current_user["id"], limit=min(max(limit, 3), 20))


@app.get("/watchlist", response_model=list[WatchlistItem], tags=["terminal"])
def watchlist(current_user: dict = Depends(current_user_or_401)):
    return load_watchlist(current_user["id"])


@app.get("/watchlist/starter-pack", response_model=StarterPackResponse, tags=["terminal"])
def watchlist_starter_pack(current_user: dict = Depends(current_user_or_401)):
    watchlist_items = load_watchlist(current_user["id"])
    return {
        **get_starter_pack(),
        "applied_symbols": [],
        "already_seeded": bool(watchlist_items),
        "watchlist": watchlist_items,
    }


@app.post("/watchlist/starter-pack", response_model=StarterPackResponse, tags=["terminal"])
@limiter.limit("10/minute")
def watchlist_starter_pack_apply(request: Request, current_user: dict = Depends(current_user_or_401)):
    try:
        result = apply_starter_pack(current_user["id"])
        _invalidate_user_terminal_cache(current_user["id"])
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/watchlist/intelligence", response_model=list[WatchlistInsight], tags=["terminal"])
def watchlist_intelligence(current_user: dict = Depends(current_user_or_401)):
    return _cached_watchlist_intelligence(current_user["id"])


@app.get("/watchlist/exposures", response_model=list[WatchlistExposure], tags=["terminal"])
def watchlist_exposures(current_user: dict = Depends(current_user_or_401)):
    return _cached_watchlist_exposures(current_user["id"])


@app.get("/watchlist/stress-test/{theme}", response_model=StressTestResult, tags=["terminal"])
def watchlist_stress_test(theme: str, current_user: dict = Depends(current_user_or_401)):
    try:
        return build_stress_test(current_user["id"], theme)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/watchlist/{symbol}/detail", response_model=WatchlistDetailResponse, tags=["terminal"])
def watchlist_detail(symbol: str, current_user: dict = Depends(current_user_or_401)):
    try:
        return _cached_watchlist_detail(current_user["id"], symbol)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/calendar/catalysts", response_model=list[CatalystEvent], tags=["terminal"])
def calendar_catalysts(limit: int = 6, current_user: dict = Depends(current_user_or_401)):
    try:
        return _cached_calendar_catalysts(current_user["id"], limit=min(max(limit, 3), 10))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/settings/delivery", response_model=DeliveryPreferences, tags=["terminal"])
def settings_delivery(current_user: dict = Depends(current_user_or_401)):
    return get_delivery_preferences(current_user["id"])


@app.put("/settings/delivery", response_model=DeliveryPreferences, tags=["terminal"])
@limiter.limit("20/minute")
def settings_delivery_update(
    request: Request,
    payload: DeliveryPreferencesRequest,
    current_user: dict = Depends(current_user_or_401),
):
    try:
        result = save_delivery_preferences(
            current_user["id"],
            payload.email_enabled,
            payload.webhook_enabled,
            payload.webhook_url,
            payload.cadence,
            payload.timezone,
            payload.slack_enabled,
            payload.slack_webhook_url,
            payload.discord_enabled,
            payload.discord_webhook_url,
        )
        _invalidate_user_terminal_cache(current_user["id"])
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/settings/delivery/test/slack", response_model=DeliveryChannelTestResult, tags=["terminal"])
@limiter.limit("10/minute")
def settings_delivery_test_slack(
    request: Request,
    payload: DeliveryChannelTestRequest,
    current_user: dict = Depends(current_user_or_401),
):
    try:
        return send_test_channel_message(current_user["id"], "slack", payload.webhook_url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/settings/delivery/test/discord", response_model=DeliveryChannelTestResult, tags=["terminal"])
@limiter.limit("10/minute")
def settings_delivery_test_discord(
    request: Request,
    payload: DeliveryChannelTestRequest,
    current_user: dict = Depends(current_user_or_401),
):
    try:
        return send_test_channel_message(current_user["id"], "discord", payload.webhook_url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/delivery/global-macro/send", response_model=BriefingDeliveryResult, tags=["terminal"])
@limiter.limit("5/minute")
def delivery_global_macro_send(request: Request, current_user: dict = Depends(current_user_or_401)):
    try:
        _require_paid_tier(current_user, "Global macro delivery")
        return send_global_macro_briefing(current_user["id"])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/watchlist", response_model=list[WatchlistItem], tags=["terminal"])
@limiter.limit("30/minute")
def watchlist_add(
    request: Request,
    payload: WatchlistRequest,
    current_user: dict = Depends(current_user_or_401),
):
    try:
        watchlist_items = add_watchlist_item(current_user["id"], payload.symbol, payload.label)
        _invalidate_user_terminal_cache(current_user["id"])
        return watchlist_items
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/watchlist/{symbol}", response_model=list[WatchlistItem], tags=["terminal"])
@limiter.limit("30/minute")
def watchlist_remove(request: Request, symbol: str, current_user: dict = Depends(current_user_or_401)):
    result = remove_watchlist_item(current_user["id"], symbol)
    _invalidate_user_terminal_cache(current_user["id"])
    return result


@app.get("/alerts", response_model=list[AlertItem], tags=["terminal"])
def alerts(request: Request, current_user: dict = Depends(current_user_or_401)):
    try:
        user_alerts = _cached_alerts(current_user["id"])
        if user_alerts:
            log_audit_event("alerts_generated", current_user["id"], {"count": len(user_alerts), "ip": request.client.host if request.client else None})
        return user_alerts
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/predict", response_model=PredictResponse, tags=["inference"])
@limiter.limit("45/minute")
def predict(
    request: Request,
    payload: PredictRequest,
    current_user: dict = Depends(current_user_or_401),
):
    try:
        if payload.features is None:
            return predict_latest(MODEL, META)
        return predict_from_features(
            MODEL,
            META,
            payload.features,
            source="custom_payload",
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/predict/latest", response_model=PredictResponse, tags=["inference"])
@limiter.limit("60/minute")
def predict_latest_endpoint(request: Request, current_user: dict = Depends(current_user_or_401)):
    try:
        return _cached_prediction_latest()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/ai/analyze", response_model=AIAnalyzeResponse, tags=["ai"])
@limiter.limit("10/minute")
def ai_analyze(
    request: Request,
    payload: AIAnalyzeRequest,
    current_user: dict = Depends(current_user_or_401),
):
    try:
        tier = get_tier_config(current_user.get("tier"))
        _require_paid_tier(current_user, "AI analysis")
        try:
            enforce_burst_limit(current_user["id"], "ai_analyze", int(tier.get("ai_minute_limit", 0)))
            usage = enforce_daily_limit(current_user["id"], "ai_analyze", int(tier.get("ai_daily_limit", 0)))
        except APILimitError as exc:
            _record_security_metric("quota_denied")
            raise HTTPException(status_code=429, detail=str(exc)) from exc

        response = generate_analysis(payload)
        log_audit_event(
            "ai_analyze",
            current_user["id"],
            {
                "mode": response.mode,
                "attempts": response.attempts,
                "validator_passed": response.validator_passed,
                "validation_error_count": len(response.validation_errors),
                "daily_usage_used": usage["used"],
                "daily_usage_remaining": usage["remaining"],
                "ip": request.client.host if request.client else None,
            },
        )
        return response
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
