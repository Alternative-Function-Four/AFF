# Agent Contracts

This document defines strict IO contracts and failure behavior for every agent in the prototype pipeline.

## 1. Global Contract Rules

- All agents return JSON only.
- Responses must include `status` with values `ok` or `error`.
- Agents never fabricate missing source facts.
- All timestamps must be ISO 8601.
- Currency defaults to SGD only when explicitly present or inferable from source metadata.

### Success Envelope

```json
{
  "status": "ok",
  "data": {"...": "agent-specific payload"},
  "meta": {
    "agent": "AgentName",
    "version": "v1",
    "run_id": "uuid"
  }
}
```

### Error Envelope

```json
{
  "status": "error",
  "error": {
    "code": "AGENT_ERROR_CODE",
    "message": "human-readable",
    "retryable": true,
    "details": {}
  },
  "meta": {
    "agent": "AgentName",
    "version": "v1",
    "run_id": "uuid"
  }
}
```

## 2. SourceHunterAgent

### Input

```json
{
  "city": "Singapore",
  "categories": ["events", "food", "nightlife"],
  "seed_sources": ["string"]
}
```

### Output `data`

```json
{
  "sources": [
    {
      "name": "string",
      "url": "https://example.com",
      "source_type": "venue_schedule|promotion_agency|ticketing_platform|local_blog|social_media_page|food_guide",
      "access_method": "api|rss|ics|html_extract|manual",
      "update_frequency_estimate": "daily|weekly|irregular",
      "reliability_score": 1,
      "policy_risk_score": 0
    }
  ]
}
```

### Failure Behavior

- If no sources found, return `status=ok` with empty `sources` and warning in `meta`.
- Return `status=error` only for invalid input schema or execution failure.

## 3. SourceValidatorAgent

### Input

```json
{
  "source": {
    "source_id": "uuid",
    "url": "https://example.com",
    "access_method": "api|rss|ics|html_extract|manual"
  }
}
```

### Output `data`

```json
{
  "validation_status": "approved|rejected|needs_manual_review",
  "is_active": true,
  "is_parseable": true,
  "freshness_estimate_hours": 24,
  "extraction_hints": {
    "endpoint": "string|null",
    "selectors": ["string"]
  },
  "policy_flags": ["string"]
}
```

### Failure Behavior

- On network timeout, return retryable error code `SOURCE_VALIDATION_TIMEOUT`.
- On policy violation, return `status=ok` with `validation_status=rejected`.

## 4. CrawlerAgent

### Input

```json
{
  "source": {
    "source_id": "uuid",
    "url": "https://example.com",
    "access_method": "api|rss|ics|html_extract"
  },
  "crawl_window": {
    "from": "2026-03-01T00:00:00+08:00",
    "to": "2026-03-31T23:59:59+08:00"
  }
}
```

### Output `data`

```json
{
  "raw_events": [
    {
      "external_event_id": "string|null",
      "raw_title": "string|null",
      "raw_date_or_schedule": "string|null",
      "raw_location": "string|null",
      "raw_description": "string|null",
      "raw_price": "string|null",
      "raw_url": "string|null",
      "raw_media_url": "string|null",
      "captured_at": "2026-02-28T10:00:00+08:00"
    }
  ],
  "payload_ref": {
    "storage": "s3",
    "path": "s3://bucket/key"
  }
}
```

### Failure Behavior

- Partial extraction allowed; include malformed items in `meta.skipped_count`.
- Hard failure when payload cannot be fetched.

## 5. EventNormalizerAgent

### Input

```json
{
  "raw_event": {
    "raw_title": "string",
    "raw_date_or_schedule": "string",
    "raw_location": "string",
    "raw_description": "string|null",
    "raw_price": "string|null",
    "raw_url": "string|null"
  },
  "city_context": "Singapore"
}
```

### Output `data`

```json
{
  "normalized_event": {
    "title": "string",
    "category": "concert|festival|art_exhibition|theatre|comedy|food_experience|outdoor_activity|sport|workshop|nightlife|film|other",
    "subcategory": "string",
    "datetime_start": "2026-03-05T20:00:00+08:00",
    "datetime_end": "2026-03-05T22:00:00+08:00",
    "is_recurring": false,
    "recurrence_rule": null,
    "venue_name": "string|null",
    "venue_address": "string|null",
    "venue_lat": 1.29,
    "venue_lng": 103.85,
    "price_min": 20,
    "price_max": 60,
    "currency": "SGD",
    "description": "string",
    "tags": ["string"],
    "source_url": "https://example.com/event",
    "confidence_score": 0.9,
    "parsing_notes": "string|null"
  }
}
```

### Failure Behavior

- If required fields are missing, return `status=ok` with confidence < 0.6 and parsing notes.
- Return `status=error` only for invalid input envelope.

## 6. DeduplicationAgent

### Input

```json
{
  "candidate_event": {"...": "normalized event"},
  "similar_events": [
    {
      "event_id": "uuid",
      "title": "string",
      "datetime_start": "2026-03-05T20:00:00+08:00",
      "venue_name": "string",
      "similarity_score": 0.88
    }
  ]
}
```

### Output `data`

```json
{
  "is_duplicate": true,
  "duplicate_of_id": "uuid|null",
  "merge_action": "skip|merge_sources|create_new",
  "confidence": 0.91,
  "reasoning": "string",
  "requires_manual_review": false
}
```

### Failure Behavior

- If confidence < 0.65, must set `requires_manual_review=true`.
- No hard failure for uncertainty.

## 7. PreferenceProfilerAgent

### Input

```json
{
  "explicit_preferences": {
    "categories": ["events", "food", "nightlife"],
    "budget_mode": "budget|moderate|premium|any",
    "time_preferences": ["evening"]
  },
  "interaction_history": [
    {"event_id": "uuid", "signal": "interested|not_for_me|already_knew"}
  ],
  "location": {"lat": 1.29, "lng": 103.85}
}
```

### Output `data`

```json
{
  "profile": {
    "preferred_categories": ["nightlife", "food_experience"],
    "preferred_subcategories": ["indie_music", "hidden_gem_restaurants"],
    "price_sensitivity": "moderate",
    "preferred_distance_km": 8,
    "active_days": "both",
    "preferred_times": ["evening"],
    "taste_descriptors": ["indie not mainstream"],
    "anti_preferences": ["large_crowds"]
  }
}
```

### Failure Behavior

- If interactions are empty, profile is still generated from explicit inputs.

## 8. RecommendationAgent

### Input

```json
{
  "user_id": "uuid",
  "profile": {"...": "preference profile"},
  "context": {
    "lat": 1.29,
    "lng": 103.85,
    "time_window": "tonight",
    "budget": "moderate",
    "mode": "solo"
  },
  "candidate_events": [
    {"event_id": "uuid", "features": {"...": "structured"}}
  ]
}
```

### Output `data`

```json
{
  "ranked": [
    {
      "event_id": "uuid",
      "relevance_score": 0.93,
      "personal_pitch": "string",
      "reasons": ["string"],
      "notify_immediately": true,
      "notify_reason": "string"
    }
  ]
}
```

### Failure Behavior

- If candidate set is empty, return empty `ranked` list.
- If profile missing, return retryable error `PROFILE_NOT_FOUND`.

## 9. NotificationComposerAgent

### Input

```json
{
  "user_id": "uuid",
  "event": {
    "event_id": "uuid",
    "title": "string",
    "datetime_start": "2026-03-05T20:00:00+08:00"
  },
  "notify_reason": "string",
  "recent_notifications": [
    {"title": "string", "sent_at": "2026-03-01T12:00:00+08:00"}
  ]
}
```

### Output `data`

```json
{
  "title": "string <=100 chars",
  "body": "string <=200 chars",
  "deep_link": "aff://events/{event_id}",
  "priority": "low|medium|high"
}
```

### Failure Behavior

- If message exceeds limits, truncate deterministically and include warning in `meta`.
