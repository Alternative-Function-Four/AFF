from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from constants import QUIET_HOUR_END, QUIET_HOUR_START, SG_TZ
from models import FlexibleObject, InMemoryStore, IngestionLogRecord, IngestionMetrics


def make_request_id() -> str:
    return f"req_{uuid4().hex[:12]}"


def as_sg_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=SG_TZ)
    return value.astimezone(SG_TZ)


def now_sg(store: InMemoryStore) -> datetime:
    return as_sg_datetime(store.now_provider())


def make_ingestion_metrics() -> IngestionMetrics:
    return IngestionMetrics()


def append_ingestion_log(
    store: InMemoryStore,
    *,
    run_id: str,
    level: str,
    message: str,
    payload: FlexibleObject | dict[str, object],
    user_id: str | None = None,
    source_id: str | None = None,
    event_id: str | None = None,
) -> None:
    payload_model = payload if isinstance(payload, FlexibleObject) else FlexibleObject.model_validate(payload)
    store.ingestion_logs.append(
        IngestionLogRecord(
            timestamp=now_sg(store).isoformat(),
            level=level,
            service="ingestion",
            run_id=run_id,
            user_id=user_id,
            source_id=source_id,
            event_id=event_id,
            message=message,
            payload=payload_model,
        )
    )


def is_quiet_hours(moment: datetime) -> bool:
    hour = moment.hour
    return hour >= QUIET_HOUR_START or hour < QUIET_HOUR_END
