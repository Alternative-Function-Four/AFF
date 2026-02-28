from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from core.settings import settings
from entities import Base
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


DATABASE_URL = settings.normalized_database_url()


engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


def _ensure_sqlite_schema(connection) -> None:  # type: ignore[no-untyped-def]
    inspector = inspect(connection)
    if inspector is None:
        return
    if "events" not in inspector.get_table_names():
        return

    event_columns = {column["name"] for column in inspector.get_columns("events")}
    if "indoor_outdoor" not in event_columns:
        connection.exec_driver_sql(
            "ALTER TABLE events "
            "ADD COLUMN indoor_outdoor VARCHAR(16) NOT NULL DEFAULT 'indoor'"
        )


async def init_db_schema() -> None:
    async with engine.begin() as connection:
        if connection.dialect.name == "postgresql":
            await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await connection.run_sync(Base.metadata.create_all)
        if connection.dialect.name == "sqlite":
            await connection.run_sync(_ensure_sqlite_schema)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        try:
            yield session
        finally:
            await session.close()
