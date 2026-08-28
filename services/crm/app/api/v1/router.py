from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.csv_analysis import router as csv_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.health import router as health_router
from app.api.v1.leads import router as leads_router
from app.api.v1.market import router as market_router
from app.api.v1.reports import router as reports_router
from app.api.v1.tickets import router as tickets_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(health_router, tags=["health"])
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(leads_router)
api_v1_router.include_router(tickets_router)
api_v1_router.include_router(market_router)
api_v1_router.include_router(reports_router)
api_v1_router.include_router(csv_router)
