# Source Ingestion Policy

## 1. Policy Objective

Maximize recommendation quality while minimizing legal and maintenance risk.

## 2. Access Priority Order

1. Official API
2. RSS/Atom feed
3. ICS calendar feed
4. Manual curation
5. Allowlisted HTML extraction (exception path only)

HTML extraction is never default onboarding behavior.

## 3. Mandatory Source Metadata

Every source record must include:

- source URL and owner name
- source type
- access method
- terms URL (if available)
- robots policy check result
- attribution requirement
- caching allowance notes
- policy risk score
- approval decision and approver id

## 4. Risk Scoring Model

`policy_risk_score` in [0..100].

- 0-30: low risk (generally structured/public-friendly)
- 31-60: medium risk (needs manual review)
- 61-100: high risk (reject unless explicit legal sign-off)

Scoring factors:

- explicit anti-scraping terms
- unclear redistribution permissions
- aggressive anti-bot controls
- account-required access
- frequent structural instability

## 5. Approval Workflow

1. Candidate source created with status `pending`.
2. Validator records parseability and freshness evidence.
3. Policy check computes risk score and flags.
4. Admin approves or rejects:
   - approved: source can be queued
   - rejected: ingestion blocked
   - needs manual review: blocked until final decision

## 6. HTML Allowlist Exception Path

Allowed only if all conditions are true:

- No usable API/RSS/ICS alternative exists.
- Source has meaningful unique coverage value.
- Terms review does not show explicit prohibition.
- Rate-limited extraction plan is documented.
- Approval from designated operator is captured in source validation log.

## 7. Operational Guards

- Per-source rate limits are mandatory.
- Backoff and retry with jitter are mandatory.
- Failed parse ratio above threshold auto-pauses source.
- Source health is monitored daily.

## 8. Revalidation Cadence

- High-volume sources: every 24 hours
- Medium-volume sources: every 72 hours
- Low-volume sources: every 7 days
- Any source with two consecutive failures: immediate revalidation required

## 9. Enforcement in Runtime

- Admin ingestion trigger rejects non-approved sources.
- Worker refuses extraction when policy status is not `approved`.
- API exposes source status and policy flags for auditing.
