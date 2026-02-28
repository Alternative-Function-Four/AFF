# Activity Assistant SpecKit

Monorepo scaffold for proactive local activity suggestion assistant.

## Services

- `services/api`: FastAPI backend prototype for AFF v1 endpoints.
- `clients/app`: Expo React Native frontend scaffold aligned with frontend architecture spec.

## Quick Start

1. API: `make run`
2. Frontend env: copy `clients/app/.env.example` to `clients/app/.env`
3. Frontend deps: `cd clients/app && npm install`
4. Frontend app: `make app-start` (native) or `make app-web` (debug web)
