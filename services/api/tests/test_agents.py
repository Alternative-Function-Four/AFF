from datetime import datetime

from fastapi.testclient import TestClient
import pytest

import agent_contracts
import main


def _admin_headers(client: TestClient) -> dict[str, str]:
    login = client.post(
        "/v1/auth/demo-login",
        json={"display_name": "Ops", "persona_seed": "admin"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_normalizer_parses_iso_time_with_ok_envelope() -> None:
    payload = {
        "raw_event": {
            "raw_title": "Rooftop Jazz Session",
            "raw_date_or_schedule": "2026-03-05T20:00:00+08:00",
            "raw_location": "Esplanade",
            "raw_description": "Live jazz.",
            "raw_price": "SGD 20-40",
            "raw_url": "https://example.com/event",
        },
        "city_context": "Singapore",
    }

    result = agent_contracts.normalize_event_agent(payload=payload, run_id="run-test-1")

    assert result["status"] == "ok"
    assert result["meta"]["agent"] == "EventNormalizerAgent"
    event = result["data"]["normalized_event"]
    assert event["datetime_start"].startswith("2026-03-05T20:00:00")
    assert event["confidence_score"] > 0.8


def test_normalizer_missing_fields_returns_low_confidence_not_error() -> None:
    payload = {
        "raw_event": {
            "raw_title": "",
            "raw_date_or_schedule": "",
            "raw_location": "",
            "raw_description": None,
            "raw_price": None,
            "raw_url": None,
        },
        "city_context": "Singapore",
    }

    result = agent_contracts.normalize_event_agent(payload=payload, run_id="run-test-2")

    assert result["status"] == "ok"
    event = result["data"]["normalized_event"]
    assert event["confidence_score"] < 0.6
    assert event["parsing_notes"] is not None


def test_dedup_returns_explicit_action_and_manual_review_rule() -> None:
    payload = {
        "candidate_event": {"title": "Unknown Event", "datetime_start": "2026-03-05T20:00:00+08:00"},
        "similar_events": [
            {
                "event_id": "11111111-1111-1111-1111-111111111111",
                "title": "Distantly Similar",
                "datetime_start": "2026-03-10T20:00:00+08:00",
                "venue_name": "Somewhere",
                "similarity_score": 0.52,
            }
        ],
    }

    result = agent_contracts.deduplicate_event_agent(payload=payload, run_id="run-test-3")

    assert result["status"] == "ok"
    data = result["data"]
    assert data["merge_action"] in {"skip", "merge_sources", "create_new"}
    assert isinstance(data["requires_manual_review"], bool)
    if data["confidence"] < 0.65:
        assert data["requires_manual_review"] is True


def test_agent_error_envelope_shape_on_invalid_input() -> None:
    result = agent_contracts.normalize_event_agent(payload={}, run_id="run-test-4")

    assert result["status"] == "error"
    assert set(result["error"].keys()) == {"code", "message", "retryable", "details"}
    assert set(result["meta"].keys()) == {"agent", "version", "run_id"}


@pytest.fixture(autouse=True)
def reset_state() -> None:
    main.reset_store()


def test_ingestion_run_records_parse_failures_in_metrics_and_logs() -> None:
    client = TestClient(main.app)
    headers = _admin_headers(client)

    create_source = client.post(
        "/v1/admin/sources",
        headers=headers,
        json={
            "name": "Manual Source",
            "url": "https://manual.example.sg/events",
            "source_type": "manual",
            "access_method": "manual",
            "terms_url": "https://manual.example.sg/terms",
        },
    )
    assert create_source.status_code == 201
    source_id = create_source.json()["id"]

    approve_source = client.post(
        f"/v1/admin/sources/{source_id}/approve",
        headers=headers,
        json={
            "decision": "approved",
            "policy_risk_score": 25,
            "quality_score": 72,
            "notes": "Approved for manual ingest",
        },
    )
    assert approve_source.status_code == 200

    run = client.post(
        "/v1/admin/ingestion/run",
        headers=headers,
        json={"source_ids": [source_id], "reason": "scheduled_sync"},
    )
    assert run.status_code == 202

    metrics = main.store.ingestion_metrics
    assert metrics["normalization_low_confidence_total"] >= 1
    assert metrics["source_parse_failures_total"] >= 1

    warning_logs = [
        item
        for item in main.store.ingestion_logs
        if item["level"] == "warning" and item["message"] == "Low confidence normalization"
    ]
    assert warning_logs
    assert warning_logs[0]["source_id"] == source_id

    assert main.store.ingestion_metrics["dedup_merge_action_total"].keys() == {
        "skip",
        "merge_sources",
        "create_new",
    }

    # Timestamp format remains ISO 8601 parseable.
    datetime.fromisoformat(warning_logs[0]["timestamp"])
