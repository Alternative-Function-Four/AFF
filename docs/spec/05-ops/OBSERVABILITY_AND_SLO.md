# Observability and SLO

## 1. SLO Targets (Prototype)

- API availability during demo: >= 99 percent
- Feed latency p95: <= 600 ms
- Event detail latency p95: <= 400 ms
- Ingestion completion for <= 50 sources: <= 15 minutes
- Source parse success rate: >= 90 percent per approved source
- Notification duplicate rate: <= 1 percent
- Notification daily cap enforcement accuracy: 100 percent in tests

## 2. Required Metrics

## API Metrics

- `api_requests_total{route,method,status}`
- `api_request_duration_ms{route,method,p50,p95,p99}`
- `api_auth_failures_total{reason}`

## Ingestion Metrics

- `ingestion_jobs_total{status}`
- `ingestion_job_duration_seconds`
- `source_fetch_success_ratio{source_id}`
- `raw_events_extracted_total{source_id}`
- `normalization_low_confidence_total`
- `dedup_merge_action_total{action}`

## Recommendation Metrics

- `feed_candidates_total`
- `feed_ranked_items_total`
- `recommendation_score_distribution`
- `feedback_signal_total{signal}`

## Notification Metrics

- `notification_candidates_total`
- `notification_sent_total`
- `notification_suppressed_total{reason}`
- `notification_send_failures_total`

## Policy Metrics

- `sources_by_status{status}`
- `sources_policy_risk_distribution`
- `sources_revalidation_overdue_total`

## 3. Logging Standard

Each log line must include:

- `timestamp`
- `level`
- `service`
- `request_id` or `run_id`
- `user_id` (if available)
- `source_id` or `event_id` (if applicable)
- `message`
- `payload` (structured JSON object)

PII must not be logged in plaintext.

## 4. Tracing Strategy

- Generate `request_id` at API ingress and propagate to all downstream operations.
- Generate `run_id` per ingestion job and propagate through each stage.
- Link recommendation generation and notification logs via shared `request_id`.

## 5. Alert Thresholds

- Feed p95 > 900 ms for 5 minutes: warning
- Feed p95 > 1200 ms for 5 minutes: critical
- Parse success ratio < 75 percent on approved source for 2 consecutive runs: warning + auto-pause candidate
- Notification duplicate rate > 3 percent over 1 hour: critical
- Ingestion queue oldest job age > 20 minutes: warning

## 6. Dashboard Requirements

Minimum dashboard panels:

- API throughput and latency by endpoint
- Ingestion throughput and failures by source
- Dedup action split (`create_new`, `merge_sources`, `skip`)
- Feed coverage and recommendation score distribution
- Notifications sent vs suppressed with reason breakdown
