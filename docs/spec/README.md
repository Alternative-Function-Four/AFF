# AFF Spec Kit

Decision-complete specification pack for the AFF Singapore hackathon prototype.

## Purpose

This spec kit is the single source of truth for product scope, architecture, APIs, data model, operations, and delivery execution.

## Locked Decisions

- Date locked: 2026-02-28
- Launch geography: Singapore only
- Architecture: modular monolith FastAPI API + separate async ingestion worker
- Frontend: Expo React Native + TypeScript (`expo-router`, TanStack Query, Zustand)
- Source policy: API/RSS/ICS first; HTML scraping only through explicit allowlist approval
- MVP verticals: events + food + nightlife + sports + sightseeing + museums + outdoors + movies
- Client scope: mobile app primary + lightweight admin; web build allowed only for debugging
- Prototype auth: demo login required; email-password is a documented optional implementation stub
- Deliverable: docs-only spec kit

## Document Map

- `01-product/PRD.md`: product goals, personas, MVP scope, non-goals, launch constraints
- `01-product/USER_FLOWS.md`: end-to-end user and admin flows with state transitions
- `02-architecture/SYSTEM_ARCHITECTURE.md`: runtime architecture, module boundaries, dependency graph
- `02-architecture/FRONTEND_CLIENT_ARCHITECTURE.md`: frontend runtime surfaces, routing, state model, API integration, test and delivery constraints
- `02-architecture/AGENT_CONTRACTS.md`: strict contracts for source, ingestion, recommendation, and notification agents
- `03-data/DATA_MODEL.md`: canonical entities, schema rules, constraints, indexes, retention, lineage
- `03-data/SOURCE_POLICY.md`: source ingestion policy and legal/risk control workflow
- `04-api/API_CONTRACT.md`: endpoint-level contract with auth, payloads, errors, examples
- `04-api/OPENAPI.yaml`: machine-readable API contract
- `05-ops/OBSERVABILITY_AND_SLO.md`: metrics, SLOs, alerting thresholds
- `05-ops/RUNBOOKS.md`: operational response playbooks
- `06-delivery/ACCEPTANCE_CRITERIA.md`: measurable definition of done and verification matrix

## Build Order

1. `04-api/API_CONTRACT.md` + `03-data/DATA_MODEL.md`
2. `02-architecture/AGENT_CONTRACTS.md`
3. `03-data/SOURCE_POLICY.md`
4. `02-architecture/FRONTEND_CLIENT_ARCHITECTURE.md`
5. `05-ops/OBSERVABILITY_AND_SLO.md` + `05-ops/RUNBOOKS.md`
6. `01-product/PRD.md` + `01-product/USER_FLOWS.md`
7. `06-delivery/ACCEPTANCE_CRITERIA.md`
8. Final consistency pass against `04-api/OPENAPI.yaml`

## Decision Ledger

- No unresolved placeholders are permitted.
- Any future decision change must update this file and all impacted specs in the same commit.
- In case of contradiction, priority order is:
  1. `04-api/OPENAPI.yaml`
  2. `03-data/DATA_MODEL.md`
  3. `02-architecture/SYSTEM_ARCHITECTURE.md`
  4. Remaining documents
