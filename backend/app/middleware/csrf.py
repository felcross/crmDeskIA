import secrets

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.models.common import ErrorResponse, ErrorDetail

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "x-csrf-token"

# Paths exempt from CSRF (OAuth callback — Google can't send CSRF token)
_CSRF_EXEMPT_PATHS = ("/api/v1/auth/callback",)


class CSRFMiddleware(BaseHTTPMiddleware):
    """Double-submit cookie CSRF protection.

    - GET/OPTIONS/HEAD: sets a random csrf_token cookie.
    - POST/PUT/DELETE/PATCH: validates X-CSRF-Token header matches cookie.
    - Requests with a valid Authorization: Bearer header are exempt.
    """

    def __init__(
        self,
        app,
        secret_key: str,
        secure: bool = False,
        exempt_prefixes: tuple[str, ...] = _CSRF_EXEMPT_PATHS,
    ):
        super().__init__(app)
        self.secret_key = secret_key
        self.secure = secure
        self.exempt_prefixes = exempt_prefixes

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Exempt bearer-token endpoints
        if any(request.url.path.startswith(p) for p in self.exempt_prefixes):
            return await call_next(request)

        # Exempt requests that carry a Bearer token
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            return await call_next(request)

        safe_method = request.method in ("GET", "HEAD", "OPTIONS", "TRACE")

        if safe_method:
            response = await call_next(request)
            if not request.cookies.get(CSRF_COOKIE_NAME):
                token = secrets.token_hex(32)
                response.set_cookie(
                    key=CSRF_COOKIE_NAME,
                    value=token,
                    httponly=False,
                    secure=self.secure,
                    samesite="lax",
                    max_age=3600,
                )
            return response

        # State-changing method — validate
        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        header_token = request.headers.get(CSRF_HEADER_NAME)

        if not cookie_token or not header_token or cookie_token != header_token:
            detail = ErrorDetail(code="CSRF_ERROR", message="CSRF token missing or mismatched")
            return JSONResponse(
                status_code=403,
                content=ErrorResponse(error=detail).model_dump(),
            )

        return await call_next(request)
