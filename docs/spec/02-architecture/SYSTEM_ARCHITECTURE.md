# System Architecture

## 1. Architecture Style

- Primary backend: modular monolith in FastAPI (`services/api`).
- Async processing: separate ingestion worker (`services/ingestion`) consuming queued jobs.
- Datastore: PostgreSQL (+ pgvector), with S3 for raw payload retention.
- Cache: Redis for short-lived feed and source health cache.

This keeps deployment simple for hackathon speed while preserving module boundaries for later extraction.

## 2. Runtime Components

- Mobile app (Expo/React Native): onboarding, feed, event details, notification center.
- Lightweight admin surface: source registration/approval and ingestion run triggers.
- API module groups:
  - `auth`
  - `preferences`
  - `events`
  - `feed`
  - `notifications`
  - `admin`
  - `shared` (error envelope, auth middleware, pagination, request ids)
- Worker pipeline stages:
  - source fetch
  - extraction
  - normalization
  - deduplication
  - canonical upsert
  - embedding refresh

## 3. Dependency Graph

```text
Mobile + Admin
  -> FastAPI Monolith
       -> Postgres (canonical + vectors)
       -> Redis (cache)
       -> Queue (ingestion jobs)
       -> Notification adapter

Queue
  -> Ingestion Worker
       -> Source adapters (API/RSS/ICS/allowlisted HTML)
       -> Postgres
       -> S3 raw payload store
```

## 4. Module Boundaries

### API Modules

- `auth`: token issuance and validation for demo auth, login doc endpoints, OAuth stubs.
- `preferences`: CRUD for preference profile.
- `events`: read event details and capture feedback.
- `feed`: context-aware recommendation retrieval.
- `notifications`: list and test-send notification intents.
- `admin`: source lifecycle and ingestion triggers.

No module may read another module's private table directly; cross-module access must use shared repository interfaces.

### Worker Boundaries

- Worker cannot call internal API endpoints for core ingestion writes.
- Worker writes directly through ingestion repositories with idempotent upsert semantics.
- Worker emits status events and metrics only; no user-facing notification side effects.

## 5. Data Flow

1. Source approved by admin.
2. Ingestion run queued.
3. Worker fetches source payload and stores raw snapshot metadata.
4. Extractor outputs `RawEvent` records.
5. Normalizer maps into candidate canonical fields.
6. Dedup logic selects `create_new`, `merge_sources`, or `skip`.
7. Canonical event tables are updated.
8. Feed endpoint reads canonical data and reranks by user profile and interactions.
9. Notification gate evaluates event-user matches and writes logs.

## 6. Hackathon Deployment Shape

- Single API container.
- Single worker container.
- One Postgres instance.
- One Redis instance.
- Optional local queue emulation acceptable for prototype.

## 7. Scaling Path (Post-Hackathon)

- Extract worker into independently autoscaled service first.
- Split `feed` and `notifications` as separate services only after sustained load requires it.
- Preserve shared schema and event contracts before service extraction.

## 8. Non-Functional Targets

- Feed API p95 <= 600 ms for a 20-card response.
- Ingestion run completion <= 15 minutes for up to 50 sources.
- API availability during demo >= 99 percent.
- Notification duplicate rate <= 1 percent in test runs.
