from __future__ import annotations

from dataclasses import fields as dataclass_fields
from pathlib import Path
import re
import statistics
import time

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
import pytest

import main
from models import EventRecord, RawEventRecord, Source


@pytest.fixture(autouse=True)
def reset_state() -> None:
    main.reset_store()


@pytest.fixture
def client() -> TestClient:
    return TestClient(main.app)


def _login(client: TestClient, *, admin: bool = False) -> str:
    payload = {"display_name": "Ari"}
    if admin:
        payload["persona_seed"] = "admin"
    response = client.post("/v1/auth/demo-login", json=payload)
    assert response.status_code == 200
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_no_unresolved_placeholders_in_docs_spec() -> None:
    root = Path(__file__).resolve().parents[3]
    spec_dir = root / "docs" / "spec"
    patterns = ["TBD", "TODO", "FIXME", "???"]

    matches: list[str] = []
    for file_path in spec_dir.rglob("*.md"):
        if file_path.name == "ACCEPTANCE_CRITERIA.md":
            continue
        text = file_path.read_text(encoding="utf-8")
        for token in patterns:
            if token in text:
                matches.append(f"{file_path}:{token}")

    assert not matches


def test_api_contract_endpoints_exist_in_openapi_and_app() -> None:
    root = Path(__file__).resolve().parents[3]
    contract_text = (root / "docs" / "spec" / "04-api" / "API_CONTRACT.md").read_text(encoding="utf-8")
    openapi_lines = (root / "docs" / "spec" / "04-api" / "OPENAPI.yaml").read_text(
        encoding="utf-8"
    ).splitlines()

    expected = {
        (match.group(1), match.group(2))
        for match in re.finditer(r"### `([A-Z]+) ([^`]+)`", contract_text)
    }

    openapi_pairs: set[tuple[str, str]] = set()
    current_path = ""
    for line in openapi_lines:
        path_match = re.match(r"^  (/[^:]+):$", line)
        if path_match:
            current_path = path_match.group(1)
            continue
        method_match = re.match(r"^    (get|post|put|delete|patch):$", line)
        if method_match and current_path:
            openapi_pairs.add((method_match.group(1).upper(), current_path))

    app_pairs: set[tuple[str, str]] = set()
    for route in main.app.routes:
        if not isinstance(route, APIRoute):
            continue
        methods = getattr(route, "methods", set())
        for method in methods:
            if method in {"HEAD", "OPTIONS"}:
                continue
            app_pairs.add((method, route.path))

    assert expected.issubset(openapi_pairs)
    assert expected.issubset(app_pairs)


def _iter_contract_endpoint_sections(
    contract_text: str,
) -> list[tuple[str, str, str]]:
    sections: list[tuple[str, str, str]] = []
    matches = list(re.finditer(r"^### `([A-Z]+) ([^`]+)`$", contract_text, flags=re.MULTILINE))

    for index, match in enumerate(matches):
        section_start = match.end()
        section_end = matches[index + 1].start() if index + 1 < len(matches) else len(contract_text)
        sections.append((match.group(1), match.group(2), contract_text[section_start:section_end]))

    return sections


def test_api_contract_endpoint_sections_define_auth_schema_and_examples() -> None:
    root = Path(__file__).resolve().parents[3]
    contract_text = (root / "docs" / "spec" / "04-api" / "API_CONTRACT.md").read_text(encoding="utf-8")

    missing: list[str] = []
    for method, path, section in _iter_contract_endpoint_sections(contract_text):
        endpoint = f"{method} {path}"
        checks = {
            "auth mode": r"^- Auth:\s*.+$",
            "request schema": r"^- Request schema:\s*.+$",
            "response schema": r"^- Response schema:\s*.+$",
            "example label": r"^- .*example.*$",
            "json example body": r"```json[\s\S]*?```",
        }
        for check_name, pattern in checks.items():
            if not re.search(pattern, section, flags=re.IGNORECASE | re.MULTILINE):
                missing.append(f"{endpoint} missing {check_name}")

    assert not missing, "\n".join(missing)


def test_generated_openapi_schema_is_well_formed() -> None:
    schema = main.app.openapi()
    assert schema["openapi"].startswith("3.")
    assert "paths" in schema

    post_paths = [
        "/v1/auth/demo-login",
        "/v1/preferences",
        "/v1/admin/ingestion/run",
    ]
    for path in post_paths:
        assert path in schema["paths"]
    assert "responses" in schema["paths"]["/v1/auth/demo-login"]["post"]


def test_soft_delete_fields_present_on_mutable_source_event_tables() -> None:
    assert "deleted_at" in Source.model_fields
    assert Source.model_fields["deleted_at"].default is None

    event_fields = {field.name: field for field in dataclass_fields(EventRecord)}
    raw_event_fields = {field.name: field for field in dataclass_fields(RawEventRecord)}

    assert "deleted_at" in event_fields
    assert "deleted_at" in raw_event_fields
    assert event_fields["deleted_at"].default is None
    assert raw_event_fields["deleted_at"].default is None


def test_error_envelope_shape_is_consistent() -> None:
    client = TestClient(main.app)
    user_token = _login(client)
    admin_token = _login(client, admin=True)

    unauthorized = client.get("/v1/preferences")
    not_found = client.post(
        "/v1/events/00000000-0000-0000-0000-000000000000/feedback",
        headers=_headers(user_token),
        json={"signal": "not_for_me", "context": {"surface": "event_detail"}},
    )

    create_source = client.post(
        "/v1/admin/sources",
        headers=_headers(admin_token),
        json={
            "name": "Dup",
            "url": "https://dup.example.sg/feed",
            "source_type": "events",
            "access_method": "rss",
            "terms_url": "https://dup.example.sg/terms",
        },
    )
    assert create_source.status_code == 201
    conflict = client.post(
        "/v1/admin/sources",
        headers=_headers(admin_token),
        json={
            "name": "Dup2",
            "url": "https://dup.example.sg/feed",
            "source_type": "events",
            "access_method": "rss",
            "terms_url": "https://dup.example.sg/terms",
        },
    )

    key_sets = [
        set(unauthorized.json().keys()),
        set(not_found.json().keys()),
        set(conflict.json().keys()),
    ]
    assert unauthorized.status_code == 401
    assert not_found.status_code == 404
    assert conflict.status_code == 409
    assert all(keys == {"code", "message", "details", "request_id"} for keys in key_sets)


def test_lineage_traceable_from_source_to_recommendation(client: TestClient) -> None:
    admin_token = _login(client, admin=True)
    create = client.post(
        "/v1/admin/sources",
        headers=_headers(admin_token),
        json={
            "name": "Lineage Source",
            "url": "https://lineage.example.sg/feed",
            "source_type": "events",
            "access_method": "api",
            "terms_url": "https://lineage.example.sg/terms",
        },
    )
    source_id = create.json()["id"]
    approve = client.post(
        f"/v1/admin/sources/{source_id}/approve",
        headers=_headers(admin_token),
        json={
            "decision": "approved",
            "policy_risk_score": 20,
            "quality_score": 75,
            "notes": "approved",
        },
    )
    assert approve.status_code == 200

    run = client.post(
        "/v1/admin/ingestion/run",
        headers=_headers(admin_token),
        json={"source_ids": [source_id], "reason": "scheduled_sync"},
    )
    assert run.status_code == 202

    user_token = _login(client)
    feed = client.get(
        "/v1/feed",
        headers=_headers(user_token),
        params={
            "lat": 1.29,
            "lng": 103.85,
            "time_window": "next_7_days",
            "budget": "any",
            "mode": "solo",
        },
    )
    assert feed.status_code == 200

    assert main.store.raw_events
    assert main.store.event_source_links
    assert main.store.recommendations

    recommendation_event_ids = {item.event_id for item in main.store.recommendations}
    link_event_ids = {item.event_id for item in main.store.event_source_links}
    assert recommendation_event_ids.intersection(link_event_ids)


def test_feed_p95_latency_under_target(client: TestClient) -> None:
    token = _login(client)
    headers = _headers(token)
    durations_ms: list[float] = []

    for _ in range(120):
        start = time.perf_counter()
        response = client.get(
            "/v1/feed",
            headers=headers,
            params={
                "lat": 1.29,
                "lng": 103.85,
                "time_window": "next_7_days",
                "budget": "moderate",
                "mode": "solo",
            },
        )
        elapsed = (time.perf_counter() - start) * 1000
        assert response.status_code == 200
        durations_ms.append(elapsed)

    p95 = statistics.quantiles(durations_ms, n=100, method="inclusive")[94]
    assert p95 <= 600


def test_ingestion_50_sources_completes_within_target(client: TestClient) -> None:
    admin_token = _login(client, admin=True)
    headers = _headers(admin_token)

    source_ids: list[str] = []
    for index in range(50):
        created = client.post(
            "/v1/admin/sources",
            headers=headers,
            json={
                "name": f"Source {index}",
                "url": f"https://source-{index}.example.sg/feed",
                "source_type": "events",
                "access_method": "rss",
                "terms_url": f"https://source-{index}.example.sg/terms",
            },
        )
        assert created.status_code == 201
        source_id = created.json()["id"]
        source_ids.append(source_id)
        approved = client.post(
            f"/v1/admin/sources/{source_id}/approve",
            headers=headers,
            json={
                "decision": "approved",
                "policy_risk_score": 20,
                "quality_score": 70,
                "notes": "ok",
            },
        )
        assert approved.status_code == 200

    start = time.perf_counter()
    run = client.post(
        "/v1/admin/ingestion/run",
        headers=headers,
        json={"source_ids": source_ids, "reason": "load_test"},
    )
    elapsed_seconds = time.perf_counter() - start

    assert run.status_code == 202
    assert elapsed_seconds <= 15 * 60


def test_password_login_reuses_existing_user_and_session_is_issued(client: TestClient) -> None:
    payload = {"email": "Tester@example.com", "password": "ignored"}

    first = client.post("/v1/auth/login", json=payload)
    assert first.status_code == 200
    first_body = first.json()
    assert first_body["user"]["display_name"] == "tester"
    assert first_body["token_type"] == "bearer"

    second = client.post("/v1/auth/login", json=payload)
    assert second.status_code == 200
    second_body = second.json()

    assert first_body["user"]["id"] == second_body["user"]["id"]
    assert first_body["access_token"] != second_body["access_token"]


def test_interactions_endpoint_persists_signal_for_existing_event(client: TestClient) -> None:
    token = _login(client)
    headers = _headers(token)
    event_id = next(iter(main.store.events.keys()))

    response = client.post(
        "/v1/interactions",
        headers=headers,
        json={
            "event_id": event_id,
            "signal": "opened",
            "context": {"surface": "feed_card"},
        },
    )

    assert response.status_code == 201
    saved = main.store.interactions[-1]
    assert saved.event_id == event_id
    assert saved.signal == "opened"
    assert saved.context == {"surface": "feed_card"}


def test_get_event_returns_details_for_known_id(client: TestClient) -> None:
    token = _login(client)
    event_id = next(iter(main.store.events.keys()))

    response = client.get(f"/v1/events/{event_id}", headers=_headers(token))

    assert response.status_code == 200
    body = response.json()
    assert body["event_id"] == event_id
    assert body["title"]
    assert body["occurrences"]
    assert body["source_provenance"]


def test_get_admin_sources_supports_status_filter(client: TestClient) -> None:
    admin_token = _login(client, admin=True)
    headers = _headers(admin_token)

    created = client.post(
        "/v1/admin/sources",
        headers=headers,
        json={
            "name": "Pending Source",
            "url": "https://pending.example.sg/feed",
            "source_type": "events",
            "access_method": "rss",
            "terms_url": "https://pending.example.sg/terms",
        },
    )
    assert created.status_code == 201

    filtered = client.get("/v1/admin/sources", headers=headers, params={"status": "pending"})
    assert filtered.status_code == 200
    pending_items = filtered.json()["items"]
    assert pending_items
    assert all(item["status"] == "pending" for item in pending_items)


def test_request_id_header_is_set_for_successful_response(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")
