from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from constants import SG_TZ


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
class RawEventRecord:
    id: str
    source_id: str
    external_event_id: str | None
    payload_ref: str
    raw_title: str | None
    raw_date_or_schedule: str | None
    raw_location: str | None
    raw_description: str | None
    raw_price: str | None
    raw_url: str | None
    raw_media_url: str | None
    captured_at: datetime


@dataclass
class EventSourceLinkRecord:
    id: str
    event_id: str
    raw_event_id: str
    source_id: str
    source_url: str | None
    external_event_id: str | None
    merge_confidence: float
    first_seen_at: datetime
    last_seen_at: datetime


@dataclass
class RecommendationRecord:
    id: str
    user_id: str
    event_id: str
    context_hash: str
    rank_position: int
    relevance_score: float
    reasons: list[str]
    notify_immediately: bool
    created_at: datetime


@dataclass
class InMemoryStore:
    users: dict[str, UserRecord] = field(default_factory=dict)
    users_by_email: dict[str, str] = field(default_factory=dict)
    sessions: dict[str, SessionRecord] = field(default_factory=dict)
    preferences: dict[str, PreferenceProfile] = field(default_factory=dict)
    events: dict[str, EventRecord] = field(default_factory=dict)
    interactions: list[InteractionRecord] = field(default_factory=list)
    sources: dict[str, Source] = field(default_factory=dict)
    raw_events: dict[str, RawEventRecord] = field(default_factory=dict)
    event_source_links: list[EventSourceLinkRecord] = field(default_factory=list)
    recommendations: list[RecommendationRecord] = field(default_factory=list)
    notification_logs: list[tuple[str, NotificationLog]] = field(default_factory=list)
    ingestion_jobs: list[dict[str, Any]] = field(default_factory=list)
    ingestion_metrics: dict[str, Any] = field(default_factory=dict)
    ingestion_logs: list[dict[str, Any]] = field(default_factory=list)
    now_provider: Callable[[], datetime] = lambda: datetime.now(SG_TZ)
