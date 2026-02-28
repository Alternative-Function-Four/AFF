from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from constants import SG_TZ
from logic import make_ingestion_metrics, now_sg
from models import InMemoryStore


def create_seed_store() -> InMemoryStore:
    store = InMemoryStore()
    store.ingestion_metrics = make_ingestion_metrics()
    store.now_provider = lambda: datetime.now(SG_TZ)
    return store


STORE = create_seed_store()


def _apply_snapshot(snapshot: dict[str, Any]) -> InMemoryStore:
    now_provider = STORE.now_provider
    STORE.users = snapshot.get("users", {})
    STORE.users_by_email = snapshot.get("users_by_email", {})
    STORE.sessions = snapshot.get("sessions", {})
    STORE.preferences = snapshot.get("preferences", {})
    STORE.events = snapshot.get("events", {})
    STORE.interactions = snapshot.get("interactions", [])
    STORE.sources = snapshot.get("sources", {})
    STORE.raw_events = snapshot.get("raw_events", {})
    STORE.event_source_links = snapshot.get("event_source_links", [])
    STORE.recommendations = snapshot.get("recommendations", [])
    STORE.notification_logs = snapshot.get("notification_logs", [])
    STORE.ingestion_jobs = snapshot.get("ingestion_jobs", [])
    STORE.ingestion_metrics = snapshot.get("ingestion_metrics", make_ingestion_metrics())
    STORE.ingestion_logs = snapshot.get("ingestion_logs", [])
    STORE.now_provider = now_provider
    return STORE


async def refresh_store_from_db(session) -> InMemoryStore:
    from storage_service import get_store_snapshot

    snapshot = await get_store_snapshot(session)
    return _apply_snapshot(snapshot)


def reset_store() -> None:
    from storage_service import reset_store_snapshot

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        snapshot = asyncio.run(reset_store_snapshot())
    else:
        # Safety fallback if called in a sync test while a loop is active.
        loop = asyncio.new_event_loop()
        try:
            snapshot = loop.run_until_complete(reset_store_snapshot())
        finally:
            loop.close()
    _apply_snapshot(snapshot)


def load_store_snapshot(snapshot: dict[str, Any]) -> InMemoryStore:
    return _apply_snapshot(snapshot)


def snapshot_now() -> datetime:
    return now_sg(STORE)
