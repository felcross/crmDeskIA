from fastapi import APIRouter, Query

from app.models.common import PaginationMeta, ResponseEnvelope
from app.models.dashboard import (
    DashboardChartsResponse,
    DealResponse,
    KPICardResponse,
    LeadResponse,
)
from app.services.analytics_service import (
    compute_kpis,
    contacts_by_month,
    deals_by_stage,
    sales_funnel,
    value_by_month,
)
from app.services.deal_service import deal_service
from app.repositories.lead_repo import LeadRepository
from app.dependencies import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/kpis")
async def get_kpis():
    deals = await deal_service.get_all_deals(limit=100)
    kpis = compute_kpis(deals)
    cards = [
        KPICardResponse(title="Total de Deals", value=kpis["total_deals"]),
        KPICardResponse(title="Valor do Pipeline", value=kpis["pipeline_value"]),
        KPICardResponse(title="Ticket Médio", value=kpis["average_ticket"]),
        KPICardResponse(title="Deals Fechados", value=kpis["closed_deals"]),
    ]
    return ResponseEnvelope(data=cards)


@router.get("/charts", response_model=ResponseEnvelope[DashboardChartsResponse])
async def get_charts():
    deals = await deal_service.get_all_deals(limit=100)

    # Get leads from Postgres
    async for session in get_db():
        lead_repo = LeadRepository(session)
        contacts = await lead_repo.get_all_as_dicts(limit=100)
        break

    return ResponseEnvelope(
        data=DashboardChartsResponse(
            deals_by_stage=deals_by_stage(deals),
            sales_funnel=sales_funnel(deals),
            value_by_month=value_by_month(deals),
            contacts_by_month=contacts_by_month(contacts),
        )
    )


@router.get("/deals")
async def get_deals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("criado_em", pattern="^(nome|valor|estagio|criado_em|created_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    stage: str | None = Query(None),
):
    all_deals = await deal_service.get_all_deals(limit=100)

    # Filter
    if stage:
        all_deals = [d for d in all_deals if d["estagio"] == stage]

    # Mapeia created_at para a chave interna criado_em
    sort_key = "criado_em" if sort_by == "created_at" else sort_by

    # Sort
    reverse = sort_order == "desc"
    all_deals.sort(key=lambda d: d.get(sort_key, ""), reverse=reverse)

    # Paginate
    total = len(all_deals)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    end = start + page_size
    page_deals = all_deals[start:end]

    return ResponseEnvelope(
        data=[DealResponse(**d) for d in page_deals],
        meta=PaginationMeta(
            total=total, page=page, page_size=page_size, total_pages=total_pages
        ).model_dump(),
    )


@router.get("/leads")
async def get_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("criado_em", pattern="^(nome|email|status_lead|criado_em|created_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    status: str | None = Query(None),
):
    # Get leads from Postgres
    async for session in get_db():
        lead_repo = LeadRepository(session)
        all_leads = await lead_repo.get_all_as_dicts(limit=1000)
        break

    # Filter
    if status:
        all_leads = [c for c in all_leads if c["status_lead"] == status]

    # Mapeia created_at para a chave interna criado_em
    sort_key = "criado_em" if sort_by == "created_at" else sort_by

    # Sort
    reverse = sort_order == "desc"
    all_leads.sort(key=lambda c: c.get(sort_key, ""), reverse=reverse)

    # Paginate
    total = len(all_leads)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    end = start + page_size
    page_leads = all_leads[start:end]

    return ResponseEnvelope(
        data=[LeadResponse(**c) for c in page_leads],
        meta=PaginationMeta(
            total=total, page=page, page_size=page_size, total_pages=total_pages
        ).model_dump(),
    )
