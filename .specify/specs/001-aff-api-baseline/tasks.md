# Implementation Tasks: AFF API Baseline

## Phase 1: Foundation

- [x] 1.1 Create FastAPI app skeleton and contract models
  - Define request/response schemas for all documented v1 endpoints
  - Add request-id middleware and error envelope handlers
  - **Depends on**: None
  - **Requirement**: R1.1

- [x] 1.2 Create in-memory repository and seed canonical events
  - Add users/sessions/preferences/events/sources/notifications stores
  - Seed at least three events with provenance for feed behavior tests
  - **Depends on**: 1.1
  - **Requirement**: R1.2

## Phase 2: Core User APIs

- [x] 2.1 Implement auth and preference endpoints
  - `POST /v1/auth/demo-login`, `POST /v1/auth/login`
  - `GET/PUT /v1/preferences`
  - **Depends on**: 1.2
  - **Requirement**: R2.1, R2.2

- [x] 2.2 Implement feed, events, and interaction endpoints
  - `GET /v1/feed`, `GET /v1/events/{event_id}`
  - `POST /v1/interactions`, `POST /v1/events/{event_id}/feedback`
  - **Depends on**: 2.1
  - **Requirement**: R2.3, R2.4

## Phase 3: Admin and Notification Policies

- [x] 3.1 Implement notification endpoints with policy gates
  - `GET /v1/notifications`, `POST /v1/notifications/test`
  - Enforce daily cap and quiet-hour suppression
  - **Depends on**: 2.2
  - **Requirement**: R3.1

- [x] 3.2 Implement admin source and ingestion endpoints
  - `GET/POST /v1/admin/sources`, `POST /v1/admin/sources/{id}/approve`
  - `POST /v1/admin/ingestion/run` with approved-source gating
  - **Depends on**: 2.2
  - **Requirement**: R3.2

## Phase 4: Verification

- [x] 4.1 Add automated tests for critical acceptance criteria
  - Auth + preference roundtrip
  - Feedback alters ranking for at least one candidate
  - Ingestion rejects non-approved sources
  - Notification cap and quiet-hour suppression
  - **Depends on**: 3.1, 3.2
  - **Requirement**: R4.1

- [x] 4.2 Run lint and test validation
  - Execute `ruff check` and test suite
  - Fix implementation issues discovered by validation
  - **Depends on**: 4.1
  - **Requirement**: R4.2
