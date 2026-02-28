from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any
from urllib.parse import parse_qs, parse_qsl, urlencode, urlunparse, urlparse, unquote
from uuid import uuid4

import httpx
from pydantic_ai import Agent

from constants import SG_TZ
from core.settings import settings
from models import (
    SourceAccessMethod,
    SourceDiscoveryRunResponse,
    SourceStatus,
    TopicRecord,
)
from models import Source as SourceModel
from storage_service import (
    create_source,
    create_source_topic_link,
    list_source_topic_links,
    list_topics,
)
from storage_service import list_sources


TOPIC_MAX_NEW_DEFAULT = settings.source_discovery_max_new_per_topic
DEFAULT_MAX_NEW_PER_DOMAIN = settings.source_discovery_max_new_per_domain


class SourceQualityAssessment(BaseModel):
    source_name: str = Field(min_length=1)
    source_type: str = "discovered_event_listings"
    access_method: str = SourceAccessMethod.html_extract
    policy_risk_score: int = Field(ge=0, le=100)
    quality_score: int = Field(ge=0, le=100)
    crawl_frequency_minutes: int = Field(ge=15, le=10080)
    assessment_confidence: float = Field(ge=0.0, le=1.0)
    notes: str | None = None


@dataclass
class _DiscoveryRuntime:
    run_id: str
    existing_source_urls: dict[str, str]
    source_topic_links: set[tuple[str, str]]
    discovered_urls_in_run: set[str]
    created_source_urls: dict[str, str]
    domain_new_counts: dict[str, int]
    max_new_per_domain: int
    max_new_per_topic: int
    topics_processed: int = 0
    discovered_sources: int = 0
    topic_links_created: int = 0
    skipped_sources: int = 0
    failed_sources: int = 0


def _normalize_query(raw: str) -> str:
    value = raw.lower().strip()
    return re.sub(r"\s+", " ", value)


def _canonicalize_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme:
        parsed = urlparse(f"https://{url}")
    query_items = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
    ]
    path = parsed.path or ""
    path = path.rstrip("/")
    if path == "":
        path = "/"
    normalized = parsed._replace(
        scheme=parsed.scheme.lower() or "https",
        netloc=parsed.netloc.lower(),
        path=path,
        query=urlencode(query_items, doseq=True),
        fragment="",
    )
    return str(urlunparse(normalized))


def _strip_html(raw_html: str) -> str:
    return re.sub(r"<[^>]+>", " ", raw_html or "").lower()


def _extract_title(html: str) -> str | None:
    match = re.search(r"<title[^>]*>(.*?)</title>", html or "", re.IGNORECASE | re.S)
    if not match:
        return None
    return re.sub(r"\s+", " ", match.group(1)).strip()


def _extract_description(html: str) -> str | None:
    meta_patterns = [
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
    ]
    for pattern in meta_patterns:
        match = re.search(pattern, html or "", re.IGNORECASE | re.S)
        if match:
            value = match.group(1).strip()
            if value:
                return re.sub(r"\s+", " ", value).strip()

    return None


def _search_web(query: str, max_results: int = 8) -> list[str]:
    if not query.strip():
        return []

    url = "https://duckduckgo.com/html/"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; AFFSourceDiscoveryBot/1.0)"}
    try:
        with httpx.Client(timeout=8.0, headers=headers, follow_redirects=True) as client:
            response = client.get(url, params={"q": query}, timeout=8.0)
        response.raise_for_status()
    except (httpx.HTTPError, OSError):
        return []

    raw_html = response.text
    discovered_urls: list[str] = []

    candidate_links = re.findall(r'href=["\']([^"\']+)["\']', raw_html)
    for raw_link in candidate_links:
        if not raw_link:
            continue
        candidate_url = raw_link.strip()
        if not (candidate_url.startswith("http://") or candidate_url.startswith("https://")):
            if "duckduckgo.com/l/" in candidate_url and "uddg=" in candidate_url:
                parsed = urlparse(candidate_url)
                values = parse_qs(parsed.query)
                if "uddg" in values and values["uddg"]:
                    candidate_url = unquote(values["uddg"][0])
                else:
                    continue
            else:
                continue
        if not candidate_url:
            continue
        if "duckduckgo.com" in urlparse(candidate_url).netloc.lower():
            continue
        if candidate_url in discovered_urls:
            continue
        discovered_urls.append(candidate_url)
        if len(discovered_urls) >= max_results:
            break

    return discovered_urls


def _fetch_page(url: str) -> dict[str, Any]:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; AFFSourceDiscoveryBot/1.0)"}
    try:
        with httpx.Client(timeout=10.0, headers=headers, follow_redirects=True) as client:
            response = client.get(url, timeout=10.0)
        response.raise_for_status()
    except (httpx.HTTPError, OSError) as exc:
        return {"url": url, "status_code": 0, "html": "", "error": str(exc)}

    return {
        "url": str(response.url),
        "status_code": response.status_code,
        "html": response.text,
        "error": None,
    }


def _validate_event_page(url: str, html: str) -> dict[str, Any]:
    if not html:
        return {"is_relevant": False, "reason": "empty_or_unreachable"}

    title = _extract_title(html)
    description = _extract_description(html)
    text_blob = _strip_html(html)
    normalized_url = _normalize_query(url)

    event_markers = (
        "event",
        "events",
        "calendar",
        "listing",
        "listings",
        "agenda",
        "tickets",
        "show",
        "festival",
    )
    singapore_markers = (
        "singapore",
        "sg",
        "marina bay",
        "orchard",
        "sentosa",
        "orchard road",
    )

    title_text = (title or "").lower()
    body_text = text_blob.lower()
    has_event_signal = any(marker in title_text for marker in event_markers) or any(
        marker in body_text for marker in event_markers
    )
    is_sg = "singapore" in normalized_url or any(
        marker in title_text for marker in singapore_markers
    ) or any(marker in body_text for marker in singapore_markers)

    if not has_event_signal:
        return {
            "is_relevant": False,
            "reason": "missing_event_listing_signal",
            "page_title": title,
            "description": description,
            "confidence": 0.25,
        }

    confidence = 0.7 if is_sg else 0.45
    return {
        "is_relevant": is_sg,
        "reason": "ok" if is_sg else "weak_city_signal",
        "page_title": title,
        "description": description,
        "confidence": confidence,
    }


def _fallback_candidate_urls(topic: TopicRecord) -> list[str]:
    safe_slug = re.sub(r"[^a-z0-9-]", "-", topic.slug.lower())
    return [
        f"https://{safe_slug}.com/events/singapore",
        f"https://www.{safe_slug}.com/singapore/events",
        f"https://www.{safe_slug}.com/events",
        f"https://www.sg{safe_slug}.com/events",
    ]


def _as_sg_now() -> datetime:
    return datetime.now(SG_TZ)


def _build_discovery_agent() -> Agent[None, list[str]] | None:
    if settings.openai_api_key is None:
        return None

    model_name = settings.source_discovery_model
    if not model_name:
        return None

    try:
        from pydantic_ai.models.openai import OpenAIChatModel
    except Exception:
        return None

    try:
        model = OpenAIChatModel(model_name)
    except Exception:
        return None

    agent = Agent(model=model, output_type=list[str], name="SourceDiscoveryAgent")

    @agent.tool_plain
    def search_web(query: str) -> list[str]:
        return _search_web(query)

    @agent.tool_plain
    def fetch_page(url: str) -> dict[str, Any]:
        return _fetch_page(url)

    @agent.tool_plain
    def validate_event_page(url: str, html: str) -> dict[str, Any]:
        return _validate_event_page(url=url, html=html)

    @agent.tool_plain
    def check_existing_source(url: str) -> dict[str, Any]:
        return {
            "url": _canonicalize_url(url),
            "exists": False,
            "source_id": None,
            "note": "runtime check is handled in orchestration",
        }

    @agent.tool_plain
    def insert_source(data: dict[str, Any]) -> dict[str, Any]:
        return {
            "inserted": False,
            "source_id": data.get("url"),
            "note": "persistence handled in orchestration layer",
        }

    @agent.tool_plain
    def link_source_to_topic(source_id: str, topic_id: str) -> dict[str, Any]:
        return {
            "source_id": source_id,
            "topic_id": topic_id,
            "linked": False,
            "note": "persistence handled in orchestration layer",
        }

    return agent


def _build_scoring_agent() -> Agent[None, SourceQualityAssessment] | None:
    if settings.openai_api_key is None:
        return None

    model_name = settings.source_discovery_model
    if not model_name:
        return None

    try:
        from pydantic_ai.models.openai import OpenAIChatModel
    except Exception:
        return None

    try:
        model = OpenAIChatModel(model_name)
    except Exception:
        return None

    return Agent(
        model=model,
        output_type=SourceQualityAssessment,
        name="SourceScoringAgent",
    )


async def check_existing_source(url: str) -> dict[str, Any]:
    normalized = _canonicalize_url(url)
    return {
        "url": normalized,
        "exists": False,
        "source_id": None,
        "note": "check existing source outside agent run context",
    }


async def insert_source(structured_source: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": structured_source.get("url"),
        "inserted": False,
        "note": "insert_source requires persistence in run orchestration",
    }


async def link_source_to_topic(source_id: str, topic_id: str) -> dict[str, Any]:
    return {
        "linked": False,
        "source_id": source_id,
        "topic_id": topic_id,
        "note": "link_source_to_topic requires persistence in run orchestration",
    }


def search_web(query: str) -> list[str]:
    return _search_web(query)


def fetch_page(url: str) -> dict[str, Any]:
    return _fetch_page(url)


def validate_event_page(html: str) -> dict[str, Any]:
    return _validate_event_page(url="", html=html)


def _check_existing_source(
    runtime: _DiscoveryRuntime,
    canonical_url: str,
) -> tuple[bool, str | None]:
    source_id = runtime.existing_source_urls.get(canonical_url)
    if source_id:
        return True, source_id
    created_source_id = runtime.created_source_urls.get(canonical_url)
    if created_source_id:
        return True, created_source_id
    return False, None


async def _link_or_count_existing(
    runtime: _DiscoveryRuntime,
    source_id: str,
    topic_id: str,
    db_session,
) -> bool:
    if (source_id, topic_id) in runtime.source_topic_links:
        return False
    await create_source_topic_link(db_session, source_id, topic_id, _as_sg_now())
    runtime.source_topic_links.add((source_id, topic_id))
    return True


def _run_agent_for_topic(
    agent: Agent[None, list[str]],
    topic: TopicRecord,
    max_results: int,
) -> list[str]:
    prompt = (
        f"Return JSON array of up to {max_results} concrete Singapore event-listing URLs "
        f"for topic '{topic.name}'. Focus on official sources and event pages, not homepages."
    )
    result = agent.run_sync(prompt)
    raw_output = result.output or []
    candidates = []
    if isinstance(raw_output, list):
        for item in raw_output:
            if isinstance(item, str):
                candidates.append(item.strip())
    elif isinstance(raw_output, str):
        candidates = [
            item.strip()
            for item in re.findall(r"https?://[^\"'\\s]+", raw_output)
            if item.strip()
        ]
    elif isinstance(raw_output, dict):
        candidates_from_dict = raw_output.get("candidates")
        if isinstance(candidates_from_dict, list):
            for item in candidates_from_dict:
                if isinstance(item, str):
                    candidates.append(item.strip())
    return candidates[:max_results]


def _resolve_access_method(value: str) -> SourceAccessMethod:
    try:
        return SourceAccessMethod(value)
    except Exception:
        return SourceAccessMethod.html_extract


def _build_fallback_assessment(
    topic: TopicRecord,
    canonical_url: str,
    validation: dict[str, Any],
    page_title: str | None,
    description: str | None,
) -> SourceQualityAssessment:
    confidence = float(validation.get("confidence") or 0.0)
    parsed = urlparse(canonical_url)
    path = parsed.path.lower()
    title = (page_title or "").lower()
    desc = (description or "").lower()

    quality_score = 40
    if "events" in path:
        quality_score += 20
    if "listing" in path or "calendar" in path:
        quality_score += 10
    if "event" in title:
        quality_score += 15
    if "events" in title or "calendar" in title:
        quality_score += 10
    if "singapore" in title or "singapore" in desc:
        quality_score += 10
    if parsed.scheme == "https":
        quality_score += 5
    quality_score = min(100, max(0, quality_score + int(confidence * 20)))

    policy_risk_score = 15 if parsed.scheme == "https" else 35
    if parsed.netloc and (
        "facebook.com" in parsed.netloc.lower()
        or "instagram.com" in parsed.netloc.lower()
        or "x.com" in parsed.netloc.lower()
    ):
        policy_risk_score += 25

    policy_risk_score = min(100, max(0, policy_risk_score))

    source_name = f"{topic.name} - Event Listings"
    if title:
        source_name = title[:120].strip()[:120]

    return SourceQualityAssessment(
        source_name=source_name[:120],
        policy_risk_score=policy_risk_score,
        quality_score=quality_score,
        crawl_frequency_minutes=360,
        assessment_confidence=0.45,
        notes="fallback scoring",
    )


def _assess_source(
    scoring_agent: Agent[None, SourceQualityAssessment] | None,
    topic: TopicRecord,
    query: str,
    canonical_url: str,
    validation: dict[str, Any],
    page_title: str | None,
    description: str | None,
    page_text: str,
) -> SourceQualityAssessment:
    if scoring_agent is None:
        return _build_fallback_assessment(topic, canonical_url, validation, page_title, description)

    prompt = f"""You are scoring one candidate source.
Topic: {topic.name}
Query used: {query}
Canonical URL: {canonical_url}
Validation confidence: {validation.get("confidence", 0.0)}
Validation reason: {validation.get("reason", "")}
Page title: {page_title or ""}
Description: {description or ""}
Page text sample (lowercase): {page_text[:900]}

Return a scoring profile with realistic values:
- source_name: short user-friendly name.
- source_type: one of discovered_event_listings, scrape_listings, api_events.
- access_method: one of api, rss, ics, html_extract, manual.
- policy_risk_score: 0 (low risk) to 100 (high risk).
- quality_score: 0 to 100 based on signal strength.
- crawl_frequency_minutes: practical crawl frequency (>=15).
- assessment_confidence: your confidence 0-1.
- notes: concise one-line rationale.
"""

    try:
        result = scoring_agent.run_sync(prompt)
        if result.output is None:
            raise ValueError("no assessment")
        return result.output
    except Exception:
        return _build_fallback_assessment(topic, canonical_url, validation, page_title, description)


async def _process_topic(
    topic: TopicRecord,
    runtime: _DiscoveryRuntime,
    db_session,
    agent: Agent[None, list[str]] | None,
    scoring_agent: Agent[None, SourceQualityAssessment] | None,
) -> None:
    max_per_topic = runtime.max_new_per_topic
    query = f"{topic.name} Singapore events listings"

    if agent is None:
        candidates = _search_web(query)
        if not candidates:
            candidates = _fallback_candidate_urls(topic)
    else:
        try:
            candidates = _run_agent_for_topic(agent, topic, max_per_topic * 2)
        except Exception:
            candidates = _search_web(query)
            if not candidates:
                candidates = _fallback_candidate_urls(topic)

    discovered_for_topic = 0
    for raw_url in candidates:
        if discovered_for_topic >= max_per_topic:
            break

        canonical_url = _canonicalize_url(raw_url)
        if not canonical_url:
            runtime.skipped_sources += 1
            continue

        parsed = urlparse(canonical_url)
        domain = parsed.netloc.lower()
        if runtime.domain_new_counts.get(domain, 0) >= runtime.max_new_per_domain:
            runtime.skipped_sources += 1
            continue

        if canonical_url in runtime.discovered_urls_in_run:
            exists_in_run, source_id = _check_existing_source(runtime, canonical_url)
            if exists_in_run and source_id is not None:
                if await _link_or_count_existing(runtime, source_id, topic.id, db_session):
                    runtime.topic_links_created += 1
            runtime.skipped_sources += 1
            continue

        exists, source_id = _check_existing_source(runtime, canonical_url)
        if exists and source_id:
            if await _link_or_count_existing(runtime, source_id, topic.id, db_session):
                runtime.topic_links_created += 1
            runtime.discovered_urls_in_run.add(canonical_url)
            runtime.skipped_sources += 1
            continue

        page = _fetch_page(canonical_url)
        if page.get("status_code", 0) < 200 or not page.get("html"):
            runtime.failed_sources += 1
            continue

        validation = _validate_event_page(canonical_url, page["html"])
        if not validation.get("is_relevant", False):
            runtime.failed_sources += 1
            runtime.skipped_sources += 1
            continue

        page_title = validation.get("page_title")
        description = validation.get("description")
        assessment = _assess_source(
            scoring_agent=scoring_agent,
            topic=topic,
            query=query,
            canonical_url=canonical_url,
            validation=validation,
            page_title=page_title,
            description=description,
            page_text=_strip_html(page.get("html", "")),
        )
        source_payload = SourceModel(
            id=uuid4(),
            name=assessment.source_name,
            url=canonical_url,
            source_type=assessment.source_type,
            access_method=_resolve_access_method(assessment.access_method),
            status=SourceStatus.pending,
            policy_risk_score=assessment.policy_risk_score,
            quality_score=assessment.quality_score,
            crawl_frequency_minutes=assessment.crawl_frequency_minutes,
            page_title=page_title,
            discovery_description=description,
            discovery_metadata={
                "topic_ids": [topic.id],
                "discovered_via": "source_discovery_agent",
                "origin_query": query,
                "confidence": validation.get("confidence"),
                "agent_assessment_confidence": assessment.assessment_confidence,
            },
            discovered_at=_as_sg_now(),
            terms_url=None,
            notes=" | ".join(
                item
                for item in [validation.get("reason"), assessment.notes]
                if item
            ),
            deleted_at=None,
            canonical_url=canonical_url,
        )
        try:
            inserted = await create_source(db_session, source_payload)
        except Exception:
            runtime.failed_sources += 1
            continue

        runtime.existing_source_urls[canonical_url] = str(inserted.id)
        runtime.created_source_urls[canonical_url] = str(inserted.id)
        runtime.discovered_urls_in_run.add(canonical_url)
        runtime.discovered_sources += 1
        discovered_for_topic += 1
        runtime.domain_new_counts[domain] = runtime.domain_new_counts.get(domain, 0) + 1
        if await _link_or_count_existing(runtime, str(inserted.id), topic.id, db_session):
            runtime.topic_links_created += 1


async def run_source_discovery(
    db_session,
    *,
    max_new_per_topic: int = TOPIC_MAX_NEW_DEFAULT,
    max_new_per_domain: int = DEFAULT_MAX_NEW_PER_DOMAIN,
) -> SourceDiscoveryRunResponse:
    topic_records = await list_topics(db_session)
    existing_sources = await list_sources(db_session)
    existing_links = await list_source_topic_links(db_session)

    existing_source_urls = {
        _canonicalize_url(str(source.url)): source.id
        for source in existing_sources
        if source.url
    }
    source_topic_links = {(row.source_id, row.topic_id) for row in existing_links}
    runtime = _DiscoveryRuntime(
        run_id=str(uuid4()),
        existing_source_urls={str(k): str(v) for k, v in existing_source_urls.items()},
        source_topic_links=source_topic_links,
        discovered_urls_in_run=set(),
        created_source_urls={},
        domain_new_counts={},
        max_new_per_domain=max_new_per_domain,
        max_new_per_topic=max_new_per_topic,
    )
    topic_agent: Agent[None, list[str]] | None = _build_discovery_agent()
    scoring_agent: Agent[None, SourceQualityAssessment] | None = _build_scoring_agent()

    for topic in topic_records:
        runtime.topics_processed += 1
        await _process_topic(
            topic=topic,
            runtime=runtime,
            db_session=db_session,
            agent=topic_agent,
            scoring_agent=scoring_agent,
        )

    return SourceDiscoveryRunResponse(
        run_id=runtime.run_id,
        topics_processed=runtime.topics_processed,
        discovered_sources=runtime.discovered_sources,
        topic_links_created=runtime.topic_links_created,
        skipped_sources=runtime.skipped_sources,
        failed_sources=runtime.failed_sources,
    )
