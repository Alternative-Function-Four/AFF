# Product Requirements Document (PRD)

## 1. Product Summary

AFF is a personalized local activity assistant for Singapore that recommends events, food experiences, nightlife, sports, sightseeing, museums, outdoors activities, and movies in a way that feels personal, timely, and non-generic.

The prototype must prove three things in one demo:

1. Multi-source ingestion can produce a unified canonical event list.
2. User preferences and feedback can alter ranking in a visible way.
3. Notification logic can alert only high-relevance, time-sensitive items without spam behavior.

## 2. Problem Statement

Users miss relevant local activities because available information is fragmented across many sources and generic recommendation products do not model nuanced preferences well.

## 3. Target Users

### Persona A: Busy Urban Professional

- Age 24-38, central Singapore
- Wants quality options after work without searching multiple apps
- Sensitive to travel time and crowded venues

### Persona B: Social Planner

- Age 22-34, plans weekend activities for friends
- Needs shortlists across events + food + nightlife + sports + sightseeing + museums + outdoors + movies
- Wants recommendations by vibe and budget

### Persona C: Niche Taste Explorer

- Age 20-40
- Prefers specific subcultures (indie gigs, craft coffee popups, underground comedy)
- Cares about "hidden gem" signal and dislikes mainstream noise

## 4. Product Goals

- G1: Deliver a personalized feed with at least 20 ranked cards per user context.
- G2: Improve rank relevance after explicit user feedback in the same session.
- G3: Deliver at most one high-priority notification per user per 6-hour demo window.
- G4: Maintain source provenance for every recommendation.

## 5. Non-Goals (Prototype)

- No payments or ticket checkout.
- No social graph, invites, or messaging.
- No public web product.
- No full production-grade auth stack.
- No fully automated unrestricted web crawling.

## 6. MVP Scope

### In Scope

- Demo auth login and authenticated API access.
- Preferences capture and update.
- Feed retrieval by location/time/budget/mode.
- Event detail retrieval.
- Feedback capture (`interested`, `not_for_me`, `already_knew`).
- Recommendation rerank using preference profile and interactions.
- Notification listing and test notification trigger.
- Admin source registration, source approval, and ingestion run trigger.
- Source ingestion policy enforcement metadata.

### Out of Scope

- Real email-password credential workflow.
- Full human moderation console UI.
- Multi-city support.

## 7. Singapore Launch Constraints

- All date-time handling uses `Asia/Singapore` timezone.
- Currency defaults to `SGD`.
- Distance defaults in kilometers.
- Source priority starts from Singapore-focused providers and local venue calendars.
- Policy compliance logs are mandatory for each source entry.

## 8. Success Metrics

### Product Metrics

- At least 80 percent of feed cards contain full title + start time + venue + source provenance.
- At least 70 percent of top-10 feed cards satisfy stated user preferences in test scenarios.
- Notification precision target in test set: at least 0.8 (true positive / all sent).

### Delivery Metrics

- Prototype API endpoints available per `OPENAPI.yaml` critical path.
- One end-to-end demo scenario runs without manual DB edits.
- All acceptance checks in `06-delivery/ACCEPTANCE_CRITERIA.md` pass.

## 9. Risks and Mitigations

- Source fragility: handled via source validation cadence and approval gate.
- Notification fatigue: handled by daily cap and notification eligibility score.
- Cold start: handled by explicit onboarding preferences and fast feedback loop.
- Policy risk: handled by API/RSS/ICS-first policy and legal-risk scoring.
