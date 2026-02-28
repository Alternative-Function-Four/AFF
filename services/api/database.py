from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from entities import Base

_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./aff.db")


def _normalize_database_url(value: str) -> str:
    if value.startswith("postgres://"):
        return "postgresql+asyncpg://" + value[len("postgres://") :]
    if value.startswith("postgresql://"):
        return "postgresql+asyncpg://" + value[len("postgresql://") :]
    if value.startswith("sqlite:///"):
        return "sqlite+aiosqlite:///" + value[len("sqlite:///") :]
    return value


DATABASE_URL = _normalize_database_url(_DATABASE_URL)


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


async def init_db_schema() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        try:
            yield session
        finally:
            await session.close()
