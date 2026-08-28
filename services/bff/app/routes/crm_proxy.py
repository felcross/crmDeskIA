import httpx
import structlog
from fastapi import APIRouter, Request, Response

from app.config import settings

log = structlog.get_logger()
router = APIRouter(tags=["crm-proxy"])

# Paths that should NOT be proxied to CRM (handled by BFF itself)
_BFF_OWN_PATHS = {"/health"}


@router.api_route(
    "/crm/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
)
async def proxy_crm(request: Request, path: str) -> Response:
    """Proxy all /api/v1/crm/* requests to the CRM backend.

    The CRM backend expects paths without the /crm prefix,
    so /api/v1/crm/dashboard/kpis → http://crm-backend:8000/api/v1/dashboard/kpis
    """
    target_url = f"{settings.crm_backend_url}/api/v1/{path}"
    if request.url.query:
        target_url += f"?{request.url.query}"

    headers = dict(request.headers)
    headers.pop("host", None)

    body = await request.body()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
            )
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=dict(resp.headers),
            )
        except httpx.ConnectError:
            log.error("crm_backend_unreachable", url=target_url)
            return Response(
                content=b'{"detail":"CRM backend unreachable"}',
                status_code=502,
                media_type="application/json",
            )


# Default route: /api/v1/{path} → CRM backend (backward compatibility)
# This ensures existing frontend calls like /api/v1/dashboard/kpis still work
@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
)
async def proxy_crm_default(request: Request, path: str) -> Response:
    """Proxy all other /api/v1/* requests to CRM backend (backward compat)."""
    if path in {p.lstrip("/") for p in _BFF_OWN_PATHS}:
        return Response(status_code=404)

    target_url = f"{settings.crm_backend_url}/api/v1/{path}"
    if request.url.query:
        target_url += f"?{request.url.query}"

    headers = dict(request.headers)
    headers.pop("host", None)

    body = await request.body()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
            )
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=dict(resp.headers),
            )
        except httpx.ConnectError:
            log.error("crm_backend_unreachable", url=target_url)
            return Response(
                content=b'{"detail":"CRM backend unreachable"}',
                status_code=502,
                media_type="application/json",
            )
