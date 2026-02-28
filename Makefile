API_DIR := services/api
UV ?= uv
HOST ?= 0.0.0.0
PORT ?= 8000

.PHONY: run test lint

run:
	docker compose up --build

test:
	cd $(API_DIR) && $(UV) run pytest -q

lint:
	cd $(API_DIR) && $(UV) run ruff check . && $(UV) run pyrefly check .
