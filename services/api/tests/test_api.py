from datetime import datetime
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

API_DIR = Path(__file__).resolve().parents[1]
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

import main  # noqa: E402

SG_TZ = ZoneInfo("Asia/Singapore")


@pytest.fixture(autouse=True)
def reset_state() -> None:
    main.reset_store()


@pytest.fixture
def client() -> TestClient:
    return TestClient(main.app)


def login_demo_user(client: TestClient, persona_seed: str | None = None) -> str:
    payload: dict[str, str] = {"display_name": "Ari"}
    if persona_seed:
        payload["persona_seed"] = persona_seed
    response = client.post("/v1/auth/demo-login", json=payload)
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_preferences_round_trip(client: TestClient) -> None:
    token = login_demo_user(client)

    update_payload = {
        "preferred_categories": ["events", "food"],
        "preferred_subcategories": ["indie_music"],
        "budget_mode": "moderate",
        "preferred_distance_km": 10,
        "active_days": "both",
        "preferred_times": ["evening"],
        "anti_preferences": ["large_crowds"],
    }
    put_response = client.put(
        "/v1/preferences", json=update_payload, headers=auth_headers(token)
    )
    assert put_response.status_code == 200

    get_response = client.get("/v1/preferences", headers=auth_headers(token))
    assert get_response.status_code == 200
    body = get_response.json()

    for key, value in update_payload.items():
        assert body[key] == value
    assert "user_id" in body
    assert "updated_at" in body


def test_feedback_changes_feed_ordering(client: TestClient) -> None:
    token = login_demo_user(client)
    headers = auth_headers(token)
    params = {
        "lat": 1.29,
        "lng": 103.85,
        "time_window": "next_7_days",
        "budget": "any",
        "mode": "solo",
    }

    first_feed = client.get("/v1/feed", params=params, headers=headers)
    assert first_feed.status_code == 200
    first_items = first_feed.json()["items"]
    assert len(first_items) >= 2

    target_event_id = first_items[0]["event_id"]
    first_score = first_items[0]["relevance_score"]

    feedback = {
        "signal": "not_for_me",
        "context": {"surface": "event_detail"},
    }
    feedback_response = client.post(
        f"/v1/events/{target_event_id}/feedback", json=feedback, headers=headers
    )
    assert feedback_response.status_code == 201

    second_feed = client.get("/v1/feed", params=params, headers=headers)
    assert second_feed.status_code == 200
    second_items = second_feed.json()["items"]

    updated_target = next(item for item in second_items if item["event_id"] == target_event_id)
    assert updated_target["relevance_score"] < first_score
    assert second_items[0]["event_id"] != target_event_id


def test_ingestion_rejects_non_approved_sources(client: TestClient) -> None:
    admin_token = login_demo_user(client, persona_seed="admin")
    headers = auth_headers(admin_token)

    create_payload = {
        "name": "Candidate Source",
        "url": "https://candidate.example.sg/feed",
        "source_type": "events",
        "access_method": "rss",
        "terms_url": "https://candidate.example.sg/terms",
    }
    created = client.post("/v1/admin/sources", json=create_payload, headers=headers)
    assert created.status_code == 201
    source_id = created.json()["id"]

    run_payload = {"source_ids": [source_id], "reason": "scheduled_sync"}
    rejected = client.post("/v1/admin/ingestion/run", json=run_payload, headers=headers)
    assert rejected.status_code == 403
    assert rejected.json()["code"] == "SOURCE_NOT_APPROVED"

    approve_payload = {
        "decision": "approved",
        "policy_risk_score": 20,
        "quality_score": 80,
        "notes": "looks good",
    }
    approved = client.post(
        f"/v1/admin/sources/{source_id}/approve", json=approve_payload, headers=headers
    )
    assert approved.status_code == 200

    queued = client.post("/v1/admin/ingestion/run", json=run_payload, headers=headers)
    assert queued.status_code == 202
    assert queued.json()["queued_count"] == 1


def test_notification_limits_and_quiet_hours(client: TestClient) -> None:
    token = login_demo_user(client)
    headers = auth_headers(token)

    main.store.now_provider = lambda: datetime(2026, 2, 28, 14, 0, tzinfo=SG_TZ)
    event_id = next(iter(main.store.events.keys()))

    request_payload = {
        "event_id": event_id,
        "reason": "high_relevance_time_sensitive",
    }
    first = client.post("/v1/notifications/test", json=request_payload, headers=headers)
    second = client.post("/v1/notifications/test", json=request_payload, headers=headers)
    third = client.post("/v1/notifications/test", json=request_payload, headers=headers)

    assert first.status_code == 202
    assert second.status_code == 202
    assert third.status_code == 202
    assert first.json()["queued"] is True
    assert second.json()["queued"] is True
    assert third.json()["queued"] is False

    main.store.now_provider = lambda: datetime(2026, 3, 1, 23, 0, tzinfo=SG_TZ)
    quiet_token = login_demo_user(client)
    quiet_headers = auth_headers(quiet_token)
    quiet = client.post("/v1/notifications/test", json=request_payload, headers=quiet_headers)
    assert quiet.status_code == 202
    assert quiet.json()["queued"] is False

    logs = client.get("/v1/notifications", headers=quiet_headers)
    assert logs.status_code == 200
    statuses = [item["status"] for item in logs.json()["items"]]
    assert "suppressed" in statuses
