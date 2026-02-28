# Runbooks

Operational procedures for known high-risk incidents.

## Runbook 1: Source Crawl Failures

### Trigger

Source parse success ratio drops below 75 percent for two consecutive runs.

### Steps

1. Identify affected `source_id` from metrics.
2. Inspect latest `source_validations` and worker logs by `run_id`.
3. Determine failure class:
   - network/access issue
   - payload format change
   - policy block
4. If format changed, set source status to `paused`.
5. Trigger `SourceValidatorAgent` revalidation.
6. Update source extraction hints and resume only after successful dry run.

### Exit Criteria

- Parse success ratio >= 90 percent in one verification run.

## Runbook 2: Dedup Anomalies

### Trigger

Manual review identifies false merges or duplicate cards in feed.

### Steps

1. Query `event_source_links` and `event_occurrences` for impacted events.
2. Inspect dedup confidence and reasoning stored at merge time.
3. If false merge:
   - split event into separate canonical rows
   - relink `event_source_links`
4. If missed duplicate:
   - merge canonical rows and preserve provenance links
5. Record corrective action in ops log.

### Exit Criteria

- No duplicate card appears for same real-world event in validation feed query.

## Runbook 3: Notification Throttling Breach

### Trigger

User receives more than max allowed notifications per day or repeated messages.

### Steps

1. Check `notification_logs` for user and day window.
2. Verify suppression logic against quota and quiet-hour rules.
3. Temporarily enforce hard cap at query layer if gate is failing.
4. Backfill suppression_reason for over-sent rows.
5. Patch and redeploy gate logic.

### Exit Criteria

- Next validation test shows strict cap adherence.

## Runbook 4: API Rollback

### Trigger

Critical API regressions affecting auth/feed/events.

### Steps

1. Identify last known good artifact tag.
2. Roll back API service to previous artifact.
3. Run smoke tests: `/health`, `/v1/auth/demo-login`, `/v1/feed`.
4. Validate no schema mismatch with current DB migration level.
5. Re-enable traffic.

### Exit Criteria

- Smoke tests pass and latency returns to normal thresholds.

## Runbook 5: Queue Backlog

### Trigger

Oldest ingestion job age > 20 minutes.

### Steps

1. Inspect worker concurrency and job failure distribution.
2. Restart failed worker instances if needed.
3. Pause non-critical source runs.
4. Re-queue stuck jobs with idempotency keys preserved.

### Exit Criteria

- Queue age below 5 minutes for 10 continuous minutes.
