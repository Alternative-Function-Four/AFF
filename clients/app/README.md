# AFF Frontend Client

Expo React Native client scaffold aligned with `docs/spec/02-architecture/FRONTEND_CLIENT_ARCHITECTURE.md`.

## Run

1. Copy `.env.example` to `.env` and adjust `EXPO_PUBLIC_API_BASE_URL`.
2. Install dependencies: `npm install`.
3. Start app: `npm run start`.
4. Optional web debug admin: `npm run web` with `EXPO_PUBLIC_ENABLE_ADMIN=true`.

## Validate

- Typecheck: `npm run typecheck`
- Tests: `npm run test`
- Web export build: `npm run build`

## Production Build Input

`EXPO_PUBLIC_API_BASE_URL` is compiled into the web bundle at build time. For deployment builds, use an HTTPS backend URL.

Do not deploy with localhost/127.0.0.1 or plain HTTP API URLs.

## Included routes

- `/login`
- `/onboarding`
- `/feed`
- `/event/:eventId`
- `/notifications`
- `/preferences`
- `/admin/sources`
- `/admin/source/:sourceId`
- `/admin/ingestion`
- `/admin/notifications`

## Notes

- API integration uses typed contracts mapped to `docs/spec/04-api/OPENAPI.yaml`.
- Session persistence uses secure storage on native and session storage on web.
- Admin route group is only available when admin mode is enabled and the current role is `admin`.
