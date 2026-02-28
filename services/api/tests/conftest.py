# ruff: noqa: E402
from pathlib import Path
import sys
from datetime import datetime, timedelta, timezone

API_DIR = Path(__file__).resolve().parents[1]
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

import pytest

import event_ingestion
import event_ingestion_impl


@pytest.fixture(autouse=True)
def stub_ingestion_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_crawl_source_pages(
        runtime: event_ingestion.CrawlRuntime,  # pragma: no cover - type contract only
        source,
    ) -> list[event_ingestion.CrawledPage]:
        del runtime
        if str(source.access_method) == "manual":
            return []
        return [event_ingestion.CrawledPage(url=str(source.url), content=f"{source.name} Singapore events")]

    async def fake_extract_events(
        agent: object,  # pragma: no cover - test stub
        source,
        pages: list[event_ingestion.CrawledPage],
    ) -> list[event_ingestion.ExtractedEvent]:
        del agent
        if str(source.access_method) == "manual":
            return []
        if not pages:
            return []
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        start = now + timedelta(days=1)
        end = start + timedelta(hours=2)
        return [
            event_ingestion.ExtractedEvent(
                source_event_id=f"{source.id}-featured",
                title=f"{source.name} Featured Event",
                description=f"Ingested synthetic event from {source.name}",
                category=str(source.source_type),
                start_datetime=start,
                end_datetime=end,
                venue_name="Singapore",
                venue_address="Singapore",
                indoor_outdoor="indoor",
                latitude=1.29027,
                longitude=103.851959,
                price_min=20,
                price_max=40,
                currency="SGD",
                event_url=str(source.url),
                image_url=None,
                status="active",
            )
        ]

    async def fake_embed_text(client: object, text: str) -> list[float]:
        del client
        del text
        dims = max(8, event_ingestion_impl.settings.event_embedding_dimensions)
        return [1.0 / dims for _ in range(dims)]

    monkeypatch.setattr(event_ingestion_impl, "_build_extraction_agent", lambda: object())
    monkeypatch.setattr(event_ingestion_impl, "_build_embedding_client", lambda: object())
    monkeypatch.setattr(event_ingestion_impl, "_crawl_source_pages", fake_crawl_source_pages)
    monkeypatch.setattr(event_ingestion_impl, "_extract_events_with_llm", fake_extract_events)
    monkeypatch.setattr(event_ingestion_impl, "_embed_text", fake_embed_text)
