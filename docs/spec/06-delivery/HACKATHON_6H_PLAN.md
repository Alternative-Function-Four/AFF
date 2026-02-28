# Hackathon 6-Hour Delivery Plan

Objective: deliver a working prototype aligned with this spec kit in 6 hours.

## Team Assumption

Default plan assumes 2 contributors:

- Builder A: API + data model
- Builder B: ingestion + recommendation/notification path

If solo, execute the same sequence with strict priority order listed below.

## Timeline

## 0:00-0:45 (Contract Lock)

- Finalize `OPENAPI.yaml` and `DATA_MODEL.md` parity.
- Confirm endpoint and table names are stable.
- Implement minimal schema migration for required tables.

Deliverable:

- API and schema contracts locked, no naming ambiguity.

## 0:45-2:00 (Ingestion Spine)

- Build source list/create/approve endpoints.
- Implement ingestion run trigger.
- Implement worker stages: fetch mock payload -> normalize -> dedup action -> upsert canonical rows.
- Persist lineage links.

Deliverable:

- One approved source can produce at least one canonical event.

## 2:00-3:15 (Personalization Loop)

- Implement preferences GET/PUT.
- Implement interactions endpoint.
- Implement feed query and rank scoring function.
- Ensure feedback signal modifies ranking.

Deliverable:

- User can see ranking shift after feedback.

## 3:15-4:00 (Notification Path)

- Implement notification list endpoint.
- Implement notification gate + test trigger endpoint.
- Add caps: max 2/day and quiet-hours suppression.

Deliverable:

- At least one high-score event yields notification candidate; suppression behavior visible.

## 4:00-5:00 (Stability and Ops)

- Add request_id/run_id logs.
- Add key metrics instrumentation stubs.
- Validate runbooks against current implementation behavior.
- Test edge cases from acceptance criteria.

Deliverable:

- Operational confidence for live demo.

## 5:00-6:00 (Demo Hardening)

- Run full demo path twice with fresh demo users.
- Fix only critical issues affecting demo continuity.
- Freeze branch and prepare walkthrough.

Deliverable:

- Reliable demo script execution.

## Solo Priority Order (if time is tight)

1. Demo auth + preferences + feed endpoint
2. Ingestion run with one source and one event canonicalization
3. Feedback endpoint altering ranking
4. Notification test endpoint with caps
5. Admin source approval endpoint

## Demo Script (7-10 minutes)

1. Demo login as Singapore user persona.
2. Set preferences (nightlife + food, moderate budget, evening).
3. Trigger ingestion for approved source.
4. Open feed and show ranked cards with source provenance.
5. Submit `not_for_me` on top card and refresh feed.
6. Show ranking changed.
7. Trigger test notification for high-relevance item.
8. Open notification list and show logged result.
9. Show admin source status and policy metadata.

## Fallback Plans

- If worker queue fails: run ingestion synchronously through admin endpoint for demo only.
- If vector index unavailable: use deterministic scoring fallback by category/time/distance.
- If OAuth stubs fail: use demo login path exclusively.
