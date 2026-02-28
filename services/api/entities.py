from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKeyConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import DeclarativeBase

from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), unique=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    sessions: Mapped[list["Session"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    preference: Mapped["Preference | None"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Session(Base):
    __tablename__ = "sessions"

    token: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="sessions")


class Preference(Base):
    __tablename__ = "preferences"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    preferred_categories: Mapped[list[str]] = mapped_column(JSON(), nullable=False)
    preferred_subcategories: Mapped[list[str]] = mapped_column(JSON(), nullable=False)
    budget_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    preferred_distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    home_lat: Mapped[float] = mapped_column(Float, nullable=False, default=1.3521)
    home_lng: Mapped[float] = mapped_column(Float, nullable=False, default=103.8198)
    home_address: Mapped[str] = mapped_column(String(255), nullable=False, default="Singapore")
    active_days: Mapped[str] = mapped_column(String(32), nullable=False)
    preferred_times: Mapped[list[str]] = mapped_column(JSON(), nullable=False)
    anti_preferences: Mapped[list[str]] = mapped_column(JSON(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="preference")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    access_method: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    policy_risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    quality_score: Mapped[int] = mapped_column(Integer, nullable=False)
    crawl_frequency_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    terms_url: Mapped[str | None] = mapped_column(String(512))
    notes: Mapped[str | None] = mapped_column(Text())
    page_title: Mapped[str | None] = mapped_column(String(255))
    discovery_description: Mapped[str | None] = mapped_column(Text())
    discovery_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON())
    discovered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    city: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SourceTopicLink(Base):
    __tablename__ = "source_topic_links"

    source_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    topic_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
        ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
    )


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "source_event_id",
            name="uq_events_source_source_event_id",
        ),
        UniqueConstraint("content_hash", name="uq_events_content_hash"),
        Index("ix_events_start_datetime", "start_datetime"),
        Index("ix_events_status_start_datetime", "status", "start_datetime"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_event_id: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    event_url: Mapped[str] = mapped_column(String(512), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(512))
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    subcategory: Mapped[str | None] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text())
    venue_name: Mapped[str | None] = mapped_column(String(255))
    venue_address: Mapped[str | None] = mapped_column(String(255))
    indoor_outdoor: Mapped[str] = mapped_column(String(16), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    price_min: Mapped[float | None] = mapped_column(Float)
    price_max: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="SGD")
    embedding: Mapped[list[float] | None] = mapped_column(Vector(256))  # type: ignore[call-overload]
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    occurrences: Mapped[list["EventOccurrence"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="EventOccurrence.datetime_start",
    )
    provenance: Mapped[list["EventProvenance"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )


class EventOccurrence(Base):
    __tablename__ = "event_occurrences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    datetime_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    datetime_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)

    event: Mapped["Event"] = relationship(back_populates="occurrences")


class EventProvenance(Base):
    __tablename__ = "event_provenance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_id: Mapped[str] = mapped_column(String(36), nullable=False)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(512))

    event: Mapped["Event"] = relationship(back_populates="provenance")


class RawEvent(Base):
    __tablename__ = "raw_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    external_event_id: Mapped[str | None] = mapped_column(String(255))
    payload_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_title: Mapped[str | None] = mapped_column(String(255))
    raw_date_or_schedule: Mapped[str | None] = mapped_column(String(255))
    raw_location: Mapped[str | None] = mapped_column(String(255))
    raw_description: Mapped[str | None] = mapped_column(Text())
    raw_price: Mapped[str | None] = mapped_column(String(64))
    raw_url: Mapped[str | None] = mapped_column(String(512))
    raw_media_url: Mapped[str | None] = mapped_column(String(512))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EventSourceLink(Base):
    __tablename__ = "event_source_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_id: Mapped[str] = mapped_column(String(36), nullable=False)
    raw_event_id: Mapped[str] = mapped_column(String(36), nullable=False)
    source_id: Mapped[str] = mapped_column(String(36), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(512))
    external_event_id: Mapped[str | None] = mapped_column(String(255))
    merge_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    event_id: Mapped[str] = mapped_column(String(36), nullable=False)
    signal: Mapped[str] = mapped_column(String(64), nullable=False)
    context: Mapped[dict[str, Any]] = mapped_column(JSON(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    event_id: Mapped[str] = mapped_column(String(36), nullable=False)
    context_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    rank_position: Mapped[int] = mapped_column(Integer, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)
    reasons: Mapped[list[str]] = mapped_column(JSON(), nullable=False)
    notify_immediately: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    event_id: Mapped[str] = mapped_column(String(36), nullable=False)
    priority: Mapped[str] = mapped_column(String(16), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class IngestionMetric(Base):
    __tablename__ = "ingestion_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    normalization_low_confidence_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_parse_failures_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dedup_skip_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dedup_merge_sources_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dedup_create_new_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class IngestionLog(Base):
    __tablename__ = "ingestion_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    level: Mapped[str] = mapped_column(String(32), nullable=False)
    service: Mapped[str] = mapped_column(String(64), nullable=False)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(36))
    source_id: Mapped[str | None] = mapped_column(String(36))
    event_id: Mapped[str | None] = mapped_column(String(36))
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON(), nullable=False)


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    source_ids: Mapped[list[str]] = mapped_column(JSON(), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_events: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    merge_actions: Mapped[list[str]] = mapped_column(JSON(), nullable=False)
