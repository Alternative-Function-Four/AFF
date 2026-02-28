"""Alembic environment for async SQLAlchemy migrations."""
# ruff: noqa: E402

from __future__ import annotations

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_CANDIDATE_ROOTS = {
    _PROJECT_ROOT,
    _PROJECT_ROOT / "services" / "api",
    _PROJECT_ROOT.parent,
    Path(__file__).resolve().parent,
    Path.cwd(),
}
for _root in _CANDIDATE_ROOTS:
    if _root.is_dir() and str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from entities import Base
from database import DATABASE_URL

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://") :]
    if url.startswith("sqlite:///"):
        return "sqlite+aiosqlite:///" + url[len("sqlite:///") :]
    return url


target_metadata = Base.metadata


def _url() -> str:
    return _normalize_database_url(
        os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url", DATABASE_URL)),
    )


def run_migrations_offline() -> None:
    context.configure(
        url=_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(_url(), poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
