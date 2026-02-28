from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from constants import SG_TZ
from dependencies import APIError, get_admin_user, get_db_session
from event_ingestion import run_event_ingestion
from models import (
    IngestionRunRequest,
    IngestionRunResponse,
    Source,
    SourceApprovalDecision,
    SourceApprovalRequest,
    SourceCreateRequest,
    SourceDiscoveryRunRequest,
    SourceDiscoveryRunResponse,
    SourceListResponse,
    SourceStatus,
    UserRecord,
)
from state import refresh_store_from_db
from storage_service import (
    create_source,
    create_ingestion_job,
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
    for source_id in payload.source_ids:
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

    job_id = uuid4()
    run_id = str(job_id)
    summary = await run_event_ingestion(
        db,
        source_ids=[str(item) for item in payload.source_ids],
        reason=payload.reason,
        run_id=run_id,
        user_id=admin_user.id,
    )

    await create_ingestion_job(
        db,
        job_id=str(job_id),
        source_ids=[str(source_id) for source_id in payload.source_ids],
        reason=payload.reason,
        queued_at=datetime.now(SG_TZ),
        run_id=run_id,
        created_events=summary.created_events,
        merge_actions=summary.merge_actions,
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
