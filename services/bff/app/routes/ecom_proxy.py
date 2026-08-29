import httpx
import structlog
from fastapi import APIRouter, Request, Response

from app.config import settings
from app.proxy_utils import build_proxy_response

log = structlog.get_logger()
router = APIRouter(tags=["ecommerce-proxy"])


@router.api_route(
    "/ecommerce/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
)
async def proxy_ecommerce(request: Request, path: str) -> Response:
    """Proxy all /api/v1/ecommerce/* requests to the E-commerce backend."""
    target_url = f"{settings.ecommerce_backend_url}/api/v1/{path}"
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
            log.error("ecommerce_backend_unreachable", url=target_url)
            return Response(
                content=b'{"detail":"E-commerce backend unreachable"}',
                status_code=502,
                media_type="application/json",
            )