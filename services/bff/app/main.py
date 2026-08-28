import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes.crm_proxy import router as crm_router
from app.routes.dashboard import router as dashboard_router
from app.routes.ecom_proxy import router as ecom_router
from app.routes.health import router as health_router

log = structlog.get_logger()

app = FastAPI(
    title="CRM AI — BFF",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(ecom_router, prefix="/api/v1")
app.include_router(crm_router, prefix="/api/v1")  # catch-all CRM — must be last


@app.on_event("startup")
async def startup():
    log.info("BFF starting", env=settings.app_env, crm=settings.crm_backend_url, ecom=settings.ecommerce_backend_url)
