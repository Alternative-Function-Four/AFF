# API Contract

Version: `v1`

Base URL example: `https://api.aff.local`

## 1. Common Rules

- Content type: `application/json`
- Auth type: Bearer token except explicitly public endpoints
- Timezone: `Asia/Singapore`
- Currency default: `SGD`
- Error envelope is standardized (see below)

## 2. Error Envelope

```json
{
  "code": "INVALID_REQUEST",
  "message": "Validation failed",
  "details": {
    "field": "budget"
  },
  "request_id": "req_01J..."
}
```

Common status codes:

- `400` invalid request
- `401` unauthorized
- `403` forbidden
- `404` not found
- `409` conflict
- `422` semantic validation error
- `429` rate limited
- `500` internal error

## 3. Endpoint Catalog

## Health

### `GET /health`

- Auth: none
- Purpose: liveness check
- 200 response: `{ "status": "ok" }`

## Auth

### `POST /v1/auth/demo-login`

- Auth: none
- Required for prototype
- Request:

```json
{
  "display_name": "Ari",
  "persona_seed": "night_owl_foodie"
}
```

- 200 response:

```json
{
  "access_token": "token",
  "token_type": "bearer",
  "expires_at": "2026-02-28T22:00:00+08:00",
  "user": {
    "id": "uuid",
    "display_name": "Ari"
  }
}
```

### `POST /v1/auth/login`

- Auth: none
- Prototype mode: documented optional endpoint
- Request:

```json
{
  "email": "user@example.com",
  "password": "secret"
}
```

- 200 response mirrors demo-login token response

## Preferences and Interactions

### `GET /v1/preferences`

- Auth: required
- 200 response:

```json
{
  "user_id": "uuid",
  "preferred_categories": ["events", "food", "nightlife"],
  "preferred_subcategories": ["indie_music"],
  "budget_mode": "moderate",
  "preferred_distance_km": 8,
  "active_days": "both",
  "preferred_times": ["evening"],
  "anti_preferences": ["large_crowds"],
  "updated_at": "2026-02-28T12:00:00+08:00"
}
```

### `PUT /v1/preferences`

- Auth: required
- Request body uses same shape as GET response without `user_id` and `updated_at`
- 200 response returns persisted profile

### `POST /v1/interactions`

- Auth: required
- Request:

```json
{
  "event_id": "uuid",
  "signal": "interested",
  "context": {
    "surface": "feed"
  }
}
```

- 201 response:

```json
{
  "id": "uuid",
  "created_at": "2026-02-28T12:01:00+08:00"
}
```

## Feed and Events

### `GET /v1/feed`

- Auth: required
- Query params:
  - `lat` number required
  - `lng` number required
  - `time_window` enum: `today|tonight|weekend|next_7_days`
  - `budget` enum: `budget|moderate|premium|any`
  - `mode` enum: `solo|date|group`
- 200 response:

```json
{
  "items": [
    {
      "event_id": "uuid",
      "title": "Rooftop Jazz Session",
      "datetime_start": "2026-03-01T20:00:00+08:00",
      "venue_name": "Esplanade",
      "category": "concert",
      "price": {
        "min": 20,
        "max": 40,
        "currency": "SGD"
      },
      "relevance_score": 0.93,
      "reasons": ["Matches indie and evening preference"],
      "source_provenance": [
        {
          "source_id": "uuid",
          "source_name": "Example Source",
          "source_url": "https://example.com/event"
        }
      ]
    }
  ],
  "coverage_warning": null,
  "request_id": "req_01J..."
}
```

### `GET /v1/events/{event_id}`

- Auth: required
- 200 response contains full canonical event + occurrences + provenance links.

### `POST /v1/events/{event_id}/feedback`

- Auth: required
- Request:

```json
{
  "signal": "not_for_me",
  "context": {
    "surface": "event_detail"
  }
}
```

- 201 response: interaction id + created timestamp

## Notifications

### `GET /v1/notifications`

- Auth: required
- Query params: `limit` optional default 20 max 100
- 200 response returns chronologically descending notification logs

### `POST /v1/notifications/test`

- Auth: required
- Request:

```json
{
  "event_id": "uuid",
  "reason": "high_relevance_time_sensitive"
}
```

- 202 response:

```json
{
  "queued": true,
  "notification_id": "uuid"
}
```

## Admin

### `GET /v1/admin/sources`

- Auth: required admin role
- Query params: `status` optional
- 200 response returns list of source records with policy metadata

### `POST /v1/admin/sources`

- Auth: required admin role
- Request includes source metadata and policy fields
- 201 response returns created source

### `POST /v1/admin/sources/{source_id}/approve`

- Auth: required admin role
- Request:

```json
{
  "decision": "approved",
  "policy_risk_score": 28,
  "quality_score": 74,
  "notes": "ICS endpoint stable"
}
```

- 200 response returns updated source status

### `POST /v1/admin/ingestion/run`

- Auth: required admin role
- Request:

```json
{
  "source_ids": ["uuid"],
  "reason": "scheduled_sync"
}
```

- 202 response:

```json
{
  "job_id": "uuid",
  "queued_count": 1
}
```
