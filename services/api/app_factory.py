from fastapi import FastAPI

from dependencies import register_handlers
from routes_admin import router as admin_router
from routes_public import router as public_router


def create_app() -> FastAPI:
    app = FastAPI(title="AFF API", version="1.0.0")
    register_handlers(app)
    app.include_router(public_router)
    app.include_router(admin_router)
    return app


app = create_app()
