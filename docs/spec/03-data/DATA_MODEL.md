# Data Model

Canonical data model for the AFF Singapore prototype.

## 1. Storage Components

- PostgreSQL: canonical transactional data + vector embeddings (pgvector)
- S3: raw source payload archive with lifecycle retention
- Redis: transient cache only (no source-of-truth data)

## 2. Core Tables

## `users`

- `id` UUID PK
- `email` TEXT UNIQUE NULL (optional in demo auth)
- `display_name` TEXT NOT NULL
- `home_lat` DOUBLE PRECISION NULL
- `home_lng` DOUBLE PRECISION NULL
- `created_at` TIMESTAMPTZ NOT NULL
- `deleted_at` TIMESTAMPTZ NULL

## `auth_identities`

- `id` UUID PK
- `user_id` UUID FK -> users(id)
- `provider` TEXT NOT NULL (`demo|password|oauth_google|oauth_apple`)
- `provider_subject` TEXT NOT NULL
- `is_stub` BOOLEAN NOT NULL DEFAULT FALSE
- `created_at` TIMESTAMPTZ NOT NULL

Unique: (`provider`, `provider_subject`)

## `preferences`

- `user_id` UUID PK FK -> users(id)
- `preferred_categories` JSONB NOT NULL
- `preferred_subcategories` JSONB NOT NULL
- `budget_mode` TEXT NOT NULL
- `preferred_distance_km` NUMERIC(5,2) NOT NULL
- `active_days` TEXT NOT NULL (`weekday|weekend|both`)
- `preferred_times` JSONB NOT NULL
- `anti_preferences` JSONB NOT NULL
- `updated_at` TIMESTAMPTZ NOT NULL

## `sources`

- `id` UUID PK
- `name` TEXT NOT NULL
- `url` TEXT NOT NULL
- `source_type` TEXT NOT NULL
- `access_method` TEXT NOT NULL (`api|rss|ics|html_extract|manual`)
- `status` TEXT NOT NULL (`pending|approved|rejected|paused`)
- `policy_risk_score` SMALLINT NOT NULL
- `quality_score` SMALLINT NOT NULL
- `crawl_frequency_minutes` INTEGER NOT NULL
- `created_at` TIMESTAMPTZ NOT NULL
- `updated_at` TIMESTAMPTZ NOT NULL
- `deleted_at` TIMESTAMPTZ NULL

Unique: `url`

## `source_validations`

- `id` UUID PK
- `source_id` UUID FK -> sources(id)
- `validation_status` TEXT NOT NULL
- `is_active` BOOLEAN NOT NULL
- `is_parseable` BOOLEAN NOT NULL
- `freshness_estimate_hours` INTEGER NULL
- `policy_flags` JSONB NOT NULL
- `extraction_hints` JSONB NOT NULL
- `validated_at` TIMESTAMPTZ NOT NULL
- `validator` TEXT NOT NULL

## `raw_events`

- `id` UUID PK
- `source_id` UUID FK -> sources(id)
- `external_event_id` TEXT NULL
- `payload_ref` TEXT NOT NULL (S3 path or inline pointer)
- `raw_title` TEXT NULL
- `raw_date_or_schedule` TEXT NULL
- `raw_location` TEXT NULL
- `raw_description` TEXT NULL
- `raw_price` TEXT NULL
- `raw_url` TEXT NULL
- `raw_media_url` TEXT NULL
- `captured_at` TIMESTAMPTZ NOT NULL
- `deleted_at` TIMESTAMPTZ NULL

## `events`

- `id` UUID PK
- `title` TEXT NOT NULL
- `category` TEXT NOT NULL
- `subcategory` TEXT NULL
- `description` TEXT NULL
- `venue_name` TEXT NULL
- `venue_address` TEXT NULL
- `venue_lat` DOUBLE PRECISION NULL
- `venue_lng` DOUBLE PRECISION NULL
- `price_min` NUMERIC(10,2) NULL
- `price_max` NUMERIC(10,2) NULL
- `currency` TEXT NULL
- `is_recurring` BOOLEAN NOT NULL
- `recurrence_rule` TEXT NULL
- `embedding` VECTOR(3072) NULL
- `source_confidence` NUMERIC(4,3) NOT NULL
- `created_at` TIMESTAMPTZ NOT NULL
- `updated_at` TIMESTAMPTZ NOT NULL
- `deleted_at` TIMESTAMPTZ NULL

## `event_occurrences`

- `id` UUID PK
- `event_id` UUID FK -> events(id)
- `datetime_start` TIMESTAMPTZ NOT NULL
- `datetime_end` TIMESTAMPTZ NULL
- `timezone` TEXT NOT NULL DEFAULT 'Asia/Singapore'
- `dedup_block_key` TEXT NOT NULL
- `created_at` TIMESTAMPTZ NOT NULL

## `event_source_links`

- `id` UUID PK
- `event_id` UUID FK -> events(id)
- `raw_event_id` UUID FK -> raw_events(id)
- `source_id` UUID FK -> sources(id)
- `source_url` TEXT NULL
- `external_event_id` TEXT NULL
- `merge_confidence` NUMERIC(4,3) NOT NULL
- `first_seen_at` TIMESTAMPTZ NOT NULL
- `last_seen_at` TIMESTAMPTZ NOT NULL

Unique: (`event_id`, `raw_event_id`)

## `recommendations`

- `id` UUID PK
- `user_id` UUID FK -> users(id)
- `event_id` UUID FK -> events(id)
- `context_hash` TEXT NOT NULL
- `rank_position` INTEGER NOT NULL
- `relevance_score` NUMERIC(4,3) NOT NULL
- `reasons` JSONB NOT NULL
- `notify_immediately` BOOLEAN NOT NULL
- `created_at` TIMESTAMPTZ NOT NULL

Index: (`user_id`, `created_at` DESC)

## `interactions`

- `id` UUID PK
- `user_id` UUID FK -> users(id)
- `event_id` UUID FK -> events(id)
- `signal` TEXT NOT NULL (`interested|not_for_me|already_knew|saved|dismissed|opened`)
- `context` JSONB NOT NULL
- `created_at` TIMESTAMPTZ NOT NULL

## `notification_logs`

- `id` UUID PK
- `user_id` UUID FK -> users(id)
- `event_id` UUID FK -> events(id)
- `notification_type` TEXT NOT NULL
- `priority` TEXT NOT NULL
- `title` TEXT NOT NULL
- `body` TEXT NOT NULL
- `status` TEXT NOT NULL (`queued|sent|suppressed|failed`)
- `suppression_reason` TEXT NULL
- `sent_at` TIMESTAMPTZ NULL
- `created_at` TIMESTAMPTZ NOT NULL

## 3. Constraints and Integrity Rules

- Source URL must be unique across active and paused sources.
- Every canonical event must be linked to at least one raw event via `event_source_links`.
- `event_occurrences.datetime_start` is required for feed eligibility.
- Soft delete (`deleted_at`) is mandatory on mutable external entities (`sources`, `raw_events`, `events`).

## 4. Required Indexes

- Sources polling: index on `sources(status, crawl_frequency_minutes)`
- Feed retrieval: composite index on `event_occurrences(datetime_start, timezone)`
- Geo filtering: index on `(venue_lat, venue_lng)` (or PostGIS index if enabled)
- Vector similarity: HNSW index on `events.embedding`
- Recommendation history: index on `recommendations(user_id, created_at DESC)`
- Interaction lookup: index on `interactions(user_id, created_at DESC)`

## 5. Lineage

`source -> raw_events -> event_source_links -> events + event_occurrences -> recommendations -> notification_logs`

Lineage is mandatory for explainability and policy auditing.

## 6. Retention Defaults

- Raw source payloads in S3: 30 days lifecycle retention.
- `raw_events` rows: 30 days then purge if linked canonical data exists.
- Canonical events and lineage: retained for historical explainability.
- Notification logs: retain 90 days for anti-spam and audit.
