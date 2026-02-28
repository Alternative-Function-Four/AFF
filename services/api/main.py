from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from starlette.exceptions import HTTPException as StarletteHTTPException

from agent_contracts import deduplicate_event_agent, normalize_event_agent

SG_TZ = ZoneInfo("Asia/Singapore")
TOKEN_TTL_HOURS = 8
MAX_NOTIFICATIONS_PER_DAY = 2
QUIET_HOUR_START = 22
QUIET_HOUR_END = 8


class BudgetMode(str, Enum):
    budget = "budget"
    moderate = "moderate"
    premium = "premium"
    any = "any"


class ActiveDays(str, Enum):
    weekday = "weekday"
    weekend = "weekend"
    both = "both"


class PreferredTime(str, Enum):
    morning = "morning"
    afternoon = "afternoon"
    evening = "evening"
    late_night = "late_night"


class TimeWindow(str, Enum):
    today = "today"
    tonight = "tonight"
    weekend = "weekend"
    next_7_days = "next_7_days"


class FeedMode(str, Enum):
    solo = "solo"
    date = "date"
    group = "group"


class InteractionSignal(str, Enum):
    interested = "interested"
    not_for_me = "not_for_me"
    already_knew = "already_knew"
    saved = "saved"
    dismissed = "dismissed"
    opened = "opened"


class FeedbackSignal(str, Enum):
    interested = "interested"
    not_for_me = "not_for_me"
    already_knew = "already_knew"


class SourceAccessMethod(str, Enum):
    api = "api"
    rss = "rss"
    ics = "ics"
    html_extract = "html_extract"
    manual = "manual"


class SourceStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    paused = "paused"


class SourceApprovalDecision(str, Enum):
    approved = "approved"
    rejected = "rejected"
    needs_manual_review = "needs_manual_review"


class NotificationPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class NotificationStatus(str, Enum):
    queued = "queued"
    sent = "sent"
    suppressed = "suppressed"
    failed = "failed"


class ErrorEnvelope(BaseModel):
    code: str
    message: str
    details: dict[str, Any]
    request_id: str


class UserSummary(BaseModel):
    id: UUID
    display_name: str


class AuthSessionResponse(BaseModel):
    access_token: str
    token_type: str
    expires_at: datetime
    user: UserSummary


class DemoLoginRequest(BaseModel):
    display_name: str = Field(min_length=1)
    persona_seed: str | None = None


class PasswordLoginRequest(BaseModel):
    email: str
    password: str


class PreferenceProfileInput(BaseModel):
    preferred_categories: list[str]
    preferred_subcategories: list[str]
    budget_mode: BudgetMode
    preferred_distance_km: float = Field(ge=0, le=50)
    active_days: ActiveDays
    preferred_times: list[PreferredTime]
    anti_preferences: list[str]


class PreferenceProfile(PreferenceProfileInput):
    user_id: UUID
    updated_at: datetime


class InteractionCreateRequest(BaseModel):
    event_id: UUID
    signal: InteractionSignal
    context: dict[str, Any]


class CreatedResponse(BaseModel):
    id: UUID
    created_at: datetime


class Price(BaseModel):
    min: float | None = None
    max: float | None = None
    currency: str | None = None


class SourceProvenance(BaseModel):
    source_id: UUID
    source_name: str
    source_url: str


class FeedItem(BaseModel):
    event_id: UUID
    title: str
    datetime_start: datetime
    venue_name: str
    category: str
    price: Price | None = None
    relevance_score: float
    reasons: list[str]
    source_provenance: list[SourceProvenance]


class FeedResponse(BaseModel):
    items: list[FeedItem]
    coverage_warning: str | None
    request_id: str


class EventOccurrence(BaseModel):
    datetime_start: datetime
    datetime_end: datetime | None = None
    timezone: str


class EventDetail(BaseModel):
    event_id: UUID
    title: str
    category: str
    subcategory: str | None = None
    description: str | None = None
    venue_name: str | None = None
    venue_address: str | None = None
    occurrences: list[EventOccurrence]
    source_provenance: list[SourceProvenance]


class EventFeedbackRequest(BaseModel):
    signal: FeedbackSignal
    context: dict[str, Any]


class NotificationLog(BaseModel):
    id: UUID
    event_id: UUID
    priority: NotificationPriority
    title: str
    body: str
    status: NotificationStatus
    sent_at: datetime | None = None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationLog]


class TestNotificationRequest(BaseModel):
    event_id: UUID
    reason: str


class TestNotificationResponse(BaseModel):
    queued: bool
    notification_id: UUID


class Source(BaseModel):
    id: UUID
    name: str
    url: HttpUrl
    source_type: str
    access_method: SourceAccessMethod
    status: SourceStatus
    policy_risk_score: int = Field(ge=0, le=100)
    quality_score: int = Field(ge=0, le=100)
    crawl_frequency_minutes: int = Field(ge=15)
    terms_url: str | None = None
    notes: str | None = None

    model_config = ConfigDict(extra="forbid")


class SourceListResponse(BaseModel):
    items: list[Source]


class SourceCreateRequest(BaseModel):
    name: str
    url: HttpUrl
    source_type: str
    access_method: SourceAccessMethod
    terms_url: str | None = None


class SourceApprovalRequest(BaseModel):
    decision: SourceApprovalDecision
    policy_risk_score: int = Field(ge=0, le=100)
    quality_score: int = Field(ge=0, le=100)
    notes: str


class IngestionRunRequest(BaseModel):
    source_ids: list[UUID] = Field(min_length=1)
    reason: str


class IngestionRunResponse(BaseModel):
    job_id: UUID
    queued_count: int


@dataclass
class UserRecord:
    id: str
    display_name: str
    email: str | None
    role: str
    created_at: datetime


@dataclass
class SessionRecord:
    token: str
    user_id: str
    expires_at: datetime


@dataclass
class InteractionRecord:
    id: str
    user_id: str
    event_id: str
    signal: str
    context: dict[str, Any]
    created_at: datetime


@dataclass
class EventRecord:
    event_id: str
    title: str
    category: str
    subcategory: str | None
    description: str | None
    venue_name: str | None
    venue_address: str | None
    occurrences: list[EventOccurrence]
    price: Price | None
    source_provenance: list[SourceProvenance]


@dataclass
class InMemoryStore:
    users: dict[str, UserRecord] = field(default_factory=dict)
    users_by_email: dict[str, str] = field(default_factory=dict)
    sessions: dict[str, SessionRecord] = field(default_factory=dict)
    preferences: dict[str, PreferenceProfile] = field(default_factory=dict)
    events: dict[str, EventRecord] = field(default_factory=dict)
    interactions: list[InteractionRecord] = field(default_factory=list)
    sources: dict[str, Source] = field(default_factory=dict)
    notification_logs: list[tuple[str, NotificationLog]] = field(default_factory=list)
    ingestion_jobs: list[dict[str, Any]] = field(default_factory=list)
    ingestion_metrics: dict[str, Any] = field(default_factory=dict)
    ingestion_logs: list[dict[str, Any]] = field(default_factory=list)
    now_provider: Callable[[], datetime] = lambda: datetime.now(SG_TZ)


class APIError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


def make_request_id() -> str:
    return f"req_{uuid4().hex[:12]}"


def as_sg_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=SG_TZ)
    return value.astimezone(SG_TZ)


def now_sg(store: InMemoryStore) -> datetime:
    return as_sg_datetime(store.now_provider())


def make_ingestion_metrics() -> dict[str, Any]:
    return {
        "normalization_low_confidence_total": 0,
        "dedup_merge_action_total": {
            "skip": 0,
            "merge_sources": 0,
            "create_new": 0,
        },
        "source_parse_failures_total": 0,
    }


def append_ingestion_log(
    *,
    run_id: str,
    level: str,
    message: str,
    payload: dict[str, Any],
    user_id: str | None = None,
    source_id: str | None = None,
    event_id: str | None = None,
) -> None:
    store.ingestion_logs.append(
        {
            "timestamp": now_sg(store).isoformat(),
            "level": level,
            "service": "ingestion",
            "run_id": run_id,
            "user_id": user_id,
            "source_id": source_id,
            "event_id": event_id,
            "message": message,
            "payload": payload,
        }
    )


def default_preference_profile(user_id: str, now: datetime) -> PreferenceProfile:
    return PreferenceProfile(
        user_id=UUID(user_id),
        preferred_categories=["events", "food", "nightlife"],
        preferred_subcategories=[],
        budget_mode=BudgetMode.moderate,
        preferred_distance_km=8,
        active_days=ActiveDays.both,
        preferred_times=[PreferredTime.evening],
        anti_preferences=[],
        updated_at=now,
    )


def event_matches_window(event: EventRecord, time_window: TimeWindow, now: datetime) -> bool:
    start = event.occurrences[0].datetime_start.astimezone(SG_TZ)
    if time_window == TimeWindow.today:
        return start.date() == now.date()
    if time_window == TimeWindow.tonight:
        return start.date() == now.date() and start.hour >= 18
    if time_window == TimeWindow.weekend:
        return start.weekday() in {5, 6} and start <= now + timedelta(days=7)
    if time_window == TimeWindow.next_7_days:
        return now <= start <= now + timedelta(days=7)
    return True


def build_feed_score(
    user_id: str,
    event: EventRecord,
    profile: PreferenceProfile,
    budget: BudgetMode,
    interactions: list[InteractionRecord],
) -> tuple[float, list[str]]:
    score = 0.5
    reasons: list[str] = []

    if event.category in profile.preferred_categories:
        score += 0.25
        reasons.append(f"Matches preferred category '{event.category}'")

    if event.subcategory and event.subcategory in profile.preferred_subcategories:
        score += 0.1
        reasons.append(f"Matches subcategory '{event.subcategory}'")

    lowered = f"{event.title} {event.category}".lower()
    if any(term.lower() in lowered for term in profile.anti_preferences):
        score -= 0.2
        reasons.append("Contains anti-preference signal")

    budget_limits = {
        BudgetMode.budget: 30,
        BudgetMode.moderate: 80,
        BudgetMode.premium: 200,
        BudgetMode.any: None,
    }
    limit = budget_limits[budget]
    if limit is not None and event.price and event.price.max is not None and event.price.max > limit:
        score -= 0.15

    for item in interactions:
        if item.user_id != user_id or item.event_id != event.event_id:
            continue
        if item.signal == FeedbackSignal.interested.value:
            score += 0.3
            reasons.append("Boosted by interested feedback")
        elif item.signal == FeedbackSignal.not_for_me.value:
            score -= 0.45
            reasons.append("Lowered by not_for_me feedback")
        elif item.signal == FeedbackSignal.already_knew.value:
            score -= 0.1
            reasons.append("Novelty reduced by already_knew feedback")

    score = round(max(0.0, min(score, 1.5)), 4)
    if not reasons:
        reasons.append("General relevance baseline")
    return score, reasons


def is_quiet_hours(moment: datetime) -> bool:
    hour = moment.hour
    return hour >= QUIET_HOUR_START or hour < QUIET_HOUR_END


def notifications_count_today(store: InMemoryStore, user_id: str, now: datetime) -> int:
    total = 0
    for uid, log in store.notification_logs:
        if uid != user_id:
            continue
        if log.created_at.astimezone(SG_TZ).date() != now.date():
            continue
        if log.status in {NotificationStatus.queued, NotificationStatus.sent}:
            total += 1
    return total


def create_seed_store() -> InMemoryStore:
    store = InMemoryStore()
    current = now_sg(store).replace(minute=0, second=0, microsecond=0)
    store.ingestion_metrics = make_ingestion_metrics()

    source_a = Source(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        name="SG Arts Calendar",
        url="https://events.example.sg/arts",
        source_type="arts",
        access_method=SourceAccessMethod.rss,
        status=SourceStatus.approved,
        policy_risk_score=10,
        quality_score=82,
        crawl_frequency_minutes=60,
        terms_url="https://events.example.sg/terms",
        notes="Seed source",
    )
    source_b = Source(
        id=UUID("22222222-2222-2222-2222-222222222222"),
        name="SG Food Picks",
        url="https://food.example.sg/listings",
        source_type="food",
        access_method=SourceAccessMethod.api,
        status=SourceStatus.approved,
        policy_risk_score=8,
        quality_score=78,
        crawl_frequency_minutes=45,
        terms_url="https://food.example.sg/terms",
        notes="Seed source",
    )
    source_c = Source(
        id=UUID("33333333-3333-3333-3333-333333333333"),
        name="Nightlife Picks",
        url="https://night.example.sg/today",
        source_type="nightlife",
        access_method=SourceAccessMethod.ics,
        status=SourceStatus.approved,
        policy_risk_score=15,
        quality_score=75,
        crawl_frequency_minutes=90,
        terms_url="https://night.example.sg/terms",
        notes="Seed source",
    )
    store.sources = {
        str(source_a.id): source_a,
        str(source_b.id): source_b,
        str(source_c.id): source_c,
    }

    events = [
        EventRecord(
            event_id="aaaaaaaa-1111-4111-8111-111111111111",
            title="Rooftop Jazz Session",
            category="events",
            subcategory="indie_music",
            description="Sunset live jazz with city skyline.",
            venue_name="Esplanade",
            venue_address="1 Esplanade Dr",
            occurrences=[
                EventOccurrence(
                    datetime_start=current + timedelta(days=1, hours=2),
                    datetime_end=current + timedelta(days=1, hours=5),
                    timezone="Asia/Singapore",
                )
            ],
            price=Price(min=20, max=40, currency="SGD"),
            source_provenance=[
                SourceProvenance(
                    source_id=source_a.id,
                    source_name=source_a.name,
                    source_url=str(source_a.url),
                )
            ],
        ),
        EventRecord(
            event_id="bbbbbbbb-2222-4222-8222-222222222222",
            title="Late Night Hawker Crawl",
            category="food",
            subcategory="hawker",
            description="Guided food tour across two hawker centers.",
            venue_name="Maxwell Food Centre",
            venue_address="1 Kadayanallur St",
            occurrences=[
                EventOccurrence(
                    datetime_start=current + timedelta(days=1, hours=4),
                    datetime_end=current + timedelta(days=1, hours=7),
                    timezone="Asia/Singapore",
                )
            ],
            price=Price(min=15, max=25, currency="SGD"),
            source_provenance=[
                SourceProvenance(
                    source_id=source_b.id,
                    source_name=source_b.name,
                    source_url=str(source_b.url),
                )
            ],
        ),
        EventRecord(
            event_id="cccccccc-3333-4333-8333-333333333333",
            title="Underground Comedy Open Mic",
            category="nightlife",
            subcategory="comedy",
            description="Indie stand-up showcase.",
            venue_name="The Projector",
            venue_address="6001 Beach Rd",
            occurrences=[
                EventOccurrence(
                    datetime_start=current + timedelta(days=2, hours=3),
                    datetime_end=current + timedelta(days=2, hours=6),
                    timezone="Asia/Singapore",
                )
            ],
            price=Price(min=18, max=35, currency="SGD"),
            source_provenance=[
                SourceProvenance(
                    source_id=source_c.id,
                    source_name=source_c.name,
                    source_url=str(source_c.url),
                )
            ],
        ),
    ]
    store.events = {event.event_id: event for event in events}

    return store


store = create_seed_store()


def reset_store() -> None:
    global store
    store = create_seed_store()


def issue_session(user_id: str) -> SessionRecord:
    token = f"tok_{uuid4().hex}"
    expires_at = now_sg(store) + timedelta(hours=TOKEN_TTL_HOURS)
    session = SessionRecord(token=token, user_id=user_id, expires_at=expires_at)
    store.sessions[token] = session
    return session


def to_auth_response(user: UserRecord, session: SessionRecord) -> AuthSessionResponse:
    return AuthSessionResponse(
        access_token=session.token,
        token_type="bearer",
        expires_at=session.expires_at,
        user=UserSummary(id=UUID(user.id), display_name=user.display_name),
    )


def ensure_preferences(user_id: str) -> PreferenceProfile:
    existing = store.preferences.get(user_id)
    if existing:
        return existing
    profile = default_preference_profile(user_id=user_id, now=now_sg(store))
    store.preferences[user_id] = profile
    return profile


def build_similar_events(candidate_event: dict[str, Any]) -> list[dict[str, Any]]:
    title = str(candidate_event.get("title") or "").lower()
    candidate_start = candidate_event.get("datetime_start")
    similar_events: list[dict[str, Any]] = []

    for event in store.events.values():
        similarity = 0.35
        event_title = event.title.lower()
        if title and any(token in event_title for token in title.split()):
            similarity += 0.35
        if title and event_title in title:
            similarity += 0.25

        try:
            start_a = datetime.fromisoformat(str(candidate_start)).astimezone(SG_TZ)
            start_b = event.occurrences[0].datetime_start.astimezone(SG_TZ)
            hours_delta = abs((start_a - start_b).total_seconds()) / 3600
            if hours_delta <= 2:
                similarity += 0.2
            elif hours_delta <= 12:
                similarity += 0.1
        except ValueError:
            pass

        similar_events.append(
            {
                "event_id": event.event_id,
                "title": event.title,
                "datetime_start": event.occurrences[0].datetime_start.isoformat(),
                "venue_name": event.venue_name,
                "similarity_score": round(min(similarity, 0.99), 3),
            }
        )

    similar_events.sort(key=lambda item: item["similarity_score"], reverse=True)
    return similar_events[:5]


app = FastAPI(title="AFF API", version="1.0.0")
bearer = HTTPBearer(auto_error=False)


def request_id_for(request: Request) -> str:
    value = getattr(request.state, "request_id", None)
    if value:
        return str(value)
    fallback = make_request_id()
    request.state.request_id = fallback
    return fallback


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any],
) -> JSONResponse:
    payload = ErrorEnvelope(
        code=code,
        message=message,
        details=details,
        request_id=request_id_for(request),
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


@app.middleware("http")
async def request_id_middleware(request: Request, call_next: Callable[..., Any]) -> JSONResponse:
    request.state.request_id = make_request_id()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    return error_response(request, exc.status_code, exc.code, exc.message, exc.details)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(
        request=request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="INVALID_REQUEST",
        message="Validation failed",
        details={"errors": exc.errors()},
    )


@app.exception_handler(StarletteHTTPException)
async def starlette_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code_map = {
        400: "INVALID_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "INVALID_REQUEST",
    }
    message_map = {
        401: "Authentication required",
        403: "Forbidden",
        404: "Resource not found",
    }
    return error_response(
        request=request,
        status_code=exc.status_code,
        code=code_map.get(exc.status_code, "HTTP_ERROR"),
        message=message_map.get(exc.status_code, "Request failed"),
        details={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_response(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_ERROR",
        message="Internal server error",
        details={"error": type(exc).__name__},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> UserRecord:
    if credentials is None:
        raise APIError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="Authentication required",
            details={"auth": "bearer"},
        )

    session = store.sessions.get(credentials.credentials)
    if session is None or session.expires_at < now_sg(store):
        raise APIError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="Invalid or expired token",
            details={"token": "expired_or_unknown"},
        )

    user = store.users.get(session.user_id)
    if user is None:
        raise APIError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="Invalid session user",
            details={"user_id": session.user_id},
        )
    return user


def get_admin_user(user: UserRecord = Depends(get_current_user)) -> UserRecord:
    if user.role != "admin":
        raise APIError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="ADMIN_REQUIRED",
            message="Admin role required",
            details={"role": user.role},
        )
    return user


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/auth/demo-login", response_model=AuthSessionResponse)
def demo_login(payload: DemoLoginRequest) -> AuthSessionResponse:
    role = "admin" if (payload.persona_seed or "").strip().lower() == "admin" else "user"
    user = UserRecord(
        id=str(uuid4()),
        display_name=payload.display_name,
        email=None,
        role=role,
        created_at=now_sg(store),
    )
    store.users[user.id] = user
    ensure_preferences(user.id)
    session = issue_session(user.id)
    return to_auth_response(user, session)


@app.post("/v1/auth/login", response_model=AuthSessionResponse)
def login(payload: PasswordLoginRequest) -> AuthSessionResponse:
    normalized_email = payload.email.strip().lower()
    if not normalized_email:
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_REQUEST",
            message="Email is required",
            details={"field": "email"},
        )

    user_id = store.users_by_email.get(normalized_email)
    user: UserRecord
    if user_id and user_id in store.users:
        user = store.users[user_id]
    else:
        local_part = normalized_email.split("@", 1)[0]
        role = "admin" if "admin" in local_part else "user"
        user = UserRecord(
            id=str(uuid4()),
            display_name=local_part or "user",
            email=normalized_email,
            role=role,
            created_at=now_sg(store),
        )
        store.users[user.id] = user
        store.users_by_email[normalized_email] = user.id

    ensure_preferences(user.id)
    session = issue_session(user.id)
    return to_auth_response(user, session)


@app.get("/v1/preferences", response_model=PreferenceProfile)
def get_preferences(user: UserRecord = Depends(get_current_user)) -> PreferenceProfile:
    return ensure_preferences(user.id)


@app.put("/v1/preferences", response_model=PreferenceProfile)
def put_preferences(
    payload: PreferenceProfileInput,
    user: UserRecord = Depends(get_current_user),
) -> PreferenceProfile:
    profile = PreferenceProfile(
        user_id=UUID(user.id),
        updated_at=now_sg(store),
        **payload.model_dump(),
    )
    store.preferences[user.id] = profile
    return profile


@app.post("/v1/interactions", response_model=CreatedResponse, status_code=status.HTTP_201_CREATED)
def post_interactions(
    payload: InteractionCreateRequest,
    user: UserRecord = Depends(get_current_user),
) -> CreatedResponse:
    event_id = str(payload.event_id)
    if event_id not in store.events:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="EVENT_NOT_FOUND",
            message="Event not found",
            details={"event_id": event_id},
        )

    created = now_sg(store)
    record = InteractionRecord(
        id=str(uuid4()),
        user_id=user.id,
        event_id=event_id,
        signal=payload.signal.value,
        context=payload.context,
        created_at=created,
    )
    store.interactions.append(record)
    return CreatedResponse(id=UUID(record.id), created_at=created)


@app.get("/v1/feed", response_model=FeedResponse)
def get_feed(
    request: Request,
    lat: float,
    lng: float,
    time_window: TimeWindow,
    budget: BudgetMode,
    mode: FeedMode,
    user: UserRecord = Depends(get_current_user),
) -> FeedResponse:
    del lat, lng, mode

    profile = ensure_preferences(user.id)
    now = now_sg(store)

    items: list[FeedItem] = []
    for event in store.events.values():
        if not event_matches_window(event, time_window, now):
            continue
        score, reasons = build_feed_score(
            user_id=user.id,
            event=event,
            profile=profile,
            budget=budget,
            interactions=store.interactions,
        )
        items.append(
            FeedItem(
                event_id=UUID(event.event_id),
                title=event.title,
                datetime_start=event.occurrences[0].datetime_start,
                venue_name=event.venue_name or "",
                category=event.category,
                price=event.price,
                relevance_score=score,
                reasons=reasons,
                source_provenance=event.source_provenance,
            )
        )

    items.sort(key=lambda item: (-item.relevance_score, item.datetime_start))
    coverage_warning = None
    if len(items) < 20:
        coverage_warning = "Limited candidate coverage for selected filters."

    return FeedResponse(
        items=items,
        coverage_warning=coverage_warning,
        request_id=request_id_for(request),
    )


@app.get("/v1/events/{event_id}", response_model=EventDetail)
def get_event(event_id: UUID, user: UserRecord = Depends(get_current_user)) -> EventDetail:
    del user
    event = store.events.get(str(event_id))
    if event is None:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="EVENT_NOT_FOUND",
            message="Event not found",
            details={"event_id": str(event_id)},
        )

    return EventDetail(
        event_id=UUID(event.event_id),
        title=event.title,
        category=event.category,
        subcategory=event.subcategory,
        description=event.description,
        venue_name=event.venue_name,
        venue_address=event.venue_address,
        occurrences=event.occurrences,
        source_provenance=event.source_provenance,
    )


@app.post(
    "/v1/events/{event_id}/feedback",
    response_model=CreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_feedback(
    event_id: UUID,
    payload: EventFeedbackRequest,
    user: UserRecord = Depends(get_current_user),
) -> CreatedResponse:
    event_id_str = str(event_id)
    if event_id_str not in store.events:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="EVENT_NOT_FOUND",
            message="Event not found",
            details={"event_id": event_id_str},
        )

    created = now_sg(store)
    record = InteractionRecord(
        id=str(uuid4()),
        user_id=user.id,
        event_id=event_id_str,
        signal=payload.signal.value,
        context=payload.context,
        created_at=created,
    )
    store.interactions.append(record)
    return CreatedResponse(id=UUID(record.id), created_at=created)


@app.get("/v1/notifications", response_model=NotificationListResponse)
def get_notifications(
    limit: int = Query(default=20, ge=1, le=100),
    user: UserRecord = Depends(get_current_user),
) -> NotificationListResponse:
    items = [log for uid, log in store.notification_logs if uid == user.id]
    items.sort(key=lambda item: item.created_at, reverse=True)
    return NotificationListResponse(items=items[:limit])


@app.post(
    "/v1/notifications/test",
    response_model=TestNotificationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def post_test_notification(
    payload: TestNotificationRequest,
    user: UserRecord = Depends(get_current_user),
) -> TestNotificationResponse:
    event = store.events.get(str(payload.event_id))
    if event is None:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="EVENT_NOT_FOUND",
            message="Event not found",
            details={"event_id": str(payload.event_id)},
        )

    now = now_sg(store)
    note_status = NotificationStatus.queued
    sent_at: datetime | None = None
    if notifications_count_today(store, user.id, now) >= MAX_NOTIFICATIONS_PER_DAY:
        note_status = NotificationStatus.suppressed
    elif is_quiet_hours(now):
        note_status = NotificationStatus.suppressed

    if note_status == NotificationStatus.sent:
        sent_at = now

    notification = NotificationLog(
        id=uuid4(),
        event_id=payload.event_id,
        priority=NotificationPriority.high,
        title=f"AFF Alert: {event.title}",
        body=payload.reason,
        status=note_status,
        sent_at=sent_at,
        created_at=now,
    )
    store.notification_logs.append((user.id, notification))
    return TestNotificationResponse(
        queued=notification.status == NotificationStatus.queued,
        notification_id=notification.id,
    )


@app.get("/v1/admin/sources", response_model=SourceListResponse)
def get_admin_sources(
    status_filter: SourceStatus | None = Query(default=None, alias="status"),
    admin_user: UserRecord = Depends(get_admin_user),
) -> SourceListResponse:
    del admin_user
    items = list(store.sources.values())
    if status_filter:
        items = [source for source in items if source.status == status_filter]
    return SourceListResponse(items=items)


@app.post(
    "/v1/admin/sources",
    response_model=Source,
    status_code=status.HTTP_201_CREATED,
)
def post_admin_source(
    payload: SourceCreateRequest,
    admin_user: UserRecord = Depends(get_admin_user),
) -> Source:
    del admin_user
    normalized_url = str(payload.url)
    for source in store.sources.values():
        if str(source.url) == normalized_url:
            raise APIError(
                status_code=status.HTTP_409_CONFLICT,
                code="SOURCE_URL_CONFLICT",
                message="Source URL already exists",
                details={"url": normalized_url},
            )

    source = Source(
        id=uuid4(),
        name=payload.name,
        url=payload.url,
        source_type=payload.source_type,
        access_method=payload.access_method,
        status=SourceStatus.pending,
        policy_risk_score=0,
        quality_score=0,
        crawl_frequency_minutes=60,
        terms_url=payload.terms_url,
        notes=None,
    )
    store.sources[str(source.id)] = source
    return source


@app.post("/v1/admin/sources/{source_id}/approve", response_model=Source)
def post_admin_source_approve(
    source_id: UUID,
    payload: SourceApprovalRequest,
    admin_user: UserRecord = Depends(get_admin_user),
) -> Source:
    del admin_user
    source = store.sources.get(str(source_id))
    if source is None:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="SOURCE_NOT_FOUND",
            message="Source not found",
            details={"source_id": str(source_id)},
        )

    if payload.decision == SourceApprovalDecision.approved:
        new_status = SourceStatus.approved
    elif payload.decision == SourceApprovalDecision.rejected:
        new_status = SourceStatus.rejected
    else:
        new_status = SourceStatus.pending

    updated = source.model_copy(
        update={
            "status": new_status,
            "policy_risk_score": payload.policy_risk_score,
            "quality_score": payload.quality_score,
            "notes": payload.notes,
        }
    )
    store.sources[str(source_id)] = updated
    return updated


@app.post(
    "/v1/admin/ingestion/run",
    response_model=IngestionRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def post_admin_ingestion_run(
    payload: IngestionRunRequest,
    admin_user: UserRecord = Depends(get_admin_user),
) -> IngestionRunResponse:
    approved_sources: list[Source] = []
    for source_id in payload.source_ids:
        source = store.sources.get(str(source_id))
        if source is None:
            raise APIError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="SOURCE_NOT_FOUND",
                message="Source not found",
                details={"source_id": str(source_id)},
            )
        if source.status != SourceStatus.approved:
            raise APIError(
                status_code=status.HTTP_403_FORBIDDEN,
                code="SOURCE_NOT_APPROVED",
                message="Only approved sources can be ingested",
                details={"source_id": str(source_id), "status": source.status.value},
            )
        approved_sources.append(source)

    job_id = uuid4()
    run_id = str(job_id)
    created_events = 0
    merge_actions: list[str] = []

    for source in approved_sources:
        raw_event = {
            "raw_title": f"{source.name} Featured Event",
            "raw_date_or_schedule": now_sg(store).replace(
                hour=20,
                minute=0,
                second=0,
                microsecond=0,
            ).isoformat(),
            "raw_location": "Singapore",
            "raw_description": f"Ingestion from source {source.name}",
            "raw_price": "SGD 20-40",
            "raw_url": str(source.url),
        }

        if source.access_method == SourceAccessMethod.manual:
            raw_event["raw_date_or_schedule"] = ""
            raw_event["raw_location"] = ""

        normalized = normalize_event_agent(
            payload={"raw_event": raw_event, "city_context": "Singapore"},
            run_id=run_id,
        )
        if normalized["status"] == "error":
            store.ingestion_metrics["source_parse_failures_total"] += 1
            append_ingestion_log(
                run_id=run_id,
                level="error",
                message="Normalizer failed",
                user_id=admin_user.id,
                source_id=str(source.id),
                payload=normalized["error"],
            )
            continue

        normalized_event = normalized["data"]["normalized_event"]
        confidence_score = float(normalized_event["confidence_score"])
        if confidence_score < 0.6:
            store.ingestion_metrics["normalization_low_confidence_total"] += 1
            store.ingestion_metrics["source_parse_failures_total"] += 1
            append_ingestion_log(
                run_id=run_id,
                level="warning",
                message="Low confidence normalization",
                user_id=admin_user.id,
                source_id=str(source.id),
                payload={
                    "confidence_score": confidence_score,
                    "parsing_notes": normalized_event.get("parsing_notes"),
                },
            )

        dedup = deduplicate_event_agent(
            payload={
                "candidate_event": normalized_event,
                "similar_events": build_similar_events(normalized_event),
            },
            run_id=run_id,
        )
        if dedup["status"] == "error":
            store.ingestion_metrics["source_parse_failures_total"] += 1
            append_ingestion_log(
                run_id=run_id,
                level="error",
                message="Deduplication failed",
                user_id=admin_user.id,
                source_id=str(source.id),
                payload=dedup["error"],
            )
            continue

        decision = dedup["data"]
        action = decision["merge_action"]
        merge_actions.append(action)
        store.ingestion_metrics["dedup_merge_action_total"][action] += 1
        append_ingestion_log(
            run_id=run_id,
            level="info",
            message="Deduplication decision computed",
            user_id=admin_user.id,
            source_id=str(source.id),
            payload=decision,
        )

        if action == "create_new":
            event_id = str(uuid4())
            start = datetime.fromisoformat(normalized_event["datetime_start"]).astimezone(SG_TZ)
            end_value = normalized_event.get("datetime_end")
            end = datetime.fromisoformat(end_value).astimezone(SG_TZ) if end_value else None
            new_event = EventRecord(
                event_id=event_id,
                title=normalized_event["title"],
                category=normalized_event["category"],
                subcategory=normalized_event.get("subcategory"),
                description=normalized_event.get("description"),
                venue_name=normalized_event.get("venue_name"),
                venue_address=normalized_event.get("venue_address"),
                occurrences=[
                    EventOccurrence(
                        datetime_start=start,
                        datetime_end=end,
                        timezone="Asia/Singapore",
                    )
                ],
                price=Price(
                    min=normalized_event.get("price_min"),
                    max=normalized_event.get("price_max"),
                    currency=normalized_event.get("currency"),
                ),
                source_provenance=[
                    SourceProvenance(
                        source_id=source.id,
                        source_name=source.name,
                        source_url=str(source.url),
                    )
                ],
            )
            store.events[event_id] = new_event
            created_events += 1
            append_ingestion_log(
                run_id=run_id,
                level="info",
                message="Created canonical event from ingestion",
                user_id=admin_user.id,
                source_id=str(source.id),
                event_id=event_id,
                payload={"title": new_event.title},
            )

    store.ingestion_jobs.append(
        {
            "job_id": str(job_id),
            "source_ids": [str(source_id) for source_id in payload.source_ids],
            "reason": payload.reason,
            "queued_at": now_sg(store).isoformat(),
            "run_id": run_id,
            "created_events": created_events,
            "merge_actions": merge_actions,
        }
    )
    return IngestionRunResponse(job_id=job_id, queued_count=len(payload.source_ids))
