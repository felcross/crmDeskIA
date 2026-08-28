from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ResponseEnvelope[T](BaseModel):
    data: T
    error: None = None
    meta: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    data: None = None
    error: ErrorDetail
    meta: dict[str, Any] | None = None


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
