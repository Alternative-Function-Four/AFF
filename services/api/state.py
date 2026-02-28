from __future__ import annotations

from datetime import timedelta
from uuid import UUID
from uuid import uuid4

from logic import make_ingestion_metrics, now_sg
from models import (
    EventOccurrence,
    EventRecord,
    EventSourceLinkRecord,
    InMemoryStore,
    Price,
    RawEventRecord,
    Source,
    SourceAccessMethod,
    SourceProvenance,
    SourceStatus,
)


def create_seed_store() -> InMemoryStore:
    store = InMemoryStore()
    store.ingestion_metrics = make_ingestion_metrics()
    current = now_sg(store).replace(minute=0, second=0, microsecond=0)

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

    store.events = {
        "aaaaaaaa-1111-4111-8111-111111111111": EventRecord(
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
        "bbbbbbbb-2222-4222-8222-222222222222": EventRecord(
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
        "cccccccc-3333-4333-8333-333333333333": EventRecord(
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
    }

    for event in store.events.values():
        source = event.source_provenance[0]
        raw_event_id = str(uuid4())
        store.raw_events[raw_event_id] = RawEventRecord(
            id=raw_event_id,
            source_id=str(source.source_id),
            external_event_id=None,
            payload_ref=f"seed://{raw_event_id}",
            raw_title=event.title,
            raw_date_or_schedule=event.occurrences[0].datetime_start.isoformat(),
            raw_location=event.venue_name,
            raw_description=event.description,
            raw_price=(
                f"SGD {event.price.min}-{event.price.max}"
                if event.price and event.price.min is not None and event.price.max is not None
                else None
            ),
            raw_url=source.source_url,
            raw_media_url=None,
            captured_at=event.occurrences[0].datetime_start,
        )
        store.event_source_links.append(
            EventSourceLinkRecord(
                id=str(uuid4()),
                event_id=event.event_id,
                raw_event_id=raw_event_id,
                source_id=str(source.source_id),
                source_url=source.source_url,
                external_event_id=None,
                merge_confidence=0.9,
                first_seen_at=event.occurrences[0].datetime_start,
                last_seen_at=event.occurrences[0].datetime_start,
            )
        )

    return store


STORE = create_seed_store()


def reset_store() -> None:
    fresh = create_seed_store()
    STORE.__dict__.clear()
    STORE.__dict__.update(fresh.__dict__)
