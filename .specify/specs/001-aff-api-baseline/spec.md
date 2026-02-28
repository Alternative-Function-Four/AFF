# Feature Specification: AFF API Baseline

## Problem Statement

The repository contains detailed AFF API and product specifications but lacks a working API implementation for the documented v1 endpoints.

## User Stories

### Story 1: Demo User Onboarding and Preferences

As a prototype user
I want to log in with demo auth and save preferences
So that I can receive personalized activity recommendations.

**Acceptance Criteria:**
- [ ] `POST /v1/auth/demo-login` returns token and user summary.
- [ ] `PUT /v1/preferences` persists user preferences.
- [ ] `GET /v1/preferences` returns previously saved values.

### Story 2: Personalized Feed and Feedback Loop

As an authenticated user
I want to fetch ranked feed items and send feedback
So that future ranking reflects my preferences and interactions.

**Acceptance Criteria:**
- [ ] `GET /v1/feed` returns ranked items with reasons and source provenance.
- [ ] `POST /v1/events/{event_id}/feedback` records user signal.
- [ ] At least one candidate ranking changes after feedback.

### Story 3: Admin Source Governance and Ingestion Trigger

As an admin operator
I want to create, approve, and run ingestion for sources
So that only policy-compliant sources enter the ingestion pipeline.

**Acceptance Criteria:**
- [ ] `POST /v1/admin/sources` creates source with pending status.
- [ ] `POST /v1/admin/sources/{id}/approve` changes source status.
- [ ] `POST /v1/admin/ingestion/run` rejects non-approved sources.

### Story 4: Notification Logging with Safety Gates

As a user
I want notifications to be useful but not spammy
So that I receive relevant alerts within policy limits.

**Acceptance Criteria:**
- [ ] `POST /v1/notifications/test` creates a notification log entry.
- [ ] Max 2 notifications per user per day is enforced.
- [ ] Quiet-hour suppression (22:00-08:00 Asia/Singapore) is enforced.

## Clarifications

### Q1: Persistence mode for this feature?
**Context**: Fast delivery is needed while DB migrations are not yet available.
**Answer**: Use in-memory persistence for this slice; keep data models structured for later DB replacement.

### Q2: Admin role assignment during prototype auth?
**Context**: Admin endpoints require role checks but there is no real IAM flow yet.
**Answer**: Assign admin role when `persona_seed` equals `admin` or when password-login email has `admin` local part.

## Non-Functional Requirements

- Performance: Feed endpoint should stay under prototype target with in-memory operations.
- Security: Authenticated endpoints require bearer token, admin endpoints require admin role.
- Reliability: Error envelopes must be consistent across failures.
- Localization: Timezone defaults to Asia/Singapore and currency to SGD.

## Success Metrics

- All critical endpoints in `docs/spec/04-api/OPENAPI.yaml` are implemented.
- Core flows pass automated tests.
- Acceptance criteria in this spec are fully covered by implementation tasks.

## Out of Scope

- Production auth and credential storage.
- External ingestion workers and durable queues.
- Persistent database migrations.
