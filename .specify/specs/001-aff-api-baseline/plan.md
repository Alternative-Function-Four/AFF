# Implementation Plan: AFF API Baseline

## Technology Stack

### Backend
- Framework: FastAPI
- Validation: Pydantic models
- Storage: In-memory repository layer
- Testing: pytest + FastAPI TestClient

## Architecture

### System Overview
- Single FastAPI app exposing all v1 endpoints.
- In-memory `Store` object keeps users, sessions, preferences, events, interactions, sources, ingestion jobs, and notification logs.
- Deterministic ranking module computes feed scores using preference and interaction signals.

### Component Design

#### API Layer
- Request validation, auth checks, and contract-shaped responses.
- Global error envelope handler for both validation and runtime exceptions.

#### Domain Rules
- Feed scorer with additive penalties/bonuses.
- Notification policy gate for daily cap and quiet hours.
- Source policy gate for ingestion eligibility.

#### Repository Layer
- Mutable state container with helper lookups by user/token/event/source.

## Security Considerations

- Bearer token required for protected routes.
- Admin role required for `/v1/admin/*` routes.
- Uniform failure envelope avoids leaking internals.

## Performance Strategy

- O(n) in-memory ranking and filtering for prototype scale.
- Lightweight datetime handling with fixed Singapore timezone.

## Error Handling

- Return `ErrorEnvelope` with `code`, `message`, `details`, `request_id`.
- Map common failures to 4xx/5xx with deterministic codes.
