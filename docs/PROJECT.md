# AFF Project Overview

AFF is a Singapore-first personalized activity assistant prototype focused on events, food, and nightlife.

The project currently uses a docs-first execution model. Canonical specifications live under `docs/spec/`.

## Read This First

- `docs/spec/README.md`
- `docs/spec/01-product/PRD.md`
- `docs/spec/04-api/API_CONTRACT.md`
- `docs/spec/06-delivery/HACKATHON_6H_PLAN.md`

## What This Repository Contains

- `services/api`: FastAPI scaffold for v1 endpoints
- `services/ingestion`: async ingestion worker scaffold
- `schemas`: SQL schema baseline
- `infra`: infrastructure baseline
- `docs/spec`: decision-complete spec kit

## Delivery Goal

Build a working 6-hour hackathon prototype with:

- Demo auth
- Personalized feed
- Source ingestion and dedup flow
- Feedback-driven reranking
- Notification gating and logging
- Lightweight admin source controls
