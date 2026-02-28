FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/services/api

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    sqlalchemy \
    asyncpg \
    aiosqlite \
    alembic \
    pydantic \
    httpx

COPY services/api /app/services/api

WORKDIR /app/services/api

EXPOSE 8000

CMD ["sh", "-lc", "alembic -c alembic.ini upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]
