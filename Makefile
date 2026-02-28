API_DIR := services/api
UV ?= uv
HOST ?= 0.0.0.0
PORT ?= 8000

.PHONY: run test lint

run:
	cd $(API_DIR) && $(UV) run uvicorn main:app --reload --host $(HOST) --port $(PORT)

test:
	cd $(API_DIR) && $(UV) run pytest -q

lint:
	cd $(API_DIR) && $(UV) run ruff check .
