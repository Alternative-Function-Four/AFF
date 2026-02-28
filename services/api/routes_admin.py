from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, status

from agent_contracts import deduplicate_event_agent, normalize_event_agent
from core import append_ingestion_log, now_sg
from dependencies import APIError, get_admin_user
from logic import build_similar_events
from models import (
    CandidateEventForDedup,
    EventOccurrence,
    EventRecord,
    EventSourceLinkRecord,
    FlexibleObject,
    IngestionJobRecord,
    IngestionRunRequest,
    IngestionRunResponse,
    Price,
    RawEventRecord,
    Source,
    SourceAccessMethod,
    SourceApprovalDecision,
    SourceApprovalRequest,
    SourceCreateRequest,
    SourceListResponse,
    SourceProvenance,
    SourceStatus,
    UserRecord,
)
from state import STORE

router = APIRouter()


@router.get("/v1/admin/sources", response_model=SourceListResponse)
def get_admin_sources(
    status_filter: SourceStatus | None = Query(default=None, alias="status"),
    admin_user: UserRecord = Depends(get_admin_user),
) -> SourceListResponse:
    del admin_user
    items = list(STORE.sources.values())
    if status_filter:
        items = [source for source in items if source.status == status_filter]
    return SourceListResponse(items=items)


@router.post(
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
    for source in STORE.sources.values():
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
    STORE.sources[str(source.id)] = source
    return source


@router.post("/v1/admin/sources/{source_id}/approve", response_model=Source)
def post_admin_source_approve(
    source_id: UUID,
    payload: SourceApprovalRequest,
    admin_user: UserRecord = Depends(get_admin_user),
) -> Source:
    del admin_user
    source = STORE.sources.get(str(source_id))
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
    STORE.sources[str(source_id)] = updated
    return updated


@router.post(
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
        source = STORE.sources.get(str(source_id))
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
        captured_at = now_sg(STORE)
        raw_event = {
            "raw_title": f"{source.name} Featured Event",
            "raw_date_or_schedule": captured_at.replace(
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

        raw_event_id = str(uuid4())
        STORE.raw_events[raw_event_id] = RawEventRecord(
            id=raw_event_id,
            source_id=str(source.id),
            external_event_id=None,
            payload_ref=f"ingestion://{run_id}/{raw_event_id}",
            raw_title=raw_event.get("raw_title"),
            raw_date_or_schedule=raw_event.get("raw_date_or_schedule"),
            raw_location=raw_event.get("raw_location"),
            raw_description=raw_event.get("raw_description"),
            raw_price=raw_event.get("raw_price"),
            raw_url=raw_event.get("raw_url"),
            raw_media_url=None,
            captured_at=captured_at,
        )

        normalized = normalize_event_agent(
            payload={"raw_event": raw_event, "city_context": "Singapore"},
            run_id=run_id,
        )
        if normalized.status == "error":
            STORE.ingestion_metrics.source_parse_failures_total += 1
            append_ingestion_log(
                STORE,
                run_id=run_id,
                level="error",
                message="Normalizer failed",
                user_id=admin_user.id,
                source_id=str(source.id),
                payload=FlexibleObject.model_validate(normalized.error.model_dump(mode="python")),
            )
            continue

        normalized_event = normalized.data.model_dump(mode="python")["normalized_event"]
        confidence_score = float(normalized_event["confidence_score"])
        if confidence_score < 0.6:
            STORE.ingestion_metrics.normalization_low_confidence_total += 1
            STORE.ingestion_metrics.source_parse_failures_total += 1
            append_ingestion_log(
                STORE,
                run_id=run_id,
                level="warning",
                message="Low confidence normalization",
                user_id=admin_user.id,
                source_id=str(source.id),
                payload=FlexibleObject.model_validate(
                    {
                        "confidence_score": confidence_score,
                        "parsing_notes": normalized_event.get("parsing_notes"),
                    }
                ),
            )
            continue

        dedup = deduplicate_event_agent(
            payload={
                "candidate_event": CandidateEventForDedup.model_validate(normalized_event),
                "similar_events": build_similar_events(
                    STORE,
                    CandidateEventForDedup.model_validate(normalized_event),
                ),
            },
            run_id=run_id,
        )
        if dedup.status == "error":
            STORE.ingestion_metrics.source_parse_failures_total += 1
            append_ingestion_log(
                STORE,
                run_id=run_id,
                level="error",
                message="Deduplication failed",
                user_id=admin_user.id,
                source_id=str(source.id),
                payload=FlexibleObject.model_validate(dedup.error.model_dump(mode="python")),
            )
            continue

        decision = dedup.data.model_dump(mode="json")
        action = str(decision["merge_action"])
        merge_actions.append(action)
        if action == "skip":
            STORE.ingestion_metrics.dedup_merge_action_total.skip += 1
        elif action == "merge_sources":
            STORE.ingestion_metrics.dedup_merge_action_total.merge_sources += 1
        else:
            STORE.ingestion_metrics.dedup_merge_action_total.create_new += 1
        append_ingestion_log(
            STORE,
            run_id=run_id,
            level="info",
            message="Deduplication decision computed",
            user_id=admin_user.id,
            source_id=str(source.id),
            payload=FlexibleObject.model_validate(decision),
        )

        if action == "create_new":
            event_id = str(uuid4())
            start = datetime.fromisoformat(normalized_event["datetime_start"])
            end_value = normalized_event.get("datetime_end")
            end = datetime.fromisoformat(end_value) if end_value else None
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
            STORE.events[event_id] = new_event
            STORE.event_source_links.append(
                EventSourceLinkRecord(
                    id=str(uuid4()),
                    event_id=event_id,
                    raw_event_id=raw_event_id,
                    source_id=str(source.id),
                    source_url=str(source.url),
                    external_event_id=None,
                    merge_confidence=float(decision["confidence"]),
                    first_seen_at=captured_at,
                    last_seen_at=captured_at,
                )
            )
            created_events += 1
            append_ingestion_log(
                STORE,
                run_id=run_id,
                level="info",
                message="Created canonical event from ingestion",
                user_id=admin_user.id,
                source_id=str(source.id),
                event_id=event_id,
                payload=FlexibleObject.model_validate({"title": new_event.title}),
            )
        elif decision.get("duplicate_of_id"):
            STORE.event_source_links.append(
                EventSourceLinkRecord(
                    id=str(uuid4()),
                    event_id=str(decision["duplicate_of_id"]),
                    raw_event_id=raw_event_id,
                    source_id=str(source.id),
                    source_url=str(source.url),
                    external_event_id=None,
                    merge_confidence=float(decision["confidence"]),
                    first_seen_at=captured_at,
                    last_seen_at=captured_at,
                )
            )

    STORE.ingestion_jobs.append(
        IngestionJobRecord(
            job_id=str(job_id),
            source_ids=[str(source_id) for source_id in payload.source_ids],
            reason=payload.reason,
            queued_at=now_sg(STORE).isoformat(),
            run_id=run_id,
            created_events=created_events,
            merge_actions=merge_actions,
        )
    )
    return IngestionRunResponse(job_id=job_id, queued_count=len(payload.source_ids))
