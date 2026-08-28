import asyncio

import structlog
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.cache.redis_cache import redis_cache
from app.db.session import async_session

log = structlog.get_logger()

router = APIRouter()

TIMEOUT = 2.0


async def _check_redis() -> str:
    try:
        await asyncio.wait_for(redis_cache.client.ping(), timeout=TIMEOUT)
        return "ok"
    except Exception:
        return "fail"


async def _check_postgres() -> str:
    try:
        async with async_session() as session:
            await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=TIMEOUT)
        return "ok"
    except Exception:
        return "fail"


@router.get("/health")
async def health_check():
    redis, postgres = await asyncio.gather(
        _check_redis(),
        _check_postgres(),
    )

    services = {"redis": redis, "postgres": postgres}

    if all(v == "ok" for v in services.values()):
        status = "ok"
    elif all(v == "fail" for v in services.values()):
        status = "down"
    else:
        status = "degraded"

    code = 200 if status != "down" else 503

    log.info("health_check", status=status, **services)

    return JSONResponse(
        status_code=code,
        content={"status": status, "services": services},
    )
