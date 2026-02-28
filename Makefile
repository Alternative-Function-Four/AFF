API_DIR := services/api
APP_DIR := clients/app
UV ?= uv
HOST ?= 0.0.0.0
PORT ?= 8000
AWS_REGION ?= ap-southeast-1
FRONTEND_API_BASE_URL ?= https://d228nc1qg7dv48.cloudfront.net
DEPLOY_ENV ?= preview-$(shell whoami)

.PHONY: run test lint app-start app-web app-build app-typecheck app-test deploy-frontend deploy-preview deploy-prod

run:
	docker compose build --no-cache api && \
	docker compose up --build

test:
	cd $(API_DIR) && $(UV) run pytest -q

lint:
	cd $(API_DIR) && $(UV) run ruff check . && $(UV) run pyrefly check . \
		--disable-project-excludes-heuristics true \
		--project-excludes '**/node_modules' \
		--project-excludes '**/__pycache__' \
		--project-excludes '**/.venv/**' \
		--project-excludes '**/site-packages/**' \
		--project-excludes '**/venv/**'

app-start:
	cd $(APP_DIR) && EXPO_NO_TELEMETRY=1 npm run start

app-web:
	cd $(APP_DIR) && EXPO_NO_TELEMETRY=1 npm run web

app-build:
	cd $(APP_DIR) && npm run build

app-typecheck:
	cd $(APP_DIR) && npm run typecheck

app-test:
	cd $(APP_DIR) && npm run test

deploy-frontend:
	./scripts/deploy.sh $(DEPLOY_ENV) --api-base-url $(FRONTEND_API_BASE_URL) --region $(AWS_REGION)

deploy-preview:
	./scripts/deploy.sh preview-$(shell whoami) --api-base-url $(FRONTEND_API_BASE_URL) --region $(AWS_REGION)

deploy-prod:
	./scripts/deploy.sh prod --api-base-url $(FRONTEND_API_BASE_URL) --region $(AWS_REGION)
