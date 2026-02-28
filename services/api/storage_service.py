from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import desc, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from constants import SG_TZ
from database import AsyncSessionFactory, init_db_schema
from entities import (
    Event,
    EventOccurrence,
    EventProvenance,
    EventSourceLink,
    IngestionJob,
    IngestionLog,
    IngestionMetric,
    Interaction,
    Notification,
    Preference,
    SourceTopicLink,
    Topic,
    RawEvent,
    Recommendation,
    Session,
    Source,
    User,
)
from core import make_ingestion_metrics
from models import (
    EventOccurrence as EventOccurrenceModel,
    EventRecord,
    TopicRecord,
    EventSourceLinkRecord,
    InteractionRecord,
    SourceTopicLinkRecord,
    FlexibleObject,
    NotificationLog,
    PreferenceProfile,
    Price,
    RawEventRecord,
    RecommendationRecord,
    SourceProvenance,
    Source as SourceModel,
    SessionRecord,
    SourceAccessMethod,
    SourceStatus,
    UserRecord,
)


def _as_sg_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=SG_TZ)
    return value.astimezone(SG_TZ)


def _now_sg() -> datetime:
    return _as_sg_datetime(datetime.now())


def _enum_value(value: str | SourceStatus | SourceAccessMethod) -> str:
    if hasattr(value, "value"):
        return value.value  # type: ignore[return-value]
    return str(value)


def to_user_record(row: User) -> UserRecord:
    return UserRecord(
        id=row.id,
        display_name=row.display_name,
        email=row.email,
        role=row.role,
        created_at=row.created_at,
    )


def to_session_record(row: Session) -> SessionRecord:
    return SessionRecord(token=row.token, user_id=row.user_id, expires_at=row.expires_at)


def _to_price(row: Event) -> Price | None:
    if row.price_min is None and row.price_max is None and row.currency is None:
        return None
    return Price(min=row.price_min, max=row.price_max, currency=row.currency)


def to_event_record(row: Event) -> EventRecord:
    return EventRecord(
        event_id=row.id,
        title=row.title,
        category=row.category,
        subcategory=row.subcategory,
        description=row.description,
        venue_name=row.venue_name,
        venue_address=row.venue_address,
        occurrences=[
            EventOccurrenceModel(
                datetime_start=item.datetime_start,
                datetime_end=item.datetime_end,
                timezone=item.timezone,
            )
            for item in row.occurrences
        ],
        price=_to_price(row),
        source_provenance=[
            SourceProvenance(
                source_id=UUID(item.source_id),
                source_name=item.source_name,
                source_url=str(item.source_url or ""),
            )
            for item in row.provenance
            if item.source_id
        ],
        deleted_at=row.deleted_at,
    )


def to_raw_event_record(row: RawEvent) -> RawEventRecord:
    return RawEventRecord(
        id=row.id,
        source_id=row.source_id,
        external_event_id=row.external_event_id,
        payload_ref=row.payload_ref,
        raw_title=row.raw_title,
        raw_date_or_schedule=row.raw_date_or_schedule,
        raw_location=row.raw_location,
        raw_description=row.raw_description,
        raw_price=row.raw_price,
        raw_url=row.raw_url,
        raw_media_url=row.raw_media_url,
        captured_at=row.captured_at,
        deleted_at=row.deleted_at,
    )


def to_source_model(row: Source) -> SourceModel:
    return SourceModel(
        id=row.id,
        name=row.name,
        url=row.url,
        source_type=row.source_type,
        access_method=row.access_method,
        status=row.status,
        policy_risk_score=row.policy_risk_score,
        quality_score=row.quality_score,
        crawl_frequency_minutes=row.crawl_frequency_minutes,
        page_title=row.page_title,
        discovery_description=row.discovery_description,
        discovery_metadata=FlexibleObject.model_validate(row.discovery_metadata)
        if row.discovery_metadata is not None
        else None,
        discovered_at=row.discovered_at,
        canonical_url=row.url,
        terms_url=row.terms_url,
        notes=row.notes,
        deleted_at=row.deleted_at,
    )


def to_topic_record(row: Topic) -> TopicRecord:
    return TopicRecord(
        id=row.id,
        slug=row.slug,
        name=row.name,
        city=row.city,
        description=row.description,
        is_active=row.is_active,
        created_at=row.created_at,
    )


def to_source_topic_link_record(row: SourceTopicLink) -> SourceTopicLinkRecord:
    return SourceTopicLinkRecord(
        source_id=row.source_id,
        topic_id=row.topic_id,
        created_at=row.created_at,
    )


def to_event_source_link(row: EventSourceLink) -> EventSourceLinkRecord:
    return EventSourceLinkRecord(
        id=row.id,
        event_id=row.event_id,
        raw_event_id=row.raw_event_id,
        source_id=row.source_id,
        source_url=row.source_url,
        external_event_id=row.external_event_id,
        merge_confidence=row.merge_confidence,
        first_seen_at=row.first_seen_at,
        last_seen_at=row.last_seen_at,
    )


def to_interaction(row: Interaction) -> InteractionRecord:
    return InteractionRecord(
        id=row.id,
        user_id=row.user_id,
        event_id=row.event_id,
        signal=row.signal,
        context=FlexibleObject.model_validate(row.context),
        created_at=row.created_at,
    )


def to_recommendation(row: Recommendation) -> RecommendationRecord:
    return RecommendationRecord(
        id=row.id,
        user_id=row.user_id,
        event_id=row.event_id,
        context_hash=row.context_hash,
        rank_position=row.rank_position,
        relevance_score=row.relevance_score,
        reasons=row.reasons,
        notify_immediately=row.notify_immediately,
        created_at=row.created_at,
    )


def to_notification(row: Notification) -> NotificationLog:
    return NotificationLog(
        id=UUID(row.id),
        event_id=UUID(row.event_id),
        priority=row.priority,
        title=row.title,
        body=row.body,
        status=row.status,
        sent_at=row.sent_at,
        created_at=row.created_at,
    )


def to_preference(row: Preference) -> PreferenceProfile:
    return PreferenceProfile(
        user_id=UUID(row.user_id),
        preferred_categories=row.preferred_categories,
        preferred_subcategories=row.preferred_subcategories,
        budget_mode=row.budget_mode,
        preferred_distance_km=row.preferred_distance_km,
        active_days=row.active_days,
        preferred_times=row.preferred_times,
        anti_preferences=row.anti_preferences,
        updated_at=row.updated_at,
    )


async def get_store_snapshot(session: AsyncSession) -> dict[str, Any]:
    users_result = await session.execute(select(User))
    users = [to_user_record(row) for row in users_result.scalars().all()]

    sessions_result = await session.execute(select(Session))
    sessions = [to_session_record(row) for row in sessions_result.scalars().all()]

    preferences_result = await session.execute(select(Preference))
    prefs = [to_preference(row) for row in preferences_result.scalars().all()]

    events_result = await session.execute(
        select(Event)
        .order_by(Event.title)
        .options(selectinload(Event.occurrences), selectinload(Event.provenance))
    )
    events = [to_event_record(row) for row in events_result.unique().scalars().all()]

    interactions_result = await session.execute(
        select(Interaction).order_by(desc(Interaction.created_at))
    )
    interactions = [to_interaction(row) for row in interactions_result.scalars().all()]

    sources_result = await session.execute(select(Source))
    sources = [to_source_model(row) for row in sources_result.scalars().all()]

    topics_result = await session.execute(select(Topic).where(Topic.is_active.is_(True)).order_by(Topic.name))
    topics = [to_topic_record(row) for row in topics_result.scalars().all()]

    source_topic_result = await session.execute(
        select(SourceTopicLink).order_by(
            SourceTopicLink.source_id,
            SourceTopicLink.topic_id,
        )
    )
    source_topic_links = [
        to_source_topic_link_record(row) for row in source_topic_result.scalars().all()
    ]

    raw_events_result = await session.execute(
        select(RawEvent).order_by(desc(RawEvent.captured_at))
    )
    raw_events = [to_raw_event_record(row) for row in raw_events_result.scalars().all()]

    event_links_result = await session.execute(
        select(EventSourceLink).order_by(desc(EventSourceLink.last_seen_at))
    )
    event_source_links = [
        to_event_source_link(row) for row in event_links_result.scalars().all()
    ]

    rec_result = await session.execute(
        select(Recommendation).order_by(desc(Recommendation.created_at))
    )
    recommendations = [to_recommendation(row) for row in rec_result.scalars().all()]

    job_result = await session.execute(
        select(IngestionJob).order_by(desc(IngestionJob.queued_at))
    )
    ingestion_jobs = [
        {
            "job_id": row.id,
            "source_ids": row.source_ids,
            "reason": row.reason,
            "queued_at": row.queued_at.isoformat(),
            "run_id": row.run_id,
            "created_events": row.created_events,
            "merge_actions": row.merge_actions,
        }
        for row in job_result.scalars().all()
    ]

    log_result = await session.execute(
        select(IngestionLog).order_by(desc(IngestionLog.timestamp))
    )
    ingestion_logs = [
        {
            "timestamp": row.timestamp.isoformat(),
            "level": row.level,
            "service": row.service,
            "run_id": row.run_id,
            "user_id": row.user_id,
            "source_id": row.source_id,
            "event_id": row.event_id,
            "message": row.message,
            "payload": row.payload,
        }
        for row in log_result.scalars().all()
    ]

    metric_row = (
        await session.execute(
            select(IngestionMetric).order_by(desc(IngestionMetric.id)).limit(1)
        )
    ).scalars().first()
    if metric_row is None:
        ingestion_metrics = make_ingestion_metrics()
    else:
        ingestion_metrics = {
            "normalization_low_confidence_total": metric_row.normalization_low_confidence_total,
            "source_parse_failures_total": metric_row.source_parse_failures_total,
            "dedup_merge_action_total": {
                "skip": metric_row.dedup_skip_total,
                "merge_sources": metric_row.dedup_merge_sources_total,
                "create_new": metric_row.dedup_create_new_total,
            },
        }

    notifications_result = await session.execute(
        select(Notification).order_by(desc(Notification.created_at))
    )
    notification_rows = notifications_result.scalars().all()

    return {
        "users": {item.id: item for item in users},
        "users_by_email": {
            item.email: item.id for item in users if item.email is not None
        },
        "sessions": {item.token: item for item in sessions},
        "preferences": {item.user_id: item for item in prefs},
        "events": {item.event_id: item for item in events},
        "interactions": interactions,
        "sources": {item.id: item for item in sources},
        "topics": {item.id: item for item in topics},
        "source_topic_links": source_topic_links,
        "raw_events": {item.id: item for item in raw_events},
        "event_source_links": event_source_links,
        "recommendations": recommendations,
        "notification_logs": [(row.user_id, to_notification(row)) for row in notification_rows],
        "ingestion_jobs": ingestion_jobs,
        "ingestion_metrics": ingestion_metrics,
        "ingestion_logs": ingestion_logs,
    }


async def create_default_metrics(session: AsyncSession) -> None:
    existing = await session.scalar(select(func.count()).select_from(IngestionMetric))
    if existing:
        return

    session.add(
        IngestionMetric(
            normalization_low_confidence_total=0,
            source_parse_failures_total=0,
            dedup_skip_total=0,
            dedup_merge_sources_total=0,
            dedup_create_new_total=0,
            updated_at=_now_sg(),
        )
    )
    await session.commit()


async def increment_metric(
    session: AsyncSession,
    name: str,
    action: str | None = None,
    delta: int = 1,
) -> None:
    await create_default_metrics(session)
    row = (
        await session.execute(select(IngestionMetric).order_by(desc(IngestionMetric.id)).limit(1))
    ).scalar_one_or_none()
    if row is None:
        return

    if name == "normalization_low_confidence_total":
        row.normalization_low_confidence_total += delta
    elif name == "source_parse_failures_total":
        row.source_parse_failures_total += delta
    elif name == "dedup_merge_action_total" and action:
        if action == "skip":
            row.dedup_skip_total += delta
        elif action == "merge_sources":
            row.dedup_merge_sources_total += delta
        elif action == "create_new":
            row.dedup_create_new_total += delta
    row.updated_at = _now_sg()
    await session.commit()


async def append_ingestion_log(
    session: AsyncSession,
    *,
    run_id: str,
    level: str,
    message: str,
    payload: dict[str, Any],
    user_id: str | None = None,
    source_id: str | None = None,
    event_id: str | None = None,
) -> dict[str, Any]:
    timestamp = _now_sg()
    payload_value = dict(payload)
    session.add(
        IngestionLog(
            timestamp=timestamp,
            level=level,
            service="ingestion",
            run_id=run_id,
            user_id=user_id,
            source_id=source_id,
            event_id=event_id,
            message=message,
            payload=payload_value,
        )
    )
    await session.commit()

    return {
        "timestamp": timestamp.isoformat(),
        "level": level,
        "service": "ingestion",
        "run_id": run_id,
        "user_id": user_id,
        "source_id": source_id,
        "event_id": event_id,
        "message": message,
        "payload": payload_value,
    }


async def get_user_by_id(session: AsyncSession, user_id: str) -> UserRecord | None:
    row = await session.get(User, user_id)
    return to_user_record(row) if row else None


async def get_user_by_email(session: AsyncSession, email: str) -> UserRecord | None:
    row = (
        await session.execute(select(User).where(User.email == email))
    ).scalars().first()
    return to_user_record(row) if row else None


async def create_user(session: AsyncSession, user: UserRecord) -> UserRecord:
    row = User(
        id=user.id,
        display_name=user.display_name,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
    )
    session.add(row)
    await session.commit()
    return user


async def create_or_update_session(
    session: AsyncSession,
    record: SessionRecord,
) -> SessionRecord:
    existing = await session.get(Session, record.token)
    if existing is None:
        session.add(
            Session(
                token=record.token,
                user_id=record.user_id,
                expires_at=record.expires_at,
            )
        )
    else:
        existing.expires_at = record.expires_at
    await session.commit()
    return record


async def get_session(session: AsyncSession, token: str) -> SessionRecord | None:
    row = await session.get(Session, token)
    return to_session_record(row) if row else None


async def get_preference(session_db: AsyncSession, user_id: str) -> PreferenceProfile | None:
    row = await session_db.get(Preference, str(user_id))
    return to_preference(row) if row else None


async def save_preference(
    session: AsyncSession,
    preference: PreferenceProfile,
) -> PreferenceProfile:
    row = await session.get(Preference, str(preference.user_id))
    if row is None:
        row = Preference(user_id=str(preference.user_id))
        session.add(row)

    row.preferred_categories = list(preference.preferred_categories)
    row.preferred_subcategories = list(preference.preferred_subcategories)
    row.budget_mode = preference.budget_mode.value
    row.preferred_distance_km = preference.preferred_distance_km
    row.active_days = preference.active_days.value
    row.preferred_times = [item.value for item in preference.preferred_times]
    row.anti_preferences = list(preference.anti_preferences)
    row.updated_at = preference.updated_at
    await session.commit()
    return preference


async def list_sources(
    session_db: AsyncSession,
    status_filter: SourceStatus | None = None,
) -> list[SourceModel]:
    stmt = select(Source)
    if status_filter is not None:
        stmt = stmt.where(Source.status == status_filter.value)
    rows = (await session_db.execute(stmt)).scalars().all()
    return [to_source_model(row) for row in rows]


async def list_topics(
    session_db: AsyncSession,
    topic_ids: list[str] | None = None,
    include_inactive: bool = False,
) -> list[TopicRecord]:
    stmt = select(Topic)
    if topic_ids:
        stmt = stmt.where(Topic.id.in_(topic_ids))
    if not include_inactive:
        stmt = stmt.where(Topic.is_active.is_(True))
    rows = (await session_db.execute(stmt)).scalars().all()
    return [to_topic_record(row) for row in rows]


async def get_topic(session_db: AsyncSession, topic_id: str) -> TopicRecord | None:
    row = await session_db.get(Topic, topic_id)
    return to_topic_record(row) if row else None


async def get_source(session_db: AsyncSession, source_id: str) -> SourceModel | None:
    row = await session_db.get(Source, source_id)
    return to_source_model(row) if row else None


async def source_exists_with_url(session_db: AsyncSession, url: str) -> bool:
    row = await session_db.execute(
        select(Source).where(Source.url == str(url)).limit(1)
    )
    return row.scalars().first() is not None


async def list_source_topic_links(
    session_db: AsyncSession,
) -> list[SourceTopicLinkRecord]:
    rows = await session_db.execute(
        select(SourceTopicLink).order_by(
            SourceTopicLink.source_id,
            SourceTopicLink.topic_id,
        )
    )
    return [to_source_topic_link_record(row) for row in rows.scalars().all()]


async def create_source(session_db: AsyncSession, source: SourceModel) -> SourceModel:
    canonical_url = source.canonical_url or str(source.url)
    row = Source(
        id=str(source.id),
        name=source.name,
        url=canonical_url,
        source_type=source.source_type,
        access_method=_enum_value(source.access_method),
        status=_enum_value(source.status),
        policy_risk_score=source.policy_risk_score,
        quality_score=source.quality_score,
        crawl_frequency_minutes=source.crawl_frequency_minutes,
        page_title=source.page_title,
        discovery_description=source.discovery_description,
        discovery_metadata=dict(source.discovery_metadata) if source.discovery_metadata else None,
        discovered_at=source.discovered_at,
        terms_url=source.terms_url,
        notes=source.notes,
        deleted_at=source.deleted_at,
    )
    session_db.add(row)
    await session_db.commit()
    return to_source_model(row)


async def save_source(session_db: AsyncSession, source: SourceModel) -> SourceModel:
    row = await session_db.get(Source, str(source.id))
    if row is None:
        return await create_source(session_db, source)

    row.name = source.name
    row.url = str(source.url)
    row.source_type = source.source_type
    row.access_method = _enum_value(source.access_method)
    row.status = _enum_value(source.status)
    row.policy_risk_score = source.policy_risk_score
    row.quality_score = source.quality_score
    row.crawl_frequency_minutes = source.crawl_frequency_minutes
    row.page_title = source.page_title
    row.discovery_description = source.discovery_description
    row.discovery_metadata = (
        dict(source.discovery_metadata) if source.discovery_metadata else None
    )
    row.discovered_at = source.discovered_at
    row.terms_url = source.terms_url
    row.notes = source.notes
    row.deleted_at = source.deleted_at
    await session_db.commit()
    return source


async def create_source_topic_link(
    session_db: AsyncSession,
    source_id: str,
    topic_id: str,
    created_at: datetime,
) -> SourceTopicLinkRecord | None:
    existing = await session_db.execute(
        select(SourceTopicLink).where(
            SourceTopicLink.source_id == source_id,
            SourceTopicLink.topic_id == topic_id,
        ).limit(1)
    )
    if existing.scalars().first() is not None:
        return SourceTopicLinkRecord(
            source_id=source_id,
            topic_id=topic_id,
            created_at=created_at,
        )

    row = SourceTopicLink(
        source_id=source_id,
        topic_id=topic_id,
        created_at=created_at,
    )
    session_db.add(row)
    await session_db.commit()
    return SourceTopicLinkRecord(
        source_id=source_id,
        topic_id=topic_id,
        created_at=created_at,
    )


async def list_events(session_db: AsyncSession) -> list[EventRecord]:
    rows = await session_db.execute(
        select(Event)
        .order_by(Event.title)
        .options(selectinload(Event.occurrences), selectinload(Event.provenance))
    )
    return [to_event_record(row) for row in rows.unique().scalars().all()]


async def get_event(session_db: AsyncSession, event_id: str) -> EventRecord | None:
    row = (
        await session_db.execute(
            select(Event)
            .where(Event.id == event_id)
            .options(selectinload(Event.occurrences), selectinload(Event.provenance))
        )
    ).scalars().first()
    return to_event_record(row) if row else None


async def create_raw_event(session_db: AsyncSession, row: RawEventRecord) -> RawEventRecord:
    payload = RawEvent(
        id=row.id,
        source_id=row.source_id,
        external_event_id=row.external_event_id,
        payload_ref=row.payload_ref,
        raw_title=row.raw_title,
        raw_date_or_schedule=row.raw_date_or_schedule,
        raw_location=row.raw_location,
        raw_description=row.raw_description,
        raw_price=row.raw_price,
        raw_url=row.raw_url,
        raw_media_url=row.raw_media_url,
        captured_at=row.captured_at,
        deleted_at=row.deleted_at,
    )
    session_db.add(payload)
    await session_db.commit()
    return row


async def create_event(session_db: AsyncSession, row: EventRecord) -> EventRecord:
    payload = Event(
        id=row.event_id,
        title=row.title,
        category=row.category,
        subcategory=row.subcategory,
        description=row.description,
        venue_name=row.venue_name,
        venue_address=row.venue_address,
        price_min=row.price.min if row.price else None,
        price_max=row.price.max if row.price else None,
        currency=row.price.currency if row.price else None,
        deleted_at=row.deleted_at,
    )

    payload.occurrences = [
        EventOccurrence(
            event_id=row.event_id,
            datetime_start=item.datetime_start,
            datetime_end=item.datetime_end,
            timezone=item.timezone,
        )
        for item in row.occurrences
    ]
    payload.provenance = [
        EventProvenance(
            event_id=row.event_id,
            source_id=str(item.source_id),
            source_name=item.source_name,
            source_url=str(item.source_url),
        )
        for item in row.source_provenance
    ]
    session_db.add(payload)
    await session_db.commit()
    return row


async def create_event_source_link(
    session_db: AsyncSession,
    row: EventSourceLinkRecord,
) -> EventSourceLinkRecord:
    payload = EventSourceLink(
        id=row.id,
        event_id=row.event_id,
        raw_event_id=row.raw_event_id,
        source_id=row.source_id,
        source_url=row.source_url,
        external_event_id=row.external_event_id,
        merge_confidence=row.merge_confidence,
        first_seen_at=row.first_seen_at,
        last_seen_at=row.last_seen_at,
    )
    session_db.add(payload)
    await session_db.commit()
    return row


async def create_interaction(
    session_db: AsyncSession,
    row: InteractionRecord,
) -> InteractionRecord:
    payload = Interaction(
        id=row.id,
        user_id=row.user_id,
        event_id=row.event_id,
        signal=row.signal,
        context=dict(row.context),
        created_at=row.created_at,
    )
    session_db.add(payload)
    await session_db.commit()
    return row


async def list_interactions(session_db: AsyncSession) -> list[InteractionRecord]:
    rows = await session_db.execute(
        select(Interaction).order_by(Interaction.created_at)
    )
    return [to_interaction(item) for item in rows.scalars().all()]


async def create_recommendation(
    session_db: AsyncSession,
    row: RecommendationRecord,
) -> RecommendationRecord:
    payload = Recommendation(
        id=row.id,
        user_id=row.user_id,
        event_id=row.event_id,
        context_hash=row.context_hash,
        rank_position=row.rank_position,
        relevance_score=row.relevance_score,
        reasons=row.reasons,
        notify_immediately=row.notify_immediately,
        created_at=row.created_at,
    )
    session_db.add(payload)
    await session_db.commit()
    return row


async def create_notification(
    session_db: AsyncSession,
    user_id: str,
    row: NotificationLog,
) -> NotificationLog:
    payload = Notification(
        id=str(row.id),
        user_id=user_id,
        event_id=str(row.event_id),
        priority=_enum_value(row.priority),
        title=row.title,
        body=row.body,
        status=_enum_value(row.status),
        sent_at=row.sent_at,
        created_at=row.created_at,
    )
    session_db.add(payload)
    await session_db.commit()
    return row


async def list_notifications_for_user(
    session_db: AsyncSession,
    user_id: str,
    limit: int,
) -> list[tuple[str, NotificationLog]]:
    rows = await session_db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(desc(Notification.created_at))
        .limit(limit)
    )
    return [(row.user_id, to_notification(row)) for row in rows.scalars().all()]


async def create_ingestion_job(
    session_db: AsyncSession,
    *,
    job_id: str,
    source_ids: list[str],
    reason: str,
    queued_at: datetime,
    run_id: str,
    created_events: int,
    merge_actions: list[str],
) -> None:
    session_db.add(
        IngestionJob(
            id=job_id,
            source_ids=source_ids,
            reason=reason,
            queued_at=queued_at,
            run_id=run_id,
            created_events=created_events,
            merge_actions=merge_actions,
        )
    )
    await session_db.commit()


async def clear_all_tables(session: AsyncSession) -> None:
    await session.execute(delete(SourceTopicLink))
    await session.execute(delete(IngestionLog))
    await session.execute(delete(IngestionJob))
    await session.execute(delete(Recommendation))
    await session.execute(delete(Notification))
    await session.execute(delete(Interaction))
    await session.execute(delete(EventSourceLink))
    await session.execute(delete(EventOccurrence))
    await session.execute(delete(EventProvenance))
    await session.execute(delete(Event))
    await session.execute(delete(RawEvent))
    await session.execute(delete(Source))
    await session.execute(delete(Topic))
    await session.execute(delete(Preference))
    await session.execute(delete(Session))
    await session.execute(delete(IngestionMetric))
    await session.execute(delete(User))
    await session.commit()


async def seed_initial_data(session: AsyncSession) -> dict[str, Any]:
    await clear_all_tables(session)

    current = _now_sg().replace(minute=0, second=0, microsecond=0)

    source_a = Source(
        id="11111111-1111-1111-1111-111111111111",
        name="SG Arts Calendar",
        url="https://events.example.sg/arts",
        source_type="arts",
        access_method="rss",
        status="approved",
        policy_risk_score=10,
        quality_score=82,
        crawl_frequency_minutes=60,
        terms_url="https://events.example.sg/terms",
        notes="Seed source",
        deleted_at=None,
    )
    source_b = Source(
        id="22222222-2222-2222-2222-222222222222",
        name="SG Food Picks",
        url="https://food.example.sg/listings",
        source_type="food",
        access_method="api",
        status="approved",
        policy_risk_score=8,
        quality_score=78,
        crawl_frequency_minutes=45,
        terms_url="https://food.example.sg/terms",
        notes="Seed source",
        deleted_at=None,
    )
    source_c = Source(
        id="33333333-3333-3333-3333-333333333333",
        name="Nightlife Picks",
        url="https://night.example.sg/today",
        source_type="nightlife",
        access_method="ics",
        status="approved",
        policy_risk_score=15,
        quality_score=75,
        crawl_frequency_minutes=90,
        terms_url="https://night.example.sg/terms",
        notes="Seed source",
        deleted_at=None,
    )
    session.add_all([source_a, source_b, source_c])
    await session.flush()

    topic_events = Topic(
        id="aaaaaaaa-aaaa-4aaa-aaaa-aaaaaaaaaaa1",
        slug="events",
        name="Events",
        city="Singapore",
        description="Singapore event calendars and listings.",
        is_active=True,
        created_at=current,
    )
    topic_food = Topic(
        id="bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbb2",
        slug="food",
        name="Food",
        city="Singapore",
        description="Food and dining related listings.",
        is_active=True,
        created_at=current,
    )
    topic_nightlife = Topic(
        id="cccccccc-cccc-4ccc-cccc-ccccccccccc3",
        slug="nightlife",
        name="Nightlife",
        city="Singapore",
        description="Music and nightlife event sources.",
        is_active=True,
        created_at=current,
    )
    session.add_all([topic_events, topic_food, topic_nightlife])

    session.add_all([
        SourceTopicLink(
            source_id=source_a.id,
            topic_id=topic_events.id,
            created_at=current,
        ),
        SourceTopicLink(
            source_id=source_a.id,
            topic_id=topic_nightlife.id,
            created_at=current,
        ),
        SourceTopicLink(
            source_id=source_b.id,
            topic_id=topic_food.id,
            created_at=current,
        ),
        SourceTopicLink(
            source_id=source_c.id,
            topic_id=topic_nightlife.id,
            created_at=current,
        ),
    ])

    event_a = Event(
        id="aaaaaaaa-1111-4111-8111-111111111111",
        title="Rooftop Jazz Session",
        category="events",
        subcategory="indie_music",
        description="Sunset live jazz with city skyline.",
        venue_name="Esplanade",
        venue_address="1 Esplanade Dr",
        price_min=20,
        price_max=40,
        currency="SGD",
        deleted_at=None,
    )
    event_b = Event(
        id="bbbbbbbb-2222-4222-8222-222222222222",
        title="Late Night Hawker Crawl",
        category="food",
        subcategory="hawker",
        description="Guided food tour across two hawker centers.",
        venue_name="Maxwell Food Centre",
        venue_address="1 Kadayanallur St",
        price_min=15,
        price_max=25,
        currency="SGD",
        deleted_at=None,
    )
    event_c = Event(
        id="cccccccc-3333-4333-8333-333333333333",
        title="Underground Comedy Open Mic",
        category="nightlife",
        subcategory="comedy",
        description="Indie stand-up showcase.",
        venue_name="The Projector",
        venue_address="6001 Beach Rd",
        price_min=18,
        price_max=35,
        currency="SGD",
        deleted_at=None,
    )

    event_a.occurrences = [
        EventOccurrence(
            event_id=event_a.id,
            datetime_start=current + timedelta(days=1, hours=2),
            datetime_end=current + timedelta(days=1, hours=5),
            timezone="Asia/Singapore",
        )
    ]
    event_b.occurrences = [
        EventOccurrence(
            event_id=event_b.id,
            datetime_start=current + timedelta(days=1, hours=4),
            datetime_end=current + timedelta(days=1, hours=7),
            timezone="Asia/Singapore",
        )
    ]
    event_c.occurrences = [
        EventOccurrence(
            event_id=event_c.id,
            datetime_start=current + timedelta(days=2, hours=3),
            datetime_end=current + timedelta(days=2, hours=6),
            timezone="Asia/Singapore",
        )
    ]
    event_a.provenance = [
        EventProvenance(
            event_id=event_a.id,
            source_id=source_a.id,
            source_name=source_a.name,
            source_url=str(source_a.url),
        )
    ]
    event_b.provenance = [
        EventProvenance(
            event_id=event_b.id,
            source_id=source_b.id,
            source_name=source_b.name,
            source_url=str(source_b.url),
        )
    ]
    event_c.provenance = [
        EventProvenance(
            event_id=event_c.id,
            source_id=source_c.id,
            source_name=source_c.name,
            source_url=str(source_c.url),
        )
    ]
    session.add_all([event_a, event_b, event_c])

    for source, event in ((source_a, event_a), (source_b, event_b), (source_c, event_c)):
        raw_id = str(uuid4())
        session.add(
            RawEvent(
                id=raw_id,
                source_id=source.id,
                external_event_id=None,
                payload_ref=f"seed://{raw_id}",
                raw_title=event.title,
                raw_date_or_schedule=event.occurrences[0].datetime_start.isoformat(),
                raw_location=event.venue_name,
                raw_description=event.description,
                raw_price=(
                    f"SGD {event.price_min}-{event.price_max}"
                    if event.price_min is not None and event.price_max is not None
                    else None
                ),
                raw_url=str(source.url),
                raw_media_url=None,
                captured_at=event.occurrences[0].datetime_start,
                deleted_at=None,
            )
        )
        session.add(
            EventSourceLink(
                id=str(uuid4()),
                event_id=event.id,
                raw_event_id=raw_id,
                source_id=source.id,
                source_url=str(source.url),
                external_event_id=None,
                merge_confidence=0.9,
                first_seen_at=event.occurrences[0].datetime_start,
                last_seen_at=event.occurrences[0].datetime_start,
            )
        )

    await create_default_metrics(session)
    await session.commit()

    return await get_store_snapshot(session)


async def ensure_seed_data(session: AsyncSession) -> dict[str, Any]:
    existing_count = await session.scalar(select(func.count(Event.id)))
    if existing_count:
        return await get_store_snapshot(session)
    return await seed_initial_data(session)


async def reset_store_snapshot() -> dict[str, Any]:
    await init_db_schema()
    async with AsyncSessionFactory() as db:
        return await seed_initial_data(db)
