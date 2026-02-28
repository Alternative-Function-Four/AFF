from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from agent_contracts import deduplicate_event_agent, normalize_event_agent
from dependencies import APIError, get_admin_user, get_db_session
from core import now_sg
from logic import build_similar_events
from models import (
    EventOccurrence,
    EventRecord,
    EventSourceLinkRecord,
    IngestionRunRequest,
    IngestionRunResponse,
    Price,
    RawEventRecord,
    Source,
    SourceAccessMethod,
    SourceApprovalDecision,
    SourceApprovalRequest,
    SourceCreateRequest,
    SourceDiscoveryRunRequest,
    SourceDiscoveryRunResponse,
    SourceListResponse,
    SourceProvenance,
    SourceStatus,
    UserRecord,
)
from state import STORE, refresh_store_from_db
from storage_service import (
    append_ingestion_log,
    create_source,
    create_event,
    create_event_source_link,
    create_ingestion_job,
    create_raw_event,
    increment_metric,
    list_sources,
    get_source,
    save_source,
    source_exists_with_url,
)
from source_discovery import run_source_discovery

router = APIRouter()


@router.get("/v1/admin/sources", response_model=SourceListResponse)
async def get_admin_sources(
    status_filter: SourceStatus | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db_session),
    admin_user: UserRecord = Depends(get_admin_user),
) -> SourceListResponse:
    del admin_user
    await refresh_store_from_db(db)
    items = await list_sources(db, status_filter=status_filter)
    return SourceListResponse(items=items)


@router.post(
    "/v1/admin/sources",
    response_model=Source,
    status_code=status.HTTP_201_CREATED,
)
async def post_admin_source(
    payload: SourceCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    admin_user: UserRecord = Depends(get_admin_user),
) -> Source:
    del admin_user
    normalized_url = str(payload.url)
    if await source_exists_with_url(db, normalized_url):
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
    created = await create_source(db, source)
    await refresh_store_from_db(db)
    return created


@router.post("/v1/admin/sources/{source_id}/approve", response_model=Source)
async def post_admin_source_approve(
    source_id: UUID,
    payload: SourceApprovalRequest,
    db: AsyncSession = Depends(get_db_session),
    admin_user: UserRecord = Depends(get_admin_user),
) -> Source:
    del admin_user
    source = await get_source(db, str(source_id))
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
    saved = await save_source(db, updated)
    await refresh_store_from_db(db)
    return saved


@router.post(
    "/v1/admin/ingestion/run",
    response_model=IngestionRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def post_admin_ingestion_run(
    payload: IngestionRunRequest,
    db: AsyncSession = Depends(get_db_session),
    admin_user: UserRecord = Depends(get_admin_user),
) -> IngestionRunResponse:
    await refresh_store_from_db(db)

    approved_sources: list[Source] = []
    for source_id in payload.source_ids:
        source = STORE.sources.get(str(source_id))
        if source is None:
            source = await get_source(db, str(source_id))
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
        await create_raw_event(
            db,
            RawEventRecord(
                id=raw_event_id,
                source_id=str(source.id),
                external_event_id=None,
                payload_ref=f"ingestion://{run_id}/{raw_event_id}",
                raw_title=raw_event["raw_title"],
                raw_date_or_schedule=raw_event["raw_date_or_schedule"],
                raw_location=raw_event["raw_location"],
                raw_description=raw_event["raw_description"],
                raw_price=raw_event["raw_price"],
                raw_url=raw_event["raw_url"],
                raw_media_url=None,
                captured_at=captured_at,
            ),
        )

        normalized = normalize_event_agent(
            payload={"raw_event": raw_event, "city_context": "Singapore"},
            run_id=run_id,
        )
        if normalized["status"] == "error":
            await increment_metric(db, "source_parse_failures_total")
            await append_ingestion_log(
                db,
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
            await increment_metric(db, "normalization_low_confidence_total")
            await increment_metric(db, "source_parse_failures_total")
            await append_ingestion_log(
                db,
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
                "similar_events": build_similar_events(STORE, normalized_event),
            },
            run_id=run_id,
        )
        if dedup["status"] == "error":
            await increment_metric(db, "source_parse_failures_total")
            await append_ingestion_log(
                db,
                run_id=run_id,
                level="error",
                message="Deduplication failed",
                user_id=admin_user.id,
                source_id=str(source.id),
                payload=dedup["error"],
            )
            continue
        else:
            decision = dedup["data"]
            action = decision["merge_action"]
            merge_actions.append(action)
            await increment_metric(db, "dedup_merge_action_total", action=action)
            await append_ingestion_log(
                db,
                run_id=run_id,
                level="info",
                message="Deduplication decision computed",
                user_id=admin_user.id,
                source_id=str(source.id),
                payload=decision,
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
                await create_event(db, new_event)
                await create_event_source_link(
                    db,
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
                    ),
                )
                created_events += 1
                await append_ingestion_log(
                    db,
                    run_id=run_id,
                    level="info",
                    message="Created canonical event from ingestion",
                    user_id=admin_user.id,
                    source_id=str(source.id),
                    event_id=event_id,
                    payload={"title": new_event.title},
                )
            elif decision.get("duplicate_of_id"):
                await append_ingestion_log(
                    db,
                    run_id=run_id,
                    level="info",
                    message="Deduplicated into existing event",
                    user_id=admin_user.id,
                    source_id=str(source.id),
                    event_id=str(decision["duplicate_of_id"]),
                    payload={"target_event_id": decision["duplicate_of_id"]},
                )

                await create_event_source_link(
                    db,
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
                    ),
                )

    await create_ingestion_job(
        db,
        job_id=str(job_id),
        source_ids=[str(source_id) for source_id in payload.source_ids],
        reason=payload.reason,
        queued_at=now_sg(STORE),
        run_id=run_id,
        created_events=created_events,
        merge_actions=merge_actions,
    )
    await refresh_store_from_db(db)

    return IngestionRunResponse(job_id=job_id, queued_count=len(payload.source_ids))


@router.post(
    "/v1/admin/source-discovery/run",
    response_model=SourceDiscoveryRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def post_admin_source_discovery_run(
    payload: SourceDiscoveryRunRequest,
    db: AsyncSession = Depends(get_db_session),
    admin_user: UserRecord = Depends(get_admin_user),
) -> SourceDiscoveryRunResponse:
    del admin_user
    await refresh_store_from_db(db)
    result = await run_source_discovery(
        db,
        max_new_per_topic=payload.max_new_per_topic,
    )
    await refresh_store_from_db(db)
    return result
