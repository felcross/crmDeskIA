import httpx
import structlog
from fastapi import APIRouter, Request, Response

from app.config import settings
from app.proxy_utils import build_proxy_response

log = structlog.get_logger()
router = APIRouter(tags=["crm-proxy"])

_BFF_OWN_PATHS = {"/health"}


@router.api_route(
    "/crm/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
)
async def proxy_crm(request: Request, path: str) -> Response:
    """Proxy all /api/v1/crm/* requests to the CRM backend."""
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
            return build_proxy_response(resp)
        except httpx.ConnectError:
            log.error("crm_backend_unreachable", url=target_url)
            return Response(
                content=b'{"detail":"CRM backend unreachable"}',
                status_code=502,
                media_type="application/json",
            )


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
            return build_proxy_response(resp)
        except httpx.ConnectError:
            log.error("crm_backend_unreachable", url=target_url)
            return Response(
                content=b'{"detail":"CRM backend unreachable"}',
                status_code=502,
                media_type="application/json",
            )