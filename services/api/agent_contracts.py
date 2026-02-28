from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
import re
from typing import Any, Literal
from uuid import uuid4
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from models import CandidateEventForDedup, FlexibleObject, SimilarEventCandidate

SG_TZ = ZoneInfo("Asia/Singapore")


class DictLikeModel(BaseModel):
    def as_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="python")

    def __getitem__(self, key: str) -> Any:
        return self.as_dict()[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.as_dict().get(key, default)

    def keys(self):  # type: ignore[no-untyped-def]
        return self.as_dict().keys()

    def items(self):  # type: ignore[no-untyped-def]
        return self.as_dict().items()

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self.as_dict())

    def __len__(self) -> int:
        return len(self.as_dict())


class AgentMeta(DictLikeModel):
    agent: str
    version: str = "v1"
    run_id: str


class AgentErrorPayload(DictLikeModel):
    code: str
    message: str
    retryable: bool
    details: FlexibleObject = Field(default_factory=FlexibleObject)


class AgentOkEnvelope(DictLikeModel):
    status: Literal["ok"] = "ok"
    data: FlexibleObject
    meta: AgentMeta


class AgentErrorEnvelope(DictLikeModel):
    status: Literal["error"] = "error"
    error: AgentErrorPayload
    meta: AgentMeta


class MergeAction(str, Enum):
    skip = "skip"
    merge_sources = "merge_sources"
    create_new = "create_new"


class NormalizedEvent(BaseModel):
    title: str
    category: str
    subcategory: str | None = None
    datetime_start: str
    datetime_end: str
    is_recurring: bool
    recurrence_rule: str | None = None
    venue_name: str | None = None
    venue_address: str | None = None
    venue_lat: float | None = None
    venue_lng: float | None = None
    price_min: float | None = None
    price_max: float | None = None
    currency: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    source_url: str | None = None
    confidence_score: float
    parsing_notes: str | None = None


class DedupDecision(BaseModel):
    is_duplicate: bool
    duplicate_of_id: str | None = None
    merge_action: MergeAction
    confidence: float
    reasoning: str
    requires_manual_review: bool


class RawEventInput(BaseModel):
    model_config = ConfigDict(extra="allow")
    raw_title: str | None = None
    raw_date_or_schedule: str | None = None
    raw_location: str | None = None
    raw_description: str | None = None
    raw_price: str | None = None
    raw_url: str | None = None


class NormalizeEventPayload(BaseModel):
    raw_event: RawEventInput
    city_context: str = "Singapore"


class DeduplicatePayload(BaseModel):
    candidate_event: CandidateEventForDedup
    similar_events: list[SimilarEventCandidate]


class SourceHunterPayload(BaseModel):
    city: str
    categories: list[str]


class IngestionPayload(BaseModel):
    raw_events: list[RawEventInput]


class RecommendationCandidate(BaseModel):
    event_id: str | None = None
    category: str | None = None


class RecommendationPayload(BaseModel):
    candidate_events: list[RecommendationCandidate]
    profile: FlexibleObject | None = None


class NotificationEventPayload(BaseModel):
    event_id: str | None = None
    title: str | None = None


class NotificationComposerPayload(BaseModel):
    event: NotificationEventPayload
    notify_reason: str


class PreferenceHistoryItem(BaseModel):
    category: str | None = None
    signal: str | None = None


class ExplicitPreferences(BaseModel):
    categories: list[str] = Field(default_factory=list)
    budget_mode: str = "moderate"
    time_preferences: list[str] = Field(default_factory=lambda: ["evening"])


class PreferenceProfilerPayload(BaseModel):
    explicit_preferences: ExplicitPreferences
    interaction_history: list[PreferenceHistoryItem] = Field(default_factory=list)


def _meta(agent: str, run_id: str | None) -> AgentMeta:
    return AgentMeta(agent=agent, run_id=run_id or str(uuid4()))


def ok_envelope(agent: str, data: BaseModel, run_id: str | None = None) -> AgentOkEnvelope:
    return AgentOkEnvelope(
        data=FlexibleObject.model_validate(data.model_dump(mode="python")),
        meta=_meta(agent=agent, run_id=run_id),
    )


def error_envelope(
    agent: str,
    code: str,
    message: str,
    retryable: bool,
    details: FlexibleObject | None = None,
    run_id: str | None = None,
) -> AgentErrorEnvelope:
    return AgentErrorEnvelope(
        error=AgentErrorPayload(
            code=code,
            message=message,
            retryable=retryable,
            details=details or FlexibleObject(),
        ),
        meta=_meta(agent=agent, run_id=run_id),
    )


def _parse_datetime(raw_value: str | None, now: datetime) -> tuple[datetime, str | None, float]:
    if raw_value is None or not raw_value.strip():
        fallback = now.replace(hour=20, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return fallback, "Missing date schedule; defaulted to next evening.", 0.45

    text = raw_value.strip()
    try:
        value = datetime.fromisoformat(text)
        return value.astimezone(SG_TZ), None, 0.0
    except ValueError:
        pass

    formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %I:%M %p",
        "%d %b %Y %H:%M",
        "%d %b %Y %I:%M%p",
    ]
    for fmt in formats:
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed.replace(tzinfo=SG_TZ), None, 0.05
        except ValueError:
            continue

    lowered = text.lower()
    if "tonight" in lowered:
        tonight = now.replace(hour=20, minute=0, second=0, microsecond=0)
        if tonight < now:
            tonight += timedelta(days=1)
        return tonight, "Interpreted vague schedule as tonight 20:00.", 0.25

    fallback = now.replace(hour=20, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return fallback, f"Unable to parse schedule '{text}', used fallback.", 0.4


def _infer_category(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ["jazz", "concert", "gig", "music"]):
        return "concert"
    if any(token in lowered for token in ["food", "hawker", "dinner", "brunch"]):
        return "food_experience"
    if any(token in lowered for token in ["comedy", "club", "night", "bar"]):
        return "nightlife"
    if any(token in lowered for token in ["film", "movie", "cinema"]):
        return "film"
    return "other"


def _parse_price(raw_price: str | None) -> tuple[float | None, float | None]:
    if not raw_price:
        return None, None
    numbers = [float(value) for value in re.findall(r"\d+(?:\.\d+)?", raw_price)]
    if not numbers:
        return None, None
    if len(numbers) == 1:
        return numbers[0], numbers[0]
    return min(numbers), max(numbers)


def normalize_event_agent(
    payload: NormalizeEventPayload | dict[str, Any],
    run_id: str | None = None,
) -> AgentOkEnvelope | AgentErrorEnvelope:
    agent = "EventNormalizerAgent"
    try:
        model_payload = payload if isinstance(payload, NormalizeEventPayload) else NormalizeEventPayload.model_validate(payload)
    except ValidationError:
        return error_envelope(
            agent=agent,
            code="INVALID_INPUT_ENVELOPE",
            message="Missing raw_event object",
            retryable=False,
            details=FlexibleObject.model_validate({"required": ["raw_event", "city_context"]}),
            run_id=run_id,
        )

    raw = model_payload.raw_event
    city_context = model_payload.city_context
    now = datetime.now(SG_TZ)

    title = (raw.raw_title or "").strip() or "Untitled activity"
    datetime_start, date_note, date_penalty = _parse_datetime(raw.raw_date_or_schedule, now)

    description = raw.raw_description
    location = (raw.raw_location or "").strip() or None
    source_url = raw.raw_url
    price_min, price_max = _parse_price(raw.raw_price)

    confidence = 0.95
    parsing_notes: list[str] = []

    if raw.raw_title in (None, ""):
        confidence -= 0.35
        parsing_notes.append("Missing title; used placeholder title.")
    if date_note:
        confidence -= date_penalty
        parsing_notes.append(date_note)
    if not location:
        confidence -= 0.12
        parsing_notes.append("Missing location value.")
    if not source_url:
        confidence -= 0.08
        parsing_notes.append("Missing source URL.")

    confidence = round(max(0.0, min(confidence, 1.0)), 3)
    parsing_note_text = " | ".join(parsing_notes) if parsing_notes else None

    normalized_event = NormalizedEvent(
        title=title,
        category=_infer_category(f"{title} {description or ''}"),
        datetime_start=datetime_start.isoformat(),
        datetime_end=(datetime_start + timedelta(hours=2)).isoformat(),
        is_recurring=False,
        recurrence_rule=None,
        venue_name=location,
        venue_address=location,
        venue_lat=1.29 if city_context.lower() == "singapore" else None,
        venue_lng=103.85 if city_context.lower() == "singapore" else None,
        price_min=price_min,
        price_max=price_max,
        currency="SGD" if (price_min is not None or price_max is not None) else None,
        description=description,
        tags=[],
        source_url=source_url,
        confidence_score=confidence,
        parsing_notes=parsing_note_text,
    )
    return ok_envelope(
        agent=agent,
        data=FlexibleObject.model_validate({"normalized_event": normalized_event.model_dump(mode="python")}),
        run_id=run_id,
    )


def deduplicate_event_agent(
    payload: DeduplicatePayload | dict[str, Any],
    run_id: str | None = None,
) -> AgentOkEnvelope | AgentErrorEnvelope:
    agent = "DeduplicationAgent"
    try:
        model_payload = payload if isinstance(payload, DeduplicatePayload) else DeduplicatePayload.model_validate(payload)
    except ValidationError:
        return error_envelope(
            agent=agent,
            code="INVALID_INPUT_ENVELOPE",
            message="candidate_event and similar_events are required",
            retryable=False,
            details=FlexibleObject.model_validate({"required": ["candidate_event", "similar_events"]}),
            run_id=run_id,
        )

    similar_events = model_payload.similar_events

    if not similar_events:
        return ok_envelope(
            agent=agent,
            data=FlexibleObject.model_validate(
                {
                    "is_duplicate": False,
                    "duplicate_of_id": None,
                    "merge_action": MergeAction.create_new.value,
                    "confidence": 0.82,
                    "reasoning": "No sufficiently similar existing events.",
                    "requires_manual_review": False,
                }
            ),
            run_id=run_id,
        )

    best = max(similar_events, key=lambda item: item.similarity_score)
    similarity = round(best.similarity_score, 3)

    if similarity >= 0.92:
        merge_action = MergeAction.skip
        is_duplicate = True
        confidence = similarity
        reasoning = "Near-identical event fingerprint detected."
    elif similarity >= 0.75:
        merge_action = MergeAction.merge_sources
        is_duplicate = True
        confidence = round(similarity - 0.03, 3)
        reasoning = "Substantial overlap with existing event; merge provenance."
    else:
        merge_action = MergeAction.create_new
        is_duplicate = False
        confidence = round(max(0.52, similarity + 0.05), 3)
        reasoning = "Similarity is weak; create a new canonical event."

    decision = DedupDecision(
        is_duplicate=is_duplicate,
        duplicate_of_id=best.event_id if is_duplicate else None,
        merge_action=merge_action,
        confidence=confidence,
        reasoning=reasoning,
        requires_manual_review=confidence < 0.65,
    )
    return ok_envelope(agent=agent, data=FlexibleObject.model_validate(decision.model_dump(mode="python")), run_id=run_id)


def source_hunter_agent(
    payload: SourceHunterPayload | dict[str, Any],
    run_id: str | None = None,
) -> AgentOkEnvelope | AgentErrorEnvelope:
    agent = "SourceHunterAgent"
    try:
        model_payload = payload if isinstance(payload, SourceHunterPayload) else SourceHunterPayload.model_validate(payload)
    except ValidationError:
        return error_envelope(
            agent=agent,
            code="INVALID_INPUT_ENVELOPE",
            message="city and categories are required",
            retryable=False,
            details=FlexibleObject.model_validate({"required": ["city", "categories"]}),
            run_id=run_id,
        )

    sources: list[FlexibleObject] = []
    for category in model_payload.categories:
        slug = str(category).replace("_", "-")
        sources.append(
            FlexibleObject.model_validate(
                {
                    "name": f"{model_payload.city} {category} source",
                    "url": f"https://{slug}.example.sg/feed",
                    "source_type": "local_blog",
                    "access_method": "rss",
                    "update_frequency_estimate": "daily",
                    "reliability_score": 70,
                    "policy_risk_score": 20,
                }
            )
        )

    return ok_envelope(
        agent=agent,
        data=FlexibleObject.model_validate({"sources": [source.model_dump(mode="python") for source in sources]}),
        run_id=run_id,
    )


def ingestion_agent(
    payload: IngestionPayload | dict[str, Any],
    run_id: str | None = None,
) -> AgentOkEnvelope | AgentErrorEnvelope:
    agent = "IngestionAgent"
    try:
        model_payload = payload if isinstance(payload, IngestionPayload) else IngestionPayload.model_validate(payload)
    except ValidationError:
        return error_envelope(
            agent=agent,
            code="INVALID_INPUT_ENVELOPE",
            message="raw_events list is required",
            retryable=False,
            details=FlexibleObject.model_validate({"required": ["raw_events"]}),
            run_id=run_id,
        )

    processed = len(model_payload.raw_events)
    parseable = sum(1 for event in model_payload.raw_events if bool(event.raw_title))
    return ok_envelope(
        agent=agent,
        data=FlexibleObject.model_validate(
            {
                "processed_count": processed,
                "parseable_count": parseable,
                "failed_count": processed - parseable,
            }
        ),
        run_id=run_id,
    )


def recommendation_agent(
    payload: RecommendationPayload | dict[str, Any],
    run_id: str | None = None,
) -> AgentOkEnvelope | AgentErrorEnvelope:
    agent = "RecommendationAgent"
    try:
        model_payload = payload if isinstance(payload, RecommendationPayload) else RecommendationPayload.model_validate(payload)
    except ValidationError:
        return error_envelope(
            agent=agent,
            code="INVALID_INPUT_ENVELOPE",
            message="candidate_events list is required",
            retryable=False,
            details=FlexibleObject.model_validate({"required": ["candidate_events"]}),
            run_id=run_id,
        )

    if model_payload.profile is None:
        return error_envelope(
            agent=agent,
            code="PROFILE_NOT_FOUND",
            message="profile is required",
            retryable=True,
            details=FlexibleObject(),
            run_id=run_id,
        )

    profile_data = model_payload.profile.model_dump(mode="python")
    preferred_categories = set(profile_data.get("preferred_categories", []))
    ranked: list[FlexibleObject] = []
    for event in model_payload.candidate_events:
        score = 0.6 + (0.3 if event.category in preferred_categories else 0.0)
        ranked.append(
            FlexibleObject.model_validate(
                {
                    "event_id": event.event_id,
                    "relevance_score": round(min(score, 0.98), 3),
                    "personal_pitch": "Matched to your profile",
                    "reasons": [f"category:{event.category}"],
                    "notify_immediately": score > 0.85,
                    "notify_reason": "high_relevance" if score > 0.85 else "normal",
                }
            )
        )

    ranked.sort(key=lambda item: float(item.model_dump(mode="python")["relevance_score"]), reverse=True)
    return ok_envelope(
        agent=agent,
        data=FlexibleObject.model_validate({"ranked": [item.model_dump(mode="python") for item in ranked]}),
        run_id=run_id,
    )


def notification_composer_agent(
    payload: NotificationComposerPayload | dict[str, Any],
    run_id: str | None = None,
) -> AgentOkEnvelope | AgentErrorEnvelope:
    agent = "NotificationComposerAgent"
    try:
        model_payload = payload if isinstance(payload, NotificationComposerPayload) else NotificationComposerPayload.model_validate(payload)
    except ValidationError:
        return error_envelope(
            agent=agent,
            code="INVALID_INPUT_ENVELOPE",
            message="event and notify_reason are required",
            retryable=False,
            details=FlexibleObject.model_validate({"required": ["event", "notify_reason"]}),
            run_id=run_id,
        )

    event_id = model_payload.event.event_id or ""
    title = str(model_payload.event.title or "AFF Alert")[:100]
    body = str(model_payload.notify_reason)[:200]
    return ok_envelope(
        agent=agent,
        data=FlexibleObject.model_validate(
            {
                "title": title,
                "body": body,
                "deep_link": f"aff://events/{event_id}",
                "priority": "high",
            }
        ),
        run_id=run_id,
    )


def preference_profiler_agent(
    payload: PreferenceProfilerPayload | dict[str, Any],
    run_id: str | None = None,
) -> AgentOkEnvelope | AgentErrorEnvelope:
    agent = "PreferenceProfilerAgent"
    try:
        model_payload = payload if isinstance(payload, PreferenceProfilerPayload) else PreferenceProfilerPayload.model_validate(payload)
    except ValidationError:
        return error_envelope(
            agent=agent,
            code="INVALID_INPUT_ENVELOPE",
            message="explicit_preferences and interaction_history are required",
            retryable=False,
            details=FlexibleObject.model_validate({"required": ["explicit_preferences", "interaction_history"]}),
            run_id=run_id,
        )

    categories = list(model_payload.explicit_preferences.categories)
    boosts: dict[str, int] = {}
    penalties: dict[str, int] = {}
    for item in model_payload.interaction_history:
        category = str(item.category or "other")
        signal = item.signal
        if signal == "interested":
            boosts[category] = boosts.get(category, 0) + 1
        if signal == "not_for_me":
            penalties[category] = penalties.get(category, 0) + 1

    ranked_categories = sorted(
        categories,
        key=lambda category: boosts.get(category, 0) - penalties.get(category, 0),
        reverse=True,
    )
    profile = FlexibleObject.model_validate(
        {
            "preferred_categories": ranked_categories or categories,
            "preferred_subcategories": [],
            "price_sensitivity": model_payload.explicit_preferences.budget_mode,
            "preferred_distance_km": 8,
            "active_days": "both",
            "preferred_times": list(model_payload.explicit_preferences.time_preferences),
            "taste_descriptors": ["adaptive profile"],
            "anti_preferences": [cat for cat, value in penalties.items() if value > 0],
        }
    )
    return ok_envelope(
        agent=agent,
        data=FlexibleObject.model_validate({"profile": profile.model_dump(mode="python")}),
        run_id=run_id,
    )
