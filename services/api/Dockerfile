FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/services/api

RUN pip install --no-cache-dir uv

COPY services/api/pyproject.toml services/api/uv.lock /app/services/api/

WORKDIR /app/services/api

RUN uv sync --locked --no-dev
ENV PATH="/app/services/api/.venv/bin:${PATH}"

COPY services/api /app/services/api

EXPOSE 8000

CMD ["sh", "-lc", "uv run alembic -c alembic.ini upgrade head && uv run uvicorn main:app --host 0.0.0.0 --port 8000"]
