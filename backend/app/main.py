import time

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.api.v1.router import api_v1_router
from app.config import settings
from app.middleware.csrf import CSRFMiddleware
from app.middleware.error_handler import register_error_handlers
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit import register_rate_limiting
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.observability import init_sentry, metrics

log = structlog.get_logger()

app = FastAPI(
    title="CRM AI Portal",
    version="2.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# --- Middleware (executed in reverse order of addition) ---

# Security headers (outermost after CORS)
app.add_middleware(SecurityHeadersMiddleware)

# CSRF — configurable; skip when behind Cloudflare WAF
if settings.app_env != "cloudflare":
    app.add_middleware(
        CSRFMiddleware,
        secret_key=settings.secret_key,
        secure=settings.app_env == "production",
    )

# Request logging
app.add_middleware(RequestLoggingMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Rate limiting ---
register_rate_limiting(app)

# --- Global exception handlers ---
register_error_handlers(app)

# --- Routes ---
app.include_router(api_v1_router, prefix="/api/v1")


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    metrics.inc_active()
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    except Exception:
        raise
    finally:
        metrics.inc_request(request.method, request.url.path, status)
        metrics.observe_duration(time.perf_counter() - start)
        metrics.dec_active()


@app.get("/metrics", include_in_schema=False)
async def prometheus_metrics():
    return PlainTextResponse(metrics.render(), media_type="text/plain; charset=utf-8")


@app.on_event("startup")
async def startup():
    from app.cache.redis_cache import redis_cache
    from app.services.market_service import awesomeapi_service

    init_sentry()

    log.info("Starting CRM AI Portal", env=settings.app_env)
    await redis_cache.connect()
    await awesomeapi_service.connect()


@app.on_event("shutdown")
async def shutdown():
    from app.cache.redis_cache import redis_cache
    from app.services.market_service import awesomeapi_service

    await awesomeapi_service.disconnect()
    await redis_cache.disconnect()
    log.info("Shutting down CRM AI Portal")
