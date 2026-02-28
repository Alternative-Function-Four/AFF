from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

import main


@pytest.fixture(autouse=True)
def reset_state() -> None:
    main.reset_store()


def _login(client: TestClient, *, admin: bool = False) -> str:
    payload = {"display_name": "Ops"}
    if admin:
        payload["persona_seed"] = "admin"
    response = client.post("/v1/auth/demo-login", json=payload)
    assert response.status_code == 200
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_ingestion_dedupes_same_source_event() -> None:
    client = TestClient(main.app)
    admin_token = _login(client, admin=True)
    headers = _headers(admin_token)

    created = client.post(
        "/v1/admin/sources",
        headers=headers,
        json={
            "name": "Rare Astronomy Meetup",
            "url": "https://astro.example.sg/events",
            "source_type": "community",
            "access_method": "api",
            "terms_url": "https://astro.example.sg/terms",
        },
    )
    assert created.status_code == 201
    source_id = created.json()["id"]

    approved = client.post(
        f"/v1/admin/sources/{source_id}/approve",
        headers=headers,
        json={
            "decision": "approved",
            "policy_risk_score": 20,
            "quality_score": 75,
            "notes": "approved",
        },
    )
    assert approved.status_code == 200

    first_run = client.post(
        "/v1/admin/ingestion/run",
        headers=headers,
        json={"source_ids": [source_id], "reason": "scheduled_sync"},
    )
    assert first_run.status_code == 202

    second_run = client.post(
        "/v1/admin/ingestion/run",
        headers=headers,
        json={"source_ids": [source_id], "reason": "scheduled_sync"},
    )
    assert second_run.status_code == 202

    titles = [event.title for event in main.store.events.values()]
    assert titles.count("Rare Astronomy Meetup Featured Event") == 1

    event = next(
        item
        for item in main.store.events.values()
        if item.title == "Rare Astronomy Meetup Featured Event"
    )
    assert event.content_hash is not None
    assert event.embedding is not None
    assert event.indoor_outdoor == "indoor"


def test_source_pauses_after_repeated_failures() -> None:
    client = TestClient(main.app)
    admin_token = _login(client, admin=True)
    headers = _headers(admin_token)

    created = client.post(
        "/v1/admin/sources",
        headers=headers,
        json={
            "name": "Manual Failing Source",
            "url": "https://manual-fail.example.sg/events",
            "source_type": "manual",
            "access_method": "manual",
            "terms_url": "https://manual-fail.example.sg/terms",
        },
    )
    assert created.status_code == 201
    source_id = created.json()["id"]

    approved = client.post(
        f"/v1/admin/sources/{source_id}/approve",
        headers=headers,
        json={
            "decision": "approved",
            "policy_risk_score": 20,
            "quality_score": 60,
            "notes": "approved for testing",
        },
    )
    assert approved.status_code == 200

    for _ in range(3):
        response = client.post(
            "/v1/admin/ingestion/run",
            headers=headers,
            json={"source_ids": [source_id], "reason": "scheduled_sync"},
        )
        assert response.status_code == 202

    sources = client.get("/v1/admin/sources", params={"status": "paused"}, headers=headers)
    assert sources.status_code == 200
    paused_ids = {item["id"] for item in sources.json()["items"]}
    assert source_id in paused_ids
