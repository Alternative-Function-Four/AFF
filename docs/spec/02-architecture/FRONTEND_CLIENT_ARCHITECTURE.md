# Frontend Client Architecture

## 1. Purpose and Scope

This document specifies the AFF frontend client architecture for the Singapore hackathon prototype.

Scope covered:

- End-user mobile client for onboarding, feed, event details, and notifications.
- Lightweight admin surface for source registration, approval, and ingestion trigger.
- Debug web build for internal testing only.

Out of scope:

- Public marketing website.
- Production-grade identity provider integration.
- Full moderation backoffice.

## 2. Locked Frontend Decisions

- Primary client framework: Expo React Native with TypeScript.
- Routing: `expo-router` with typed route params.
- Server state: TanStack Query.
- Local UI/session state: Zustand.
- Form handling: React Hook Form + Zod validation.
- Design system approach: token-based shared primitives with platform-aware wrappers.
- Admin surface strategy: internal-only web route group in same Expo codebase, enabled only in debug/admin mode.
- Timezone handling: always `Asia/Singapore` presentation and query defaults.
- Currency and units: `SGD` and kilometers by default.

## 3. Product Alignment

Frontend must preserve the product goals and constraints in `../01-product/PRD.md`:

- Show at least 20 ranked cards when available.
- Reflect feedback impact on subsequent feed retrieval.
- Preserve source provenance visibility in card and detail surfaces.
- Keep prototype behavior aligned with non-goals (no checkout, no social graph, no public web app).

## 4. Runtime Surfaces

## 4.1 User Mobile App (Primary)

- Platforms: iOS and Android via Expo runtime.
- Key capabilities:
  - Demo login.
  - Preferences capture/update.
  - Ranked feed retrieval.
  - Event details.
  - Feedback signals (`interested`, `not_for_me`, `already_knew`).
  - Notification history and test trigger.

## 4.2 Internal Admin Surface (Lightweight)

- Platform: Expo web debug build only.
- Access: explicit admin mode toggle and admin token required.
- Key capabilities:
  - Create source.
  - List/filter sources.
  - Approve/reject source.
  - Trigger ingestion run.
  - View recent ingestion and policy statuses returned by API.

## 4.3 Debug Web Build (Non-Public)

- Allowed only for engineering verification and demo rehearsal.
- Must not be discoverable as a public production website.
- Deploy only to protected preview environment or local development host.

## 5. Client Architecture

## 5.1 Layering

Frontend code is split into strict layers:

1. `app/` route entrypoints and layout composition.
2. `features/` user/admin feature modules.
3. `entities/` domain model adapters and mappers.
4. `shared/` cross-cutting primitives (api client, tokens, components, utils).

No route file may call `fetch` directly; all network access goes through the shared API client and typed feature hooks.

## 5.2 Recommended Repository Structure

```text
clients/app/
  app/
    (public)/
      login.tsx
    (user)/
      onboarding.tsx
      feed.tsx
      event/[eventId].tsx
      notifications.tsx
      preferences.tsx
    admin/
      _layout.tsx
      sources.tsx
      source/[sourceId].tsx
      ingestion.tsx
  src/
    features/
      auth/
      preferences/
      feed/
      events/
      notifications/
      admin/
    entities/
      event/
      source/
      profile/
    shared/
      api/
      state/
      ui/
      config/
      telemetry/
      time/
```

## 5.3 Environment Configuration

Required client environment variables:

- `EXPO_PUBLIC_API_BASE_URL`
- `EXPO_PUBLIC_APP_ENV` (`local|preview|demo`)
- `EXPO_PUBLIC_ENABLE_ADMIN` (`true|false`)
- `EXPO_PUBLIC_DEFAULT_LAT`
- `EXPO_PUBLIC_DEFAULT_LNG`

Build fails if API base URL is missing.

## 6. Navigation and Screen Contracts

## 6.1 User Route Map

- `/login`
- `/onboarding`
- `/feed`
- `/event/:eventId`
- `/notifications`
- `/preferences`

## 6.2 Admin Route Map

- `/admin/sources`
- `/admin/source/:sourceId`
- `/admin/ingestion`

Admin routes are hidden unless both conditions are true:

- `EXPO_PUBLIC_ENABLE_ADMIN=true`
- Authenticated `AuthSessionResponse.user.role` equals `admin`.

## 6.3 Screen Requirements

### Login

- Uses `POST /v1/auth/demo-login`.
- Stores bearer token + `expires_at`.
- On success:
  - If no preferences profile: navigate to onboarding.
  - Else: navigate to feed.

### Onboarding

- Collects category preferences, budget mode, preferred time, anti-preferences, distance.
- Persists via `PUT /v1/preferences`.
- Navigates to feed after successful save.

### Feed

- Calls `GET /v1/feed` with required `lat`, `lng`, `time_window`, `budget`, `mode`.
- Renders each card with:
  - title
  - start datetime
  - venue
  - category
  - price summary
  - reason chips
  - source provenance preview
- If `coverage_warning` is present, show non-blocking warning banner.
- Supports pull-to-refresh and pagination-ready list primitives.

### Event Detail

- Calls `GET /v1/events/{event_id}`.
- Shows canonical details, all occurrences, and full provenance links.
- Supports feedback submission via `POST /v1/events/{event_id}/feedback`.

### Notifications

- Calls `GET /v1/notifications`.
- Supports test trigger via `POST /v1/notifications/test`.
- Shows notification status timeline sorted by created timestamp descending.

### Preferences

- Calls `GET /v1/preferences` then `PUT /v1/preferences`.
- Persists changes optimistically with rollback on failure.

### Admin Sources

- Lists sources from `GET /v1/admin/sources`.
- Supports source creation via `POST /v1/admin/sources`.
- Supports approve/reject flow via `POST /v1/admin/sources/{source_id}/approve`.

### Admin Ingestion

- Triggers ingestion via `POST /v1/admin/ingestion/run`.
- Shows job id and queued count confirmation from API response.

## 7. API Integration Rules

## 7.1 API Client Contract

- Single HTTP client module with:
  - base URL from env
  - bearer token injection
  - request id logging
  - standardized error normalization
- All request/response payloads mapped to typed interfaces aligned with `../04-api/OPENAPI.yaml`.
- Error envelopes must surface `code`, `message`, and `request_id` in UI-safe form.

## 7.2 Auth and Session Rules

- Store token in secure storage:
  - Native: secure keychain abstraction.
  - Web debug: session storage only.
- Re-auth policy:
  - On `401`, clear session and return user to `/login`.
  - If `expires_at` is in past, force demo-login renewal before protected calls.

## 7.3 Query Key and Cache Rules

Canonical query keys:

- `["preferences"]`
- `["feed", lat, lng, time_window, budget, mode]`
- `["event", event_id]`
- `["notifications", limit]`
- `["admin", "sources", status]`

Invalidation rules:

- After feedback post: invalidate all `["feed", ...]` and `["event", event_id]`.
- After preferences update: invalidate `["preferences"]` and all `["feed", ...]`.
- After admin source approve/create: invalidate `["admin", "sources", ...]`.

## 8. State Management

## 8.1 Server State

- TanStack Query is source of truth for remote API data.
- Stale-time defaults:
  - feed: 30 seconds
  - event detail: 60 seconds
  - preferences: 5 minutes
  - notifications: 30 seconds
  - admin sources: 20 seconds

## 8.2 Local State

Zustand stores only:

- Session metadata (user id, role, token expiry).
- Non-persistent UI preferences (active filter chip, list layout mode).
- Feature flags resolved at app bootstrap.

Do not duplicate server payload entities in Zustand.

## 9. UX and Interaction Standards

## 9.1 Feed UX

- Initial load skeleton target: render placeholders within 300 ms.
- Card actions:
  - tap card opens detail.
  - inline feedback chips submit mutation with immediate UI acknowledgement.

## 9.2 Error UX

- Non-blocking network errors: top banner + retry control.
- Blocking auth errors: redirect to login.
- Validation errors: inline field messages with exact API field context when available.

## 9.3 Empty and Degraded States

- Empty feed with `coverage_warning`: explain limited source coverage and suggest broader time window.
- Notifications empty: show explanation of eligibility and quota behavior.
- Admin empty sources: show first-source creation CTA.

## 10. Timezone, Locale, and Formatting

- All user-facing datetimes rendered in `Asia/Singapore`.
- Relative labels allowed (`Tonight`, `This Weekend`) but must map to API `time_window` values.
- Currency rendering fixed to `SGD` for prototype.
- Distance rendered in kilometers with one decimal precision.

## 11. Security and Access Controls

- Never embed API secrets in client bundle.
- Admin views require server-verified admin role.
- Client must not expose hidden admin routes in navigation when not authorized.
- PII logging is prohibited; telemetry payloads include only user id hash and request id.

## 12. Observability for Frontend

## 12.1 Required Client Telemetry Events

- `auth_demo_login_started`
- `auth_demo_login_succeeded`
- `feed_request_started`
- `feed_request_succeeded`
- `feed_feedback_submitted`
- `feed_feedback_succeeded`
- `notification_test_triggered`
- `admin_source_approved`
- `admin_ingestion_run_triggered`

## 12.2 Required Telemetry Fields

- `timestamp`
- `user_id_hash`
- `request_id` (if API involved)
- `surface` (`mobile|admin_web`)
- `network_status`
- `duration_ms`

## 13. Performance Targets

- Cold start to interactive: <= 2.5 seconds on representative test device.
- Feed first meaningful content: <= 1.2 seconds on warm start + healthy network.
- Feedback mutation acknowledgement: <= 200 ms local UI response, <= 1 second server round-trip p95.
- Memory ceiling guideline for prototype: <= 220 MB active session.

## 14. Testing Strategy

## 14.1 Unit Tests

- Domain mappers for feed and event response normalization.
- Form validation schemas for onboarding and admin source create/approve.
- Session guard logic and token-expiry checks.

## 14.2 Integration Tests

- Auth -> onboarding -> feed happy path.
- Feedback mutation invalidates feed and changes ranking order visibility.
- Admin source approval and ingestion trigger flows.

## 14.3 End-to-End Tests

- New user completes onboarding and sees personalized feed with provenance.
- User submits both positive and negative feedback and sees subsequent feed change.
- Notification history and test-trigger flow function under quota constraints.
- Admin can create source, approve it, and trigger ingestion job.

## 15. Delivery and Rollout Constraints

- Frontend implementation must remain compatible with `../04-api/OPENAPI.yaml`.
- Any frontend contract change that impacts payload shape requires same-commit updates to:
  - `../04-api/API_CONTRACT.md`
  - `../04-api/OPENAPI.yaml`
  - this file
- No unresolved placeholders are allowed in this document.

## 16. Definition of Done (Frontend)

- All user flow screens listed in Section 6 are implemented and wired to v1 endpoints.
- Admin screens listed in Section 6 are available in debug/admin mode.
- Telemetry events in Section 12 are emitted in success and failure paths.
- Test suites in Section 14 pass in CI for at least one native target and one web debug run.
- Accessibility baseline:
  - touch targets >= 44 px
  - semantic labels present for primary controls
  - contrast ratio >= 4.5:1 for text content
