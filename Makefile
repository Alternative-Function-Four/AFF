API_DIR := services/api
APP_DIR := clients/app
UV ?= uv
HOST ?= 0.0.0.0
PORT ?= 8000

.PHONY: run test lint app-start app-web app-typecheck app-test

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

app-typecheck:
	cd $(APP_DIR) && npm run typecheck

app-test:
	cd $(APP_DIR) && npm run test
