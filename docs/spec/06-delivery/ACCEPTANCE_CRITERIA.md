# Acceptance Criteria

All items are pass/fail for prototype sign-off.

## 1. Contract Completeness

- [ ] No unresolved placeholders (`TBD`, `TODO`, `FIXME`, `???`) in `docs/spec`.
- [ ] Every endpoint listed in `API_CONTRACT.md` exists in `OPENAPI.yaml`.
- [ ] Every endpoint defines auth mode, request schema, response schema, and example.
- [ ] Error envelope shape is consistent across all documented error responses.

## 2. Data and Lineage

- [ ] Canonical event creation always links to at least one raw event source record.
- [ ] Lineage from source to recommendation can be traced using DB records.
- [ ] Source unique URL constraint is enforced.
- [ ] Soft-delete fields are present on mutable source/event tables.

## 3. Functional Behavior

- [ ] `POST /v1/auth/demo-login` returns usable token and user id.
- [ ] `PUT /v1/preferences` persists and `GET /v1/preferences` returns same values.
- [ ] `GET /v1/feed` returns ranked items with reasons and source provenance.
- [ ] `POST /v1/events/{event_id}/feedback` creates interaction.
- [ ] Feedback impacts subsequent feed ordering for at least one candidate.
- [ ] `POST /v1/admin/sources/{id}/approve` changes source status.
- [ ] `POST /v1/admin/ingestion/run` queues or executes ingestion job.
- [ ] `GET /v1/notifications` returns historical notifications.
- [ ] `POST /v1/notifications/test` creates a notification log entry.

## 4. Agent Contract Compliance

- [ ] Source, ingestion, recommendation, and notification agents use strict success/error envelopes.
- [ ] Dedup agent returns explicit action (`skip|merge_sources|create_new`).
- [ ] Normalizer outputs confidence score and parsing notes when ambiguous.

## 5. Reliability and Policy

- [ ] Notification cap of max 2 per user per day is enforced.
- [ ] Quiet-hour suppression is enforced for 22:00-08:00 Singapore time.
- [ ] Non-approved sources cannot be ingested.
- [ ] Failed source parses are visible in logs and metrics.

## 6. Performance Targets

- [ ] Feed endpoint p95 latency <= 600 ms in local/prototype test.
- [ ] Ingestion completion <= 15 minutes for test batch up to 50 sources.

## 7. Verification Scenarios

## Unit

- [ ] Normalization time parsing
- [ ] Dedup decision rules
- [ ] Preference profile aggregation
- [ ] Notification gate throttling

## Contract

- [ ] OpenAPI schema validation
- [ ] Error envelope contract assertion

## Integration

- [ ] Source -> raw -> normalized -> dedup -> canonical -> feed

## End-to-End

- [ ] New user onboarding to personalized feed
- [ ] Positive and negative feedback changes rank
- [ ] High relevance item triggers notification while respecting limits
