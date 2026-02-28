from __future__ import annotations

from datetime import timedelta
import hashlib
import math
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from constants import MAX_NOTIFICATIONS_PER_DAY, TOKEN_TTL_HOURS
from dependencies import APIError, get_current_user, get_db_session, request_id_for
from core import is_quiet_hours, now_sg
from logic import (
    build_feed_score,
    default_preference_profile,
    event_matches_window,
    notifications_count_today,
)
from models import (
    AuthSessionResponse,
    BudgetMode,
    CreatedResponse,
    DemoLoginRequest,
    EventDetail,
    EventFeedbackRequest,
    FeedItem,
    FeedMode,
    FeedResponse,
    InteractionCreateRequest,
    InteractionRecord,
    NotificationListResponse,
    NotificationLog,
    NotificationPriority,
    NotificationStatus,
    PasswordLoginRequest,
    PersonalizedFeedItem,
    PersonalizedFeedRequest,
    PersonalizedFeedResponse,
    PreferenceProfile,
    PreferenceProfileInput,
    RecommendationRecord,
    ScoreBreakdown,
    TestNotificationRequest,
    TestNotificationResponse,
    TimeWindow,
    SessionRecord,
    UserRecord,
    UserSummary,
)
from state import STORE, refresh_store_from_db
from storage_service import (
    create_interaction,
    create_notification,
    create_or_update_session,
    create_recommendation,
    create_user,
    get_event as get_event_record,
    get_preference,
    get_user_by_email,
    list_events,
    list_interactions,
    list_notifications_for_user,
    list_personalized_event_candidates,
    save_preference,
)

router = APIRouter()


async def issue_session(db: AsyncSession, user_id: str) -> SessionRecord:
    token = f"tok_{uuid4().hex}"
    expires_at = now_sg(STORE) + timedelta(hours=TOKEN_TTL_HOURS)
    session = SessionRecord(token=token, user_id=user_id, expires_at=expires_at)
    await create_or_update_session(db, session)
    return session


def to_auth_response(user: UserRecord, session: SessionRecord) -> AuthSessionResponse:
    return AuthSessionResponse(
        access_token=session.token,
        token_type="bearer",
        expires_at=session.expires_at,
        user=UserSummary(id=UUID(user.id), display_name=user.display_name),
    )


async def ensure_preferences(db: AsyncSession, user_id: str) -> PreferenceProfile:
    existing = await get_preference(db, user_id)
    if existing:
        return existing

    profile = default_preference_profile(user_id=user_id, now=now_sg(STORE))
    await save_preference(db, profile)
    return profile


def _build_query_embedding(payload: PersonalizedFeedRequest, profile: PreferenceProfile) -> list[float]:
    seed_text = " ".join(
        [
            payload.query_text or "",
            " ".join(payload.categories or profile.preferred_categories),
            " ".join(payload.subcategories or profile.preferred_subcategories),
            " ".join(profile.anti_preferences),
        ]
    ).strip()
    if not seed_text:
        return [0.0] * 8

    dims = 8
    vector = [0.0] * dims
    for token in seed_text.lower().split():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for index in range(dims):
            bucket = digest[index]
            vector[index] += (bucket / 255.0) - 0.5
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return [0.0] * dims
    return [round(value / norm, 6) for value in vector]


def _apply_diversity(
    candidates: list[dict[str, object]],
    *,
    diversity_strength: float,
    limit: int,
) -> list[dict[str, object]]:
    remaining = candidates[:]
    selected: list[dict[str, object]] = []
    category_counts: dict[str, int] = {}

    while remaining and len(selected) < limit:
        best_idx = 0
        best_adjusted = -1.0
        for idx, item in enumerate(remaining):
            category = str(item.get("category") or "")
            base_score = float(item.get("blended_score") or 0.0)
            category_repeat = category_counts.get(category, 0)
            penalty = diversity_strength * (0.15 * category_repeat)
            adjusted = max(0.0, base_score - penalty)
            if adjusted > best_adjusted:
                best_adjusted = adjusted
                best_idx = idx
        chosen = remaining.pop(best_idx)
        chosen["relevance_score"] = round(best_adjusted, 4)
        selected.append(chosen)
        category = str(chosen.get("category") or "")
        category_counts[category] = category_counts.get(category, 0) + 1
    return selected


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/v1/auth/demo-login", response_model=AuthSessionResponse)
async def demo_login(
    payload: DemoLoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> AuthSessionResponse:
    role = "admin" if (payload.persona_seed or "").strip().lower() == "admin" else "user"
    user = UserRecord(
        id=str(uuid4()),
        display_name=payload.display_name,
        email=None,
        role=role,
        created_at=now_sg(STORE),
    )
    await create_user(db, user)
    await ensure_preferences(db, user.id)
    session = await issue_session(db, user.id)
    await refresh_store_from_db(db)
    return to_auth_response(user, session)


@router.post("/v1/auth/login", response_model=AuthSessionResponse)
async def login(
    payload: PasswordLoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> AuthSessionResponse:
    normalized_email = payload.email.strip().lower()
    if not normalized_email:
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_REQUEST",
            message="Email is required",
            details={"field": "email"},
        )

    user = await get_user_by_email(db, normalized_email)
    if user is None:
        local_part = normalized_email.split("@", 1)[0]
        role = "admin" if "admin" in local_part else "user"
        user = UserRecord(
            id=str(uuid4()),
            display_name=local_part or "user",
            email=normalized_email,
            role=role,
            created_at=now_sg(STORE),
        )
        await create_user(db, user)

    await ensure_preferences(db, user.id)
    session = await issue_session(db, user.id)
    await refresh_store_from_db(db)
    return to_auth_response(user, session)


@router.get("/v1/preferences", response_model=PreferenceProfile)
async def get_preferences(
    db: AsyncSession = Depends(get_db_session),
    user: UserRecord = Depends(get_current_user),
) -> PreferenceProfile:
    return await ensure_preferences(db, user.id)


@router.put("/v1/preferences", response_model=PreferenceProfile)
async def put_preferences(
    payload: PreferenceProfileInput,
    db: AsyncSession = Depends(get_db_session),
    user: UserRecord = Depends(get_current_user),
) -> PreferenceProfile:
    profile = PreferenceProfile(
        user_id=UUID(user.id),
        updated_at=now_sg(STORE),
        **payload.model_dump(),
    )
    await save_preference(db, profile)
    await refresh_store_from_db(db)
    return profile


@router.post("/v1/interactions", response_model=CreatedResponse, status_code=status.HTTP_201_CREATED)
async def post_interactions(
    payload: InteractionCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    user: UserRecord = Depends(get_current_user),
) -> CreatedResponse:
    event_id = str(payload.event_id)
    if not await get_event_record(db, event_id):
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="EVENT_NOT_FOUND",
            message="Event not found",
            details={"event_id": event_id},
        )

    created = now_sg(STORE)
    record_id = str(uuid4())
    await create_interaction(
        db,
        InteractionRecord(
            id=record_id,
            user_id=user.id,
            event_id=event_id,
            signal=payload.signal.value,
            context=payload.context,
            created_at=created,
        ),
    )
    await refresh_store_from_db(db)
    return CreatedResponse(id=UUID(record_id), created_at=created)


@router.get("/v1/feed", response_model=FeedResponse)
async def get_feed(
    request: Request,
    lat: float,
    lng: float,
    time_window: TimeWindow,
    budget: BudgetMode,
    mode: FeedMode,
    db: AsyncSession = Depends(get_db_session),
    user: UserRecord = Depends(get_current_user),
) -> FeedResponse:
    del lat
    del lng
    del mode

    events = await list_events(db)
    interactions = await list_interactions(db)
    profile = await ensure_preferences(db, user.id)
    now = now_sg(STORE)

    items: list[FeedItem] = []
    for event in events:
        if not event_matches_window(event, time_window, now):
            continue
        score, reasons = build_feed_score(
            user_id=user.id,
            event=event,
            profile=profile,
            budget=budget,
            interactions=interactions,
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

    context_hash = hashlib.sha256(
        f"{user.id}:{time_window.value}:{budget.value}:{now}:{user.id}".encode("utf-8")
    ).hexdigest()[:16]
    created_at = now_sg(STORE)

    recommendations: list[RecommendationRecord] = []
    for index, item in enumerate(items, start=1):
        recommendations.append(
            RecommendationRecord(
                id=str(uuid4()),
                user_id=user.id,
                event_id=str(item.event_id),
                context_hash=context_hash,
                rank_position=index,
                relevance_score=item.relevance_score,
                reasons=item.reasons,
                notify_immediately=item.relevance_score >= 0.9,
                created_at=created_at,
            )
        )

    for recommendation in recommendations:
        await create_recommendation(db, recommendation)
    await refresh_store_from_db(db)

    return FeedResponse(
        items=items,
        coverage_warning=coverage_warning,
        request_id=request_id_for(request),
    )


@router.post("/v1/feed/personalized", response_model=PersonalizedFeedResponse)
async def get_personalized_feed(
    request: Request,
    payload: PersonalizedFeedRequest,
    db: AsyncSession = Depends(get_db_session),
    user: UserRecord = Depends(get_current_user),
) -> PersonalizedFeedResponse:
    profile = await ensure_preferences(db, user.id)
    now = now_sg(STORE)
    starts_after = payload.starts_after or now
    starts_before = payload.starts_before or (now + timedelta(days=14))
    categories = payload.categories or list(profile.preferred_categories)
    subcategories = payload.subcategories or list(profile.preferred_subcategories)
    query_embedding = _build_query_embedding(payload, profile)

    candidates = await list_personalized_event_candidates(
        db,
        query_embedding=query_embedding,
        categories=categories,
        subcategories=subcategories,
        starts_after=starts_after,
        starts_before=starts_before,
        max_price=payload.max_price,
        limit=payload.limit,
    )
    diversified = _apply_diversity(
        candidates,
        diversity_strength=payload.diversity_strength,
        limit=payload.limit,
    )

    items: list[PersonalizedFeedItem] = []
    for item in diversified:
        reasons = [
            "Vector similarity match",
            "Recent and timely event",
            "Popularity and source quality adjusted",
        ]
        if categories and str(item["category"]) in categories:
            reasons.append("Matches hard category filter")

        items.append(
            PersonalizedFeedItem(
                event_id=UUID(str(item["event_id"])),
                title=str(item["title"]),
                category=str(item["category"]),
                subcategory=(
                    str(item["subcategory"])
                    if item.get("subcategory") is not None
                    else None
                ),
                datetime_start=item["next_start"],
                venue_name=(
                    str(item["venue_name"])
                    if item.get("venue_name") is not None
                    else None
                ),
                price=(
                    None
                    if item.get("price_min") is None
                    and item.get("price_max") is None
                    and item.get("currency") is None
                    else {
                        "min": item.get("price_min"),
                        "max": item.get("price_max"),
                        "currency": item.get("currency"),
                    }
                ),
                relevance_score=float(item["relevance_score"]),
                score_breakdown=ScoreBreakdown(
                    blended=float(item["blended_score"]),
                    similarity=float(item["score_similarity"]),
                    freshness=float(item["score_freshness"]),
                    popularity=float(item["score_popularity"]),
                    quality=float(item["score_quality"]),
                ),
                reasons=reasons,
            )
        )

    return PersonalizedFeedResponse(items=items, request_id=request_id_for(request))


@router.get("/v1/events/{event_id}", response_model=EventDetail)
async def get_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user: UserRecord = Depends(get_current_user),
) -> EventDetail:
    del user
    event = await get_event_record(db, str(event_id))
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


@router.post(
    "/v1/events/{event_id}/feedback",
    response_model=CreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_feedback(
    event_id: UUID,
    payload: EventFeedbackRequest,
    db: AsyncSession = Depends(get_db_session),
    user: UserRecord = Depends(get_current_user),
) -> CreatedResponse:
    event_id_str = str(event_id)
    if not await get_event_record(db, event_id_str):
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="EVENT_NOT_FOUND",
            message="Event not found",
            details={"event_id": event_id_str},
        )

    created = now_sg(STORE)
    record_id = str(uuid4())
    await create_interaction(
        db,
        InteractionRecord(
            id=record_id,
            user_id=user.id,
            event_id=event_id_str,
            signal=payload.signal.value,
            context=payload.context,
            created_at=created,
        ),
    )
    await refresh_store_from_db(db)
    return CreatedResponse(id=UUID(record_id), created_at=created)


@router.get("/v1/notifications", response_model=NotificationListResponse)
async def get_notifications(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    user: UserRecord = Depends(get_current_user),
) -> NotificationListResponse:
    rows = await list_notifications_for_user(db, user.id, limit)
    return NotificationListResponse(items=[notification for _, notification in rows])


@router.post(
    "/v1/notifications/test",
    response_model=TestNotificationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def post_test_notification(
    payload: TestNotificationRequest,
    db: AsyncSession = Depends(get_db_session),
    user: UserRecord = Depends(get_current_user),
) -> TestNotificationResponse:
    await refresh_store_from_db(db)
    event = await get_event_record(db, str(payload.event_id))
    if event is None:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="EVENT_NOT_FOUND",
            message="Event not found",
            details={"event_id": str(payload.event_id)},
        )

    now = now_sg(STORE)
    note_status = NotificationStatus.queued
    if notifications_count_today(STORE, user.id, now) >= MAX_NOTIFICATIONS_PER_DAY:
        note_status = NotificationStatus.suppressed
    elif is_quiet_hours(now):
        note_status = NotificationStatus.suppressed

    notification = NotificationLog(
        id=uuid4(),
        event_id=payload.event_id,
        priority=NotificationPriority.high,
        title=f"AFF Alert: {event.title}",
        body=payload.reason,
        status=note_status,
        sent_at=None,
        created_at=now,
    )
    await create_notification(db, user.id, notification)
    await refresh_store_from_db(db)

    return TestNotificationResponse(
        queued=notification.status == NotificationStatus.queued,
        notification_id=notification.id,
    )
