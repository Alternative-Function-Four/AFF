from __future__ import annotations

from typing import Any, Callable

from fastapi import Depends, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.exceptions import HTTPException as StarletteHTTPException

from core import make_request_id, now_sg
from models import ErrorEnvelope, FlexibleObject, UserRecord
from state import STORE


class APIError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: FlexibleObject | dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        if details is None:
            self.details = FlexibleObject()
        elif isinstance(details, FlexibleObject):
            self.details = details
        else:
            self.details = FlexibleObject.model_validate(details)


bearer = HTTPBearer(auto_error=False)


def request_id_for(request: Request) -> str:
    value = getattr(request.state, "request_id", None)
    if value:
        return str(value)
    fallback = make_request_id()
    request.state.request_id = fallback
    return fallback


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: FlexibleObject | dict[str, Any],
) -> JSONResponse:
    details_model = details if isinstance(details, FlexibleObject) else FlexibleObject.model_validate(details)
    payload = ErrorEnvelope(
        code=code,
        message=message,
        details=details_model,
        request_id=request_id_for(request),
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


def register_handlers(app: Any) -> None:
    @app.middleware("http")
    async def request_id_middleware(
        request: Request,
        call_next: Callable[..., Any],
    ) -> JSONResponse:
        request.state.request_id = make_request_id()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        return error_response(request, exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response(
            request=request,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="INVALID_REQUEST",
            message="Validation failed",
            details={"errors": exc.errors()},
        )

    @app.exception_handler(StarletteHTTPException)
    async def starlette_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
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


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> UserRecord:
    if credentials is None:
        raise APIError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="Authentication required",
            details={"auth": "bearer"},
        )

    session = STORE.sessions.get(credentials.credentials)
    if session is None or session.expires_at < now_sg(STORE):
        raise APIError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="Invalid or expired token",
            details={"token": "expired_or_unknown"},
        )

    user = STORE.users.get(session.user_id)
    if user is None:
        raise APIError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="Invalid session user",
            details={"user_id": session.user_id},
        )
    return user


def get_admin_user(user: UserRecord = Depends(get_current_user)) -> UserRecord:
    if user.role != "admin":
        raise APIError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="ADMIN_REQUIRED",
            message="Admin role required",
            details={"role": user.role},
        )
    return user
