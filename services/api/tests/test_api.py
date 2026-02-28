from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

import main

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


def test_cors_preflight_for_demo_login(client: TestClient) -> None:
    response = client.options(
        "/v1/auth/demo-login",
        headers={
            "Origin": "http://localhost:8081",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert "POST" in response.headers["access-control-allow-methods"]


def test_error_envelope_shape_for_unauthorized_request(client: TestClient) -> None:
    response = client.get("/v1/preferences")
    assert response.status_code == 401
    body = response.json()
    assert set(body.keys()) == {"code", "message", "details", "request_id"}


def test_preferences_round_trip(client: TestClient) -> None:
    token = login_demo_user(client)

    update_payload = {
        "preferred_categories": ["events", "food"],
        "preferred_subcategories": ["indie_music"],
        "budget_mode": "moderate",
        "preferred_distance_km": 10,
        "home_lat": 1.3022,
        "home_lng": 103.8316,
        "home_address": "Tiong Bahru, Singapore",
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


def test_new_user_onboarding_to_personalized_feed(client: TestClient) -> None:
    token = login_demo_user(client)
    headers = auth_headers(token)
    response = client.put(
        "/v1/preferences",
        headers=headers,
        json={
            "preferred_categories": ["events", "nightlife"],
            "preferred_subcategories": ["indie_music"],
            "budget_mode": "moderate",
            "preferred_distance_km": 8,
            "home_lat": 1.3348,
            "home_lng": 103.9616,
            "home_address": "Bedok, Singapore",
            "active_days": "both",
            "preferred_times": ["evening"],
            "anti_preferences": ["large_crowds"],
        },
    )
    assert response.status_code == 200

    feed = client.get(
        "/v1/feed",
        params={
            "lat": 1.29,
            "lng": 103.85,
            "time_window": "next_7_days",
            "budget": "moderate",
            "mode": "solo",
        },
        headers=headers,
    )
    assert feed.status_code == 200
    assert feed.json()["items"]


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


def test_positive_feedback_increases_candidate_score(client: TestClient) -> None:
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
    target = first_items[-1]

    feedback = {
        "signal": "interested",
        "context": {"surface": "feed"},
    }
    response = client.post(
        f"/v1/events/{target['event_id']}/feedback",
        json=feedback,
        headers=headers,
    )
    assert response.status_code == 201

    second_feed = client.get("/v1/feed", params=params, headers=headers)
    assert second_feed.status_code == 200
    second_items = second_feed.json()["items"]
    updated = next(item for item in second_items if item["event_id"] == target["event_id"])
    assert updated["relevance_score"] > target["relevance_score"]


def test_feed_items_include_reasons_and_provenance(client: TestClient) -> None:
    token = login_demo_user(client)
    response = client.get(
        "/v1/feed",
        params={
            "lat": 1.29,
            "lng": 103.85,
            "time_window": "next_7_days",
            "budget": "moderate",
            "mode": "solo",
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    first = items[0]
    assert first["reasons"]
    assert first["source_provenance"]


def test_ingestion_pipeline_reaches_feed(client: TestClient) -> None:
    admin_token = login_demo_user(client, persona_seed="admin")
    admin_headers = auth_headers(admin_token)
    create = client.post(
        "/v1/admin/sources",
        headers=admin_headers,
        json={
            "name": "Rare Astronomy Meetup",
            "url": "https://astro.example.sg/events",
            "source_type": "community",
            "access_method": "api",
            "terms_url": "https://astro.example.sg/terms",
        },
    )
    assert create.status_code == 201
    source_id = create.json()["id"]

    approve = client.post(
        f"/v1/admin/sources/{source_id}/approve",
        headers=admin_headers,
        json={
            "decision": "approved",
            "policy_risk_score": 22,
            "quality_score": 77,
            "notes": "Approved for ingestion",
        },
    )
    assert approve.status_code == 200

    run = client.post(
        "/v1/admin/ingestion/run",
        headers=admin_headers,
        json={"source_ids": [source_id], "reason": "scheduled_sync"},
    )
    assert run.status_code == 202

    user_token = login_demo_user(client)
    feed = client.get(
        "/v1/feed",
        params={
            "lat": 1.29,
            "lng": 103.85,
            "time_window": "next_7_days",
            "budget": "any",
            "mode": "solo",
        },
        headers=auth_headers(user_token),
    )
    assert feed.status_code == 200
    titles = [item["title"] for item in feed.json()["items"]]
    assert "Rare Astronomy Meetup Featured Event" in titles


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


def test_source_url_unique_constraint_enforced(client: TestClient) -> None:
    admin_token = login_demo_user(client, persona_seed="admin")
    headers = auth_headers(admin_token)
    payload = {
        "name": "Unique Source",
        "url": "https://unique.example.sg/feed",
        "source_type": "events",
        "access_method": "rss",
        "terms_url": "https://unique.example.sg/terms",
    }

    first = client.post("/v1/admin/sources", json=payload, headers=headers)
    second = client.post("/v1/admin/sources", json=payload, headers=headers)
    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["code"] == "SOURCE_URL_CONFLICT"


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
