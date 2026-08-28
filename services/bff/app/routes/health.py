import httpx
import structlog
from fastapi import APIRouter

from app.config import settings

log = structlog.get_logger()
router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    services = {}

    # Check CRM backend
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.crm_backend_url}/api/v1/health")
            services["crm"] = "ok" if resp.status_code == 200 else f"error ({resp.status_code})"
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        log.warning("crm_health_failed", error=str(e))
        services["crm"] = "unreachable"

    # Check E-commerce backend
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ecommerce_backend_url}/api/v1/health")
            services["ecommerce"] = "ok" if resp.status_code == 200 else f"error ({resp.status_code})"
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        log.warning("ecom_health_failed", error=str(e))
        services["ecommerce"] = "unreachable"

    all_ok = all(v == "ok" for v in services.values())
    return {"status": "ok" if all_ok else "degraded", "services": services}
