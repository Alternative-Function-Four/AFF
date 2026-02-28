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

## Deployment

Frontend manual deploy command:

```bash
./scripts/deploy.sh <environment> --api-base-url <https-backend-url>
```

Example:

```bash
./scripts/deploy.sh preview-andrew --api-base-url https://d1234567890.cloudfront.net
```

Current preview deployment:
- Frontend: `https://d3oxivhacb7ukl.cloudfront.net`
- API edge: `https://d228nc1qg7dv48.cloudfront.net`

The script deploys:
- `AffBackendEdge-<environment>`: HTTPS CloudFront edge that proxies to backend origin `13.213.39.225:8000`
- `AffFrontend-<environment>`: S3 + CloudFront static hosting for `clients/app/dist`

See [`DEPLOYMENT.md`](./DEPLOYMENT.md) for details and validation checks.
