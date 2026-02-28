from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import hashlib
import os
from typing import Any, Literal, cast
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from uuid import uuid4

from bs4 import BeautifulSoup
import httpx
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.settings import settings
from entities import (
    Event,
    EventOccurrence,
    EventProvenance,
    EventSourceLink,
    IngestionLog,
    RawEvent,
    Source,
)
from storage_service import append_ingestion_log, increment_metric


class ExtractedEvent(BaseModel):
    source_event_id: str | None = None
    title: str = Field(min_length=1)
    description: str | None = None
    category: str
    start_datetime: datetime
    end_datetime: datetime | None = None
    venue_name: str | None = None
    venue_address: str | None = None
    indoor_outdoor: Literal["indoor", "outdoor"]
    latitude: float | None = None
    longitude: float | None = None
    price_min: float | None = None
    price_max: float | None = None
    currency: str = "SGD"
    event_url: str
    image_url: str | None = None
    status: str = "active"


class EventIngestionSummary(BaseModel):
    run_id: str
    source_ids: list[str] = Field(default_factory=list)
    processed_sources: int = 0
    crawled_pages: int = 0
    extracted_events: int = 0
    created_events: int = 0
    updated_events: int = 0
    skipped_events: int = 0
    rejected_events: int = 0
    failed_sources: int = 0
    merge_actions: list[str] = Field(default_factory=list)


@dataclass
class CrawledPage:
    url: str
    content: str


@dataclass
class CrawlRuntime:
    client: httpx.AsyncClient
    extraction_agent: Agent[None, list[ExtractedEvent]]
    robots_cache: dict[str, RobotFileParser] = field(default_factory=dict)
    domain_semaphores: dict[str, asyncio.Semaphore] = field(default_factory=dict)


def _normalize_text(value: str | None) -> str:
    return " ".join((value or "").strip().split())


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _canonical_url(url: str) -> str:
    parsed = urlparse(url)
    return str(parsed._replace(fragment=""))


def _embedding_text(event: ExtractedEvent) -> str:
    return _normalize_text(
        "\n".join(
            [
                event.title,
                event.description or "",
                event.venue_name or "",
                event.venue_address or "",
                event.category,
            ]
        )
    )


def _content_hash(event: ExtractedEvent) -> str:
    payload = "|".join(
        [
            event.title.lower(),
            (event.description or "").lower(),
            event.category.lower(),
            (event.venue_name or "").lower(),
            (event.venue_address or "").lower(),
            _to_utc(event.start_datetime).isoformat(),
            _to_utc(event.end_datetime).isoformat() if event.end_datetime else "",
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalize_vector(values: list[float]) -> list[float]:
    norm_sq = sum(item * item for item in values)
    if norm_sq <= 0:
        return values
    norm = norm_sq ** 0.5
    return [item / norm for item in values]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    return float(sum(x * y for x, y in zip(a, b)))


def _require_openai_key() -> str:
    configured = settings.openai_api_key.get_secret_value() if settings.openai_api_key else ""
    env_value = os.getenv("OPENAI_API_KEY", "")
    key = configured or env_value
    if not key:
        raise RuntimeError("OPENAI_API_KEY is required for event ingestion")
    os.environ["OPENAI_API_KEY"] = key
    return key


def _build_extraction_agent() -> Agent[None, list[ExtractedEvent]]:
    _require_openai_key()
    if not settings.event_ingestion_model:
        raise RuntimeError("event_ingestion_model is required")

    from pydantic_ai.models.openai import OpenAIChatModel

    model = OpenAIChatModel(settings.event_ingestion_model)
    return Agent(model=model, output_type=list[ExtractedEvent], name="EventExtractionAgent")


def _build_embedding_client() -> Any:
    key = _require_openai_key()
    if not settings.event_embedding_model:
        raise RuntimeError("event_embedding_model is required")

    from openai import AsyncOpenAI

    return AsyncOpenAI(api_key=key)


async def _embed_text(client: Any, text: str) -> list[float]:
    body = _normalize_text(text)
    if not body:
        raise ValueError("embedding text cannot be empty")
    request: dict[str, Any] = {
        "model": settings.event_embedding_model,
        "input": body,
    }
    if settings.event_embedding_model.startswith("text-embedding-3"):
        request["dimensions"] = settings.event_embedding_dimensions

    response = await client.embeddings.create(**request)
    vector = [float(value) for value in response.data[0].embedding]

    expected = settings.event_embedding_dimensions
    if len(vector) != expected:
        raise RuntimeError(f"unexpected embedding dimensions {len(vector)} != {expected}")

    return _normalize_vector(vector)


async def _get_robots_parser(runtime: CrawlRuntime, source_url: str) -> RobotFileParser:
    parsed = urlparse(source_url)
    domain_key = parsed.netloc.lower()
    cached = runtime.robots_cache.get(domain_key)
    if cached is not None:
        return cached

    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    lines: list[str] | None = None

    retries = max(1, settings.event_ingestion_retry_attempts)
    for attempt in range(retries):
        try:
            response = await runtime.client.get(robots_url, timeout=8.0)
            if response.status_code >= 400:
                raise RuntimeError(f"robots_http_{response.status_code}")
            lines = response.text.splitlines()
            break
        except Exception:
            if attempt == retries - 1:
                raise
            backoff = settings.event_ingestion_retry_base_seconds * (2**attempt)
            await asyncio.sleep(backoff)

    parser = RobotFileParser()
    parser.parse(lines or [])
    runtime.robots_cache[domain_key] = parser
    return parser


async def _fetch_url(runtime: CrawlRuntime, url: str) -> str | None:
    parser = await _get_robots_parser(runtime, url)
    if not parser.can_fetch(settings.event_ingestion_user_agent, url):
        return None

    parsed = urlparse(url)
    semaphore = runtime.domain_semaphores.setdefault(
        parsed.netloc.lower(),
        asyncio.Semaphore(max(1, settings.event_ingestion_domain_concurrency)),
    )

    retries = max(1, settings.event_ingestion_retry_attempts)
    async with semaphore:
        for attempt in range(retries):
            try:
                response = await runtime.client.get(url, timeout=12.0, follow_redirects=True)
                if response.status_code >= 500:
                    raise RuntimeError(f"source_http_{response.status_code}")
                if response.status_code >= 400:
                    return None
                return response.text
            except Exception:
                if attempt == retries - 1:
                    return None
                backoff = settings.event_ingestion_retry_base_seconds * (2**attempt)
                await asyncio.sleep(backoff)

    return None


def _extract_links(source_url: str, html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    root = urlparse(source_url)
    seen = {source_url}
    links = [source_url]

    for anchor in soup.select("a[href]"):
        href = str(anchor.get("href") or "").strip()
        if not href:
            continue

        absolute = _canonical_url(urljoin(source_url, href))
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"}:
            continue
        if parsed.netloc.lower() != root.netloc.lower():
            continue
        if absolute in seen:
            continue

        seen.add(absolute)
        links.append(absolute)
        if len(links) >= settings.event_ingestion_max_links_per_page:
            break

    return links


def _page_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return _normalize_text(soup.get_text(" ", strip=True))


async def _crawl_source_pages(runtime: CrawlRuntime, source: Source) -> list[CrawledPage]:
    start_url = str(source.url)
    root_html = await _fetch_url(runtime, start_url)
    if root_html is None:
        return []

    page_urls = _extract_links(start_url, root_html)[: settings.event_ingestion_max_pages_per_source]

    pages: list[CrawledPage] = []
    for page_url in page_urls:
        html = root_html if page_url == start_url else await _fetch_url(runtime, page_url)
        if html is None:
            continue
        text = _page_text(html)
        if not text:
            continue
        pages.append(CrawledPage(url=page_url, content=text[:9000]))

    return pages


async def _extract_events_with_llm(
    agent: Agent[None, list[ExtractedEvent]],
    source: Source,
    pages: list[CrawledPage],
) -> list[ExtractedEvent]:
    rules = {
        "city": "Singapore",
        "past_days_threshold": settings.event_ingestion_past_days_threshold,
        "required_fields": [
            "title",
            "category",
            "start_datetime",
            "event_url",
            "indoor_outdoor",
        ],
        "reject_if": [
            "not in Singapore",
            "missing or invalid date",
            "start date is older than threshold days in the past",
            "promotional non-event page",
        ],
        "datetime_timezone": "UTC",
        "status_values": ["active", "cancelled", "past"],
        "indoor_outdoor_values": ["indoor", "outdoor"],
    }

    payload = [
        {
            "url": page.url,
            "content": page.content,
        }
        for page in pages
    ]

    prompt = (
        "Extract structured real-world events from these pages.\n"
        "Apply the policy rules strictly and only return accepted events.\n"
        "For each accepted event, decide and return indoor_outdoor as exactly 'indoor' or 'outdoor' based on venue/context.\n"
        f"Rules: {rules}\n"
        f"Source metadata: name={source.name}, source_type={source.source_type}, source_url={source.url}\n"
        f"Current UTC: {datetime.now(timezone.utc).isoformat()}\n"
        f"Pages: {payload}"
    )
    result = await agent.run(prompt)

    normalized: list[ExtractedEvent] = []
    for item in result.output or []:
        event = item.model_copy()
        event.title = _normalize_text(event.title)
        event.description = _normalize_text(event.description) or None
        event.category = _normalize_text(event.category) or _normalize_text(source.source_type) or "events"
        event.venue_name = _normalize_text(event.venue_name) or None
        event.venue_address = _normalize_text(event.venue_address) or None
        normalized_indoor_outdoor = _normalize_text(event.indoor_outdoor).lower()
        if normalized_indoor_outdoor not in {"indoor", "outdoor"}:
            raise ValueError(f"invalid indoor_outdoor value: {event.indoor_outdoor}")
        event.indoor_outdoor = cast(Literal["indoor", "outdoor"], normalized_indoor_outdoor)
        event.currency = _normalize_text(event.currency) or "SGD"
        event.event_url = _canonical_url(_normalize_text(event.event_url) or str(source.url))
        event.image_url = _normalize_text(event.image_url) or None
        event.start_datetime = _to_utc(event.start_datetime)
        event.end_datetime = _to_utc(event.end_datetime) if event.end_datetime else None
        status = _normalize_text(event.status).lower()
        if status not in {"active", "cancelled", "past"}:
            raise ValueError(f"invalid event status: {event.status}")
        event.status = status
        normalized.append(event)

    return normalized


async def _find_semantic_duplicate(
    session: AsyncSession,
    *,
    embedding: list[float],
    start_datetime: datetime,
) -> tuple[Event | None, float]:
    candidates = (
        await session.execute(
            select(Event).where(
                Event.deleted_at.is_(None),
                Event.start_datetime >= start_datetime - timedelta(days=14),
                Event.start_datetime <= start_datetime + timedelta(days=14),
                Event.embedding.is_not(None),
            )
        )
    ).scalars().all()

    best: Event | None = None
    best_score = 0.0
    for candidate in candidates:
        raw_embedding = candidate.embedding
        if raw_embedding is None:
            continue
        existing = [float(item) for item in raw_embedding]
        score = _cosine_similarity(embedding, existing)
        if score > best_score:
            best = candidate
            best_score = score

    if best is None:
        return None, 0.0

    if best_score < settings.event_semantic_dedup_threshold:
        return None, best_score

    return best, best_score


def _event_changed(existing: Event, incoming: ExtractedEvent, content_hash: str) -> bool:
    if existing.content_hash != content_hash:
        return True

    pairs: list[tuple[Any, Any]] = [
        (existing.title, incoming.title),
        (existing.description, incoming.description),
        (existing.category, incoming.category),
        (existing.start_datetime, incoming.start_datetime),
        (existing.end_datetime, incoming.end_datetime),
        (existing.venue_name, incoming.venue_name),
        (existing.venue_address, incoming.venue_address),
        (existing.indoor_outdoor, incoming.indoor_outdoor),
        (existing.latitude, incoming.latitude),
        (existing.longitude, incoming.longitude),
        (existing.price_min, incoming.price_min),
        (existing.price_max, incoming.price_max),
        (existing.currency, incoming.currency),
        (existing.event_url, incoming.event_url),
        (existing.image_url, incoming.image_url),
        (existing.status, incoming.status),
    ]
    return any(left != right for left, right in pairs)


async def _ensure_occurrence(
    session: AsyncSession,
    *,
    event_id: str,
    start_datetime: datetime,
    end_datetime: datetime | None,
) -> None:
    row = (
        await session.execute(
            select(EventOccurrence)
            .where(EventOccurrence.event_id == event_id)
            .order_by(EventOccurrence.id)
            .limit(1)
        )
    ).scalars().first()

    if row is None:
        session.add(
            EventOccurrence(
                event_id=event_id,
                datetime_start=start_datetime,
                datetime_end=end_datetime,
                timezone="UTC",
            )
        )
        return

    row.datetime_start = start_datetime
    row.datetime_end = end_datetime
    row.timezone = "UTC"


async def _ensure_provenance(session: AsyncSession, *, event_id: str, source: Source) -> None:
    existing = (
        await session.execute(
            select(EventProvenance).where(
                EventProvenance.event_id == event_id,
                EventProvenance.source_id == source.id,
            )
        )
    ).scalars().first()

    if existing is not None:
        return

    session.add(
        EventProvenance(
            event_id=event_id,
            source_id=source.id,
            source_name=source.name,
            source_url=str(source.url),
        )
    )


async def _record_source_result(
    session: AsyncSession,
    *,
    run_id: str,
    source_id: str,
    success: bool,
    payload: dict[str, Any],
    user_id: str | None,
) -> None:
    await append_ingestion_log(
        session,
        run_id=run_id,
        level="info" if success else "error",
        message="Source crawl succeeded" if success else "Source crawl failed",
        source_id=source_id,
        user_id=user_id,
        payload=payload,
    )


async def _consecutive_failure_count(session: AsyncSession, *, source_id: str, lookback: int) -> int:
    rows = (
        await session.execute(
            select(IngestionLog.message)
            .where(
                IngestionLog.source_id == source_id,
                IngestionLog.message.in_(["Source crawl failed", "Source crawl succeeded"]),
            )
            .order_by(IngestionLog.timestamp.desc())
            .limit(max(1, lookback))
        )
    ).scalars().all()

    failures = 0
    for message in rows:
        if message == "Source crawl failed":
            failures += 1
            continue
        break
    return failures


async def _maybe_pause_source(session: AsyncSession, *, source: Source) -> None:
    threshold = max(1, settings.event_ingestion_failure_threshold)
    failures = await _consecutive_failure_count(session, source_id=source.id, lookback=threshold)
    if failures < threshold:
        return

    if source.status != "paused":
        source.status = "paused"
        note = f"Auto-paused after {failures} consecutive ingestion failures"
        source.notes = f"{source.notes} | {note}" if source.notes else note
        await session.commit()


async def _create_raw_event(
    session: AsyncSession,
    *,
    source: Source,
    event: ExtractedEvent,
    run_id: str,
    event_index: int,
    captured_at: datetime,
) -> str:
    raw_event_id = str(uuid4())
    session.add(
        RawEvent(
            id=raw_event_id,
            source_id=source.id,
            external_event_id=event.source_event_id,
            payload_ref=f"crawler://{run_id}/{source.id}/{event_index}",
            raw_title=event.title,
            raw_date_or_schedule=event.start_datetime.isoformat(),
            raw_location=_normalize_text(event.venue_name or event.venue_address),
            raw_description=event.description,
            raw_price=(
                f"{event.currency} {event.price_min}-{event.price_max}"
                if event.price_min is not None and event.price_max is not None
                else None
            ),
            raw_url=event.event_url,
            raw_media_url=event.image_url,
            captured_at=captured_at,
            deleted_at=None,
        )
    )
    await session.commit()
    return raw_event_id


async def _upsert_event(
    session: AsyncSession,
    *,
    source: Source,
    event: ExtractedEvent,
    embedding: list[float],
    content_hash: str,
    raw_event_id: str,
    captured_at: datetime,
) -> tuple[str, str]:
    existing: Event | None = None
    similarity = 0.0

    if event.source_event_id:
        existing = (
            await session.execute(
                select(Event).where(
                    Event.source_id == source.id,
                    Event.source_event_id == event.source_event_id,
                )
            )
        ).scalars().first()

    if existing is None:
        existing = (
            await session.execute(select(Event).where(Event.content_hash == content_hash))
        ).scalars().first()

    if existing is None:
        existing, similarity = await _find_semantic_duplicate(
            session,
            embedding=embedding,
            start_datetime=event.start_datetime,
        )

    now = datetime.now(timezone.utc)
    action = "create_new"

    if existing is None:
        new_event_id = str(uuid4())
        row = Event(
            id=new_event_id,
            source_id=source.id,
            source_event_id=event.source_event_id,
            title=event.title,
            event_url=event.event_url,
            image_url=event.image_url,
            category=event.category,
            subcategory=None,
            description=event.description,
            venue_name=event.venue_name,
            venue_address=event.venue_address,
            indoor_outdoor=event.indoor_outdoor,
            latitude=event.latitude,
            longitude=event.longitude,
            start_datetime=event.start_datetime,
            end_datetime=event.end_datetime,
            price_min=event.price_min,
            price_max=event.price_max,
            currency=event.currency,
            embedding=embedding,
            content_hash=content_hash,
            status=event.status,
            created_at=now,
            updated_at=now,
            last_seen_at=captured_at,
            deleted_at=None,
        )
        session.add(row)
        await _ensure_occurrence(
            session,
            event_id=new_event_id,
            start_datetime=event.start_datetime,
            end_datetime=event.end_datetime,
        )
        await _ensure_provenance(session, event_id=new_event_id, source=source)
        target_event_id = new_event_id
    else:
        changed = _event_changed(existing, event, content_hash)
        action = "merge_sources" if changed else "skip"

        if changed:
            existing.title = event.title
            existing.description = event.description
            existing.category = event.category
            existing.venue_name = event.venue_name
            existing.venue_address = event.venue_address
            existing.indoor_outdoor = event.indoor_outdoor
            existing.latitude = event.latitude
            existing.longitude = event.longitude
            existing.start_datetime = event.start_datetime
            existing.end_datetime = event.end_datetime
            existing.price_min = event.price_min
            existing.price_max = event.price_max
            existing.currency = event.currency
            existing.event_url = event.event_url
            existing.image_url = event.image_url
            existing.embedding = embedding
            existing.content_hash = content_hash
            existing.status = event.status
            existing.updated_at = now

        existing.last_seen_at = captured_at
        if existing.source_id == source.id and existing.source_event_id is None and event.source_event_id:
            existing.source_event_id = event.source_event_id

        await _ensure_occurrence(
            session,
            event_id=existing.id,
            start_datetime=existing.start_datetime,
            end_datetime=existing.end_datetime,
        )
        await _ensure_provenance(session, event_id=existing.id, source=source)
        target_event_id = existing.id

    session.add(
        EventSourceLink(
            id=str(uuid4()),
            event_id=target_event_id,
            raw_event_id=raw_event_id,
            source_id=source.id,
            source_url=str(source.url),
            external_event_id=event.source_event_id,
            merge_confidence=max(similarity, 0.55) if existing is not None else 0.99,
            first_seen_at=captured_at,
            last_seen_at=captured_at,
        )
    )
    await session.commit()
    return target_event_id, action


async def run_event_ingestion(
    session: AsyncSession,
    *,
    source_ids: list[str],
    reason: str,
    run_id: str | None = None,
    user_id: str | None = None,
) -> EventIngestionSummary:
    del reason
    summary = EventIngestionSummary(run_id=run_id or str(uuid4()), source_ids=list(source_ids))
    if not source_ids:
        return summary

    try:
        extraction_agent = _build_extraction_agent()
        embedding_client = _build_embedding_client()
    except Exception as exc:
        for source_id in source_ids:
            await increment_metric(session, "source_parse_failures_total")
            await append_ingestion_log(
                session,
                run_id=summary.run_id,
                level="error",
                message="Source crawl failed",
                source_id=source_id,
                user_id=user_id,
                payload={"reason": "llm_unavailable", "error": str(exc)},
            )
            summary.failed_sources += 1
        return summary

    source_rows = (
        await session.execute(select(Source).where(Source.id.in_(source_ids)).order_by(Source.id))
    ).scalars().all()
    sources = {row.id: row for row in source_rows}

    async with httpx.AsyncClient(
        headers={"User-Agent": settings.event_ingestion_user_agent},
        follow_redirects=True,
    ) as client:
        runtime = CrawlRuntime(client=client, extraction_agent=extraction_agent)

        for source_id in source_ids:
            source = sources.get(source_id)
            if source is None:
                summary.failed_sources += 1
                await increment_metric(session, "source_parse_failures_total")
                await append_ingestion_log(
                    session,
                    run_id=summary.run_id,
                    level="error",
                    message="Source crawl failed",
                    source_id=source_id,
                    user_id=user_id,
                    payload={"reason": "source_not_found"},
                )
                continue

            if source.status != "approved":
                summary.failed_sources += 1
                await increment_metric(session, "source_parse_failures_total")
                await append_ingestion_log(
                    session,
                    run_id=summary.run_id,
                    level="warning",
                    message="Source crawl failed",
                    source_id=source.id,
                    user_id=user_id,
                    payload={"reason": "source_not_approved", "status": source.status},
                )
                await _maybe_pause_source(session, source=source)
                continue

            summary.processed_sources += 1
            captured_at = datetime.now(timezone.utc)

            try:
                pages = await _crawl_source_pages(runtime, source)
            except Exception as exc:
                pages = []
                await append_ingestion_log(
                    session,
                    run_id=summary.run_id,
                    level="error",
                    message="Source crawl failed",
                    source_id=source.id,
                    user_id=user_id,
                    payload={"reason": "crawl_exception", "error": str(exc)},
                )

            summary.crawled_pages += len(pages)

            if not pages:
                summary.failed_sources += 1
                await increment_metric(session, "normalization_low_confidence_total")
                await increment_metric(session, "source_parse_failures_total")
                await append_ingestion_log(
                    session,
                    run_id=summary.run_id,
                    level="warning",
                    message="Low confidence normalization",
                    source_id=source.id,
                    user_id=user_id,
                    payload={"reason": "no_pages_available"},
                )
                await _record_source_result(
                    session,
                    run_id=summary.run_id,
                    source_id=source.id,
                    success=False,
                    payload={"reason": "no_pages_available"},
                    user_id=user_id,
                )
                await _maybe_pause_source(session, source=source)
                continue

            try:
                extracted_events = await _extract_events_with_llm(
                    runtime.extraction_agent,
                    source,
                    pages,
                )
            except Exception as exc:
                extracted_events = []
                await append_ingestion_log(
                    session,
                    run_id=summary.run_id,
                    level="error",
                    message="Source crawl failed",
                    source_id=source.id,
                    user_id=user_id,
                    payload={"reason": "llm_extraction_failed", "error": str(exc)},
                )

            if not extracted_events:
                summary.failed_sources += 1
                await increment_metric(session, "normalization_low_confidence_total")
                await increment_metric(session, "source_parse_failures_total")
                await append_ingestion_log(
                    session,
                    run_id=summary.run_id,
                    level="warning",
                    message="Low confidence normalization",
                    source_id=source.id,
                    user_id=user_id,
                    payload={"reason": "llm_returned_zero_events"},
                )
                await _record_source_result(
                    session,
                    run_id=summary.run_id,
                    source_id=source.id,
                    success=False,
                    payload={"reason": "llm_returned_zero_events", "pages_fetched": len(pages)},
                    user_id=user_id,
                )
                await _maybe_pause_source(session, source=source)
                continue

            ingested_count = 0
            for index, event in enumerate(extracted_events):
                summary.extracted_events += 1
                try:
                    embedding = await _embed_text(embedding_client, _embedding_text(event))
                    hash_value = _content_hash(event)
                    raw_event_id = await _create_raw_event(
                        session,
                        source=source,
                        event=event,
                        run_id=summary.run_id,
                        event_index=index,
                        captured_at=captured_at,
                    )
                    event_id, action = await _upsert_event(
                        session,
                        source=source,
                        event=event,
                        embedding=embedding,
                        content_hash=hash_value,
                        raw_event_id=raw_event_id,
                        captured_at=captured_at,
                    )
                except Exception as exc:
                    summary.rejected_events += 1
                    await increment_metric(session, "source_parse_failures_total")
                    await append_ingestion_log(
                        session,
                        run_id=summary.run_id,
                        level="warning",
                        message="Event rejected by validity rules",
                        source_id=source.id,
                        user_id=user_id,
                        payload={
                            "title": event.title,
                            "event_url": event.event_url,
                            "reason": "ingestion_exception",
                            "error": str(exc),
                        },
                    )
                    continue

                ingested_count += 1
                summary.merge_actions.append(action)
                await increment_metric(session, "dedup_merge_action_total", action=action)
                await append_ingestion_log(
                    session,
                    run_id=summary.run_id,
                    level="info",
                    message="Event ingested",
                    source_id=source.id,
                    event_id=event_id,
                    user_id=user_id,
                    payload={
                        "action": action,
                        "content_hash": hash_value,
                        "title": event.title,
                    },
                )

                if action == "create_new":
                    summary.created_events += 1
                elif action == "merge_sources":
                    summary.updated_events += 1
                else:
                    summary.skipped_events += 1

            if ingested_count == 0:
                summary.failed_sources += 1
                await _record_source_result(
                    session,
                    run_id=summary.run_id,
                    source_id=source.id,
                    success=False,
                    payload={"reason": "all_events_rejected"},
                    user_id=user_id,
                )
                await _maybe_pause_source(session, source=source)
                continue

            await _record_source_result(
                session,
                run_id=summary.run_id,
                source_id=source.id,
                success=True,
                payload={"events_ingested": ingested_count, "pages_fetched": len(pages)},
                user_id=user_id,
            )

    return summary


async def run_scheduled_event_ingestion(
    session: AsyncSession,
    *,
    reason: str = "scheduled_sync",
    run_id: str | None = None,
) -> EventIngestionSummary:
    source_rows = (
        await session.execute(
            select(Source.id, Source.crawl_frequency_minutes)
            .where(Source.status == "approved", Source.deleted_at.is_(None))
            .order_by(Source.id)
        )
    ).all()
    if not source_rows:
        return EventIngestionSummary(run_id=run_id or str(uuid4()), source_ids=[])

    source_ids = [item[0] for item in source_rows]
    frequencies = {item[0]: int(item[1]) for item in source_rows}
    last_success_rows = (
        await session.execute(
            select(IngestionLog.source_id, func.max(IngestionLog.timestamp))
            .where(
                IngestionLog.source_id.in_(source_ids),
                IngestionLog.message == "Source crawl succeeded",
            )
            .group_by(IngestionLog.source_id)
        )
    ).all()
    last_success_at = {row[0]: row[1] for row in last_success_rows if row[0]}

    now = datetime.now(timezone.utc)
    due_sources: list[str] = []
    for source_id in source_ids:
        frequency = max(15, frequencies.get(source_id, 60))
        last = last_success_at.get(source_id)
        if last is None:
            due_sources.append(source_id)
            continue
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if now - last >= timedelta(minutes=frequency):
            due_sources.append(source_id)

    return await run_event_ingestion(
        session,
        source_ids=due_sources,
        reason=reason,
        run_id=run_id,
    )
