# User and Admin Flows

All flows are specified for Singapore (`Asia/Singapore`) and map directly to endpoints in `../04-api/API_CONTRACT.md`.

## Flow 1: User Onboarding (Demo Auth + Initial Preferences)

### Trigger

User opens the app first time.

### Preconditions

- User is not authenticated.
- Backend is reachable.

### Steps

1. App calls `POST /v1/auth/demo-login` with `display_name` and optional `persona_seed`.
2. API returns `access_token`, `user`, `expires_at`.
3. App calls `PUT /v1/preferences` with selected categories, budget mode, time preferences, and anti-preferences.
4. API persists preferences and returns canonical `PreferenceProfile`.

### System Writes

- `users`
- `auth_identities` (provider=`demo`)
- `preferences`

### Edge Cases

- If profile write fails, user remains logged in and app retries preference write.
- If token expired, app repeats demo login.

## Flow 2: Personalized Feed Retrieval

### Trigger

User opens feed tab or refreshes.

### Preconditions

- Auth token valid.
- Preferences exist.

### Steps

1. App calls `GET /v1/feed?lat&lng&time_window&budget&mode`.
2. API builds candidate set from canonical events filtered by time, geo, and source quality.
3. Recommendation pipeline reranks by preference profile + interactions.
4. API returns ranked cards with reasons and provenance.

### System Reads

- `preferences`, `interactions`, `events`, `event_occurrences`, `event_source_links`, `recommendations`

### System Writes

- `recommendations` (rank snapshot with score explanation)

### Edge Cases

- If fewer than 20 candidates found, API returns available set and includes `coverage_warning`.

## Flow 3: Feedback Loop (Interested / Not for Me / Already Knew)

### Trigger

User reacts on a feed card or event details page.

### Steps

1. App calls `POST /v1/events/{event_id}/feedback`.
2. API validates event and feedback enum.
3. API writes interaction record.
4. Optional immediate rerank is triggered for next feed fetch.

### System Writes

- `interactions`

### Expected Effect

- `interested` increases similar candidates.
- `not_for_me` down-ranks similar candidates.
- `already_knew` lowers novelty score but not category affinity.

## Flow 4: Notification Lifecycle

### Trigger

New/updated high-relevance event enters eligibility window.

### Steps

1. Notification gate computes eligibility score.
2. If score passes threshold and user has quota left, create notification candidate.
3. Composer generates concise title/body.
4. Notification is logged; delivery can be real push or prototype test endpoint.

### System Writes

- `notification_logs`

### Controls

- Max 2 notifications per user per day.
- Quiet hours default: 22:00-08:00 local.
- Duplicate notification suppression by `(user_id, event_id, notification_type)` window.

## Flow 5: Admin Source Approval and Ingestion Trigger

### Trigger

Operator reviews candidate source.

### Steps

1. Admin calls `POST /v1/admin/sources` to register source metadata.
2. Admin calls `POST /v1/admin/sources/{id}/approve` with policy verdict.
3. Admin calls `POST /v1/admin/ingestion/run` with source ids.
4. Worker performs crawl -> normalize -> dedup -> upsert canonical events.

### System Writes

- `sources`, `source_validations`, `raw_events`, `events`, `event_occurrences`, `event_source_links`

### Rejection Path

- If source policy score is too risky, status remains `rejected` and ingestion trigger rejects source id.
