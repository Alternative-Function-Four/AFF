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
- Request schema: none
- Response schema: `{ status: string }`
- Purpose: liveness check
- 200 response example:

```json
{
  "status": "ok"
}
```

## Auth

### `POST /v1/auth/demo-login`

- Auth: none
- Required for prototype
- Request schema: `DemoLoginRequest`
- Response schema: `AuthSessionResponse`
- Request example:

```json
{
  "display_name": "Ari",
  "persona_seed": "night_owl_foodie"
}
```

- 200 response example:

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
- Request schema: `PasswordLoginRequest`
- Response schema: `AuthSessionResponse`
- Request example:

```json
{
  "email": "user@example.com",
  "password": "secret"
}
```

- 200 response mirrors demo-login token response
- 200 response example:

```json
{
  "access_token": "token",
  "token_type": "bearer",
  "expires_at": "2026-02-28T22:00:00+08:00",
  "user": {
    "id": "uuid",
    "display_name": "user"
  }
}
```

## Preferences and Interactions

### `GET /v1/preferences`

- Auth: required
- Request schema: none
- Response schema: `PreferenceProfile`
- 200 response example:

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
- Request schema: `PreferenceProfileInput`
- Response schema: `PreferenceProfile`
- Request body uses same shape as GET response without `user_id` and `updated_at`
- Request example:

```json
{
  "preferred_categories": ["events", "food", "nightlife"],
  "preferred_subcategories": ["indie_music"],
  "budget_mode": "moderate",
  "preferred_distance_km": 8,
  "active_days": "both",
  "preferred_times": ["evening"],
  "anti_preferences": ["large_crowds"]
}
```

- 200 response example:

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

### `POST /v1/interactions`

- Auth: required
- Request schema: `InteractionCreateRequest`
- Response schema: `CreatedResponse`
- Request example:

```json
{
  "event_id": "uuid",
  "signal": "interested",
  "context": {
    "surface": "feed"
  }
}
```

- 201 response example:

```json
{
  "id": "uuid",
  "created_at": "2026-02-28T12:01:00+08:00"
}
```

## Feed and Events

### `GET /v1/feed`

- Auth: required
- Request schema: query params `lat`, `lng`, `time_window`, `budget`, `mode`
- Response schema: `FeedResponse`
- Query params:
  - `lat` number required
  - `lng` number required
  - `time_window` enum: `today|tonight|weekend|next_7_days`
  - `budget` enum: `budget|moderate|premium|any`
  - `mode` enum: `solo|date|group`
- 200 response example:

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
- Request schema: path param `event_id: uuid`
- Response schema: `EventDetail`
- 200 response example:

```json
{
  "event_id": "uuid",
  "title": "Rooftop Jazz Session",
  "category": "concert",
  "subcategory": "indie_music",
  "description": "Sunset live jazz with city skyline.",
  "venue_name": "Esplanade",
  "venue_address": "1 Esplanade Dr",
  "occurrences": [
    {
      "datetime_start": "2026-03-01T20:00:00+08:00",
      "datetime_end": "2026-03-01T22:00:00+08:00",
      "timezone": "Asia/Singapore"
    }
  ],
  "source_provenance": [
    {
      "source_id": "uuid",
      "source_name": "Example Source",
      "source_url": "https://example.com/event"
    }
  ]
}
```

### `POST /v1/events/{event_id}/feedback`

- Auth: required
- Request schema: path param `event_id: uuid` + `EventFeedbackRequest`
- Response schema: `CreatedResponse`
- Request example:

```json
{
  "signal": "not_for_me",
  "context": {
    "surface": "event_detail"
  }
}
```

- 201 response example:

```json
{
  "id": "uuid",
  "created_at": "2026-02-28T12:02:00+08:00"
}
```

## Notifications

### `GET /v1/notifications`

- Auth: required
- Request schema: query param `limit` integer (1..100)
- Response schema: `{ items: NotificationLog[] }`
- Query params: `limit` optional default 20 max 100
- 200 response example:

```json
{
  "items": [
    {
      "id": "uuid",
      "event_id": "uuid",
      "priority": "high",
      "title": "AFF Alert: Rooftop Jazz Session",
      "body": "high_relevance_time_sensitive",
      "status": "queued",
      "sent_at": null,
      "created_at": "2026-02-28T21:00:00+08:00"
    }
  ]
}
```

### `POST /v1/notifications/test`

- Auth: required
- Request schema: `TestNotificationRequest`
- Response schema: `TestNotificationResponse`
- Request example:

```json
{
  "event_id": "uuid",
  "reason": "high_relevance_time_sensitive"
}
```

- 202 response example:

```json
{
  "queued": true,
  "notification_id": "uuid"
}
```

## Admin

### `GET /v1/admin/sources`

- Auth: required admin role
- Request schema: query param `status` optional
- Response schema: `{ items: Source[] }`
- Query params: `status` optional
- 200 response example:

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Example Events",
      "url": "https://example.com/events",
      "source_type": "ticketing_platform",
      "access_method": "rss",
      "status": "approved",
      "policy_risk_score": 28,
      "quality_score": 74,
      "crawl_frequency_minutes": 60,
      "terms_url": "https://example.com/terms",
      "notes": "ICS endpoint stable",
      "deleted_at": null
    }
  ]
}
```

### `POST /v1/admin/sources`

- Auth: required admin role
- Request schema: `SourceCreateRequest`
- Response schema: `Source`
- Request example:

```json
{
  "name": "Example Events",
  "url": "https://example.com/events",
  "source_type": "ticketing_platform",
  "access_method": "rss",
  "terms_url": "https://example.com/terms"
}
```

- 201 response example:

```json
{
  "id": "uuid",
  "name": "Example Events",
  "url": "https://example.com/events",
  "source_type": "ticketing_platform",
  "access_method": "rss",
  "status": "pending",
  "policy_risk_score": 0,
  "quality_score": 0,
  "crawl_frequency_minutes": 60,
  "terms_url": "https://example.com/terms",
  "notes": null,
  "deleted_at": null
}
```

### `POST /v1/admin/sources/{source_id}/approve`

- Auth: required admin role
- Request schema: path param `source_id: uuid` + `SourceApprovalRequest`
- Response schema: `Source`
- Request example:

```json
{
  "decision": "approved",
  "policy_risk_score": 28,
  "quality_score": 74,
  "notes": "ICS endpoint stable"
}
```

- 200 response example:

```json
{
  "id": "uuid",
  "name": "Example Events",
  "url": "https://example.com/events",
  "source_type": "ticketing_platform",
  "access_method": "rss",
  "status": "approved",
  "policy_risk_score": 28,
  "quality_score": 74,
  "crawl_frequency_minutes": 60,
  "terms_url": "https://example.com/terms",
  "notes": "ICS endpoint stable",
  "deleted_at": null
}
```

### `POST /v1/admin/ingestion/run`

- Auth: required admin role
- Request schema: `{ source_ids: uuid[], reason: string }`
- Response schema: `{ job_id: uuid, queued_count: integer }`
- Request example:

```json
{
  "source_ids": ["uuid"],
  "reason": "scheduled_sync"
}
```

- 202 response example:

```json
{
  "job_id": "uuid",
  "queued_count": 1
}
```
