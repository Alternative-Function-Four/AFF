# Data Model

## Core In-Memory Entities

### User
- `id: UUID`
- `display_name: str`
- `email: str | None`
- `role: str` (`user|admin`)
- `created_at: datetime`

### Session
- `token: str`
- `user_id: UUID`
- `expires_at: datetime`

### PreferenceProfile
- `user_id: UUID`
- `preferred_categories: list[str]`
- `preferred_subcategories: list[str]`
- `budget_mode: str`
- `preferred_distance_km: float`
- `active_days: str`
- `preferred_times: list[str]`
- `anti_preferences: list[str]`
- `updated_at: datetime`

### Event
- Canonical event fields, occurrences, and source provenance per contract.

### Interaction
- `id`, `user_id`, `event_id`, `signal`, `context`, `created_at`

### Source
- Metadata and policy status (`pending|approved|rejected|paused`) with scores.

### NotificationLog
- Notification message and status (`queued|suppressed|failed|sent`) with timestamps.

## Integrity Rules

- Source URL uniqueness enforced.
- Ingestion run allows only approved sources.
- Every feed item includes provenance entries.
