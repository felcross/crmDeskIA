import structlog
from fastapi import FastAPI

from app.api.v1.router import api_v1_router

log = structlog.get_logger()

app = FastAPI(
    title="E-commerce Service",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.include_router(api_v1_router)


@app.on_event("startup")
async def startup():
    log.info("E-commerce service starting")
