from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import AsyncSessionFactory, init_db_schema
from dependencies import register_handlers
from routes_admin import router as admin_router
from routes_public import router as public_router
from state import load_store_snapshot
from storage_service import ensure_seed_data


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    async with AsyncSessionFactory() as db:
        await init_db_schema()
        snapshot = await ensure_seed_data(db)
        load_store_snapshot(snapshot)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="AFF API", version="1.0.0", lifespan=_lifespan)
    register_handlers(app)
    app.include_router(public_router)
    app.include_router(admin_router)
    return app


app = create_app()
