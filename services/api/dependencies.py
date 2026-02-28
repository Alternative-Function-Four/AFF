from __future__ import annotations

import uuid
from typing import Any

from fastapi import Depends, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException as StarletteHTTPException

from logic import now_sg
from models import ErrorEnvelope, UserRecord
from state import STORE
from storage_service import get_session, get_user_by_id


class APIError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


bearer = HTTPBearer(auto_error=False)


def request_id_for(request: Request) -> str:
    value = getattr(request.state, "request_id", None)
    if value:
        return str(value)
    fallback = f"req_{uuid.uuid4().hex[:12]}"
    request.state.request_id = fallback
    return fallback


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any],
) -> JSONResponse:
    payload = ErrorEnvelope(
        code=code,
        message=message,
        details=details,
        request_id=request_id_for(request),
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


def register_handlers(app: Any) -> None:
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request.state.request_id = f"req_{uuid.uuid4().hex[:12]}"
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        return error_response(request, exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return error_response(
            request=request,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="INVALID_REQUEST",
            message="Validation failed",
            details={"errors": exc.errors()},
        )

    @app.exception_handler(StarletteHTTPException)
    async def starlette_error_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        code_map = {
            400: "INVALID_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "INVALID_REQUEST",
        }
        message_map = {
            401: "Authentication required",
            403: "Forbidden",
            404: "Resource not found",
        }
        return error_response(
            request=request,
            status_code=exc.status_code,
            code=code_map.get(exc.status_code, "HTTP_ERROR"),
            message=message_map.get(exc.status_code, "Request failed"),
            details={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return error_response(
            request=request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_ERROR",
            message="Internal server error",
            details={"error": type(exc).__name__},
        )


async def get_db_session() -> AsyncSession:
    from database import get_db_session as get_db_session_ctx

    async with get_db_session_ctx() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db_session),
) -> UserRecord:
    if credentials is None:
        raise APIError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="Authentication required",
            details={"auth": "bearer"},
        )

    session = await get_session(db, credentials.credentials)
    if session is None or session.expires_at < now_sg(STORE):
        raise APIError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="Invalid or expired token",
            details={"token": "expired_or_unknown"},
        )

    user = await get_user_by_id(db, session.user_id)
    if user is None:
        raise APIError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="Invalid session user",
            details={"user_id": session.user_id},
        )

    return user


async def get_admin_user(user: UserRecord = Depends(get_current_user)) -> UserRecord:
    if user.role != "admin":
        raise APIError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="ADMIN_REQUIRED",
            message="Admin role required",
            details={"role": user.role},
        )
    return user
