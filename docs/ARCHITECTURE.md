# AFF Architecture Overview

This document is a concise index. Detailed architecture specifications live in `docs/spec/02-architecture/`.

## Architecture Summary

- Style: modular monolith API + async ingestion worker
- Runtime: FastAPI + PostgreSQL (+ pgvector) + Redis + queue + S3 raw payload storage
- Scope: Singapore-only hackathon prototype
- Source policy: API/RSS/ICS first, HTML extraction only through allowlist approval

## Detailed Specs

- `docs/spec/02-architecture/SYSTEM_ARCHITECTURE.md`
- `docs/spec/02-architecture/AGENT_CONTRACTS.md`
- `docs/spec/03-data/DATA_MODEL.md`
- `docs/spec/03-data/SOURCE_POLICY.md`
- `docs/spec/05-ops/OBSERVABILITY_AND_SLO.md`
- `docs/spec/05-ops/RUNBOOKS.md`

## API and Delivery References

- `docs/spec/04-api/API_CONTRACT.md`
- `docs/spec/04-api/OPENAPI.yaml`
- `docs/spec/06-delivery/HACKATHON_6H_PLAN.md`
- `docs/spec/06-delivery/ACCEPTANCE_CRITERIA.md`
