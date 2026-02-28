# Deployment Summary

Frontend is deployed with AWS CDK to S3 + CloudFront, and uses a separate CloudFront edge distribution to expose the HTTP backend over HTTPS for browser-safe calls.

## Active Preview Deployment

- Region: `ap-southeast-1`
- Frontend stack: `AffFrontend-preview-andrew`
- Frontend URL: `https://d3oxivhacb7ukl.cloudfront.net`
- Frontend distribution ID: `E2PTR3MQII9ENR`
- API edge stack: `AffBackendEdge-preview-andrew`
- API edge URL: `https://d228nc1qg7dv48.cloudfront.net`
- API edge distribution ID: `E8EZQ5G4WWDA1`

## Manual Frontend Redeploy

```bash
./scripts/deploy.sh <environment> --api-base-url <https-backend-url>
```

Examples:

```bash
./scripts/deploy.sh preview-andrew --api-base-url https://d228nc1qg7dv48.cloudfront.net
./scripts/deploy.sh prod --api-base-url https://d228nc1qg7dv48.cloudfront.net
```

## What the Script Deploys

- `AffBackendEdge-<environment>`
  - CloudFront HTTPS edge
  - Origin: `13.213.39.225:8000` (HTTP)
  - Output: `ApiEdgeUrl`
- `AffFrontend-<environment>`
  - S3 bucket + CloudFront static website hosting
  - Upload source: `clients/app/dist`
  - Output: `FrontendUrl`

## Validation Checklist

1. Backend edge health:

```bash
curl -i https://<api-edge-url>/health
```

2. Frontend URL availability:

```bash
curl -I https://<frontend-url>
```

3. SPA deep-link fallback:

```bash
curl -I https://<frontend-url>/feed
```

4. Browser test from frontend URL:
- Login/demo-login request succeeds
- Feed loads without mixed-content errors

## Notes

- `EXPO_PUBLIC_API_BASE_URL` is baked into the web bundle at build time.
- Deployment script blocks non-HTTPS API URLs and localhost values.
- If content appears stale, invalidate CloudFront cache:

```bash
aws cloudfront create-invalidation --distribution-id <distribution-id> --paths '/*'
```
