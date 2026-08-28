import traceback

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.common import ErrorDetail, ErrorResponse

log = structlog.get_logger()


def _json_error(code: str, message: str, status: int) -> JSONResponse:
    detail = ErrorDetail(code=code, message=message)
    return JSONResponse(status_code=status, content=ErrorResponse(error=detail).model_dump())


def register_error_handlers(app: FastAPI) -> None:
    is_prod = settings.app_env == "production"

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return _json_error("HTTP_ERROR", str(exc.detail), exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        detail = ErrorDetail(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"errors": exc.errors()},
        )
        return JSONResponse(status_code=422, content=ErrorResponse(error=detail).model_dump())

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        log.error("unhandled_exception", path=request.url.path, error=str(exc))
        if is_prod:
            return _json_error("INTERNAL_ERROR", "An unexpected error occurred", 500)
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        detail = ErrorDetail(
            code="INTERNAL_ERROR",
            message=str(exc),
            details={"traceback": tb},
        )
        return JSONResponse(status_code=500, content=ErrorResponse(error=detail).model_dump())
