"""
Report Service — PDF generation using Jinja2 + WeasyPrint.
"""

from datetime import datetime
from pathlib import Path

import structlog
from jinja2 import Environment, FileSystemLoader

from app.dependencies import get_db
from app.repositories.lead_repo import LeadRepository
from app.services.analytics_service import (
    compute_kpis,
    contacts_by_month,
    deals_by_stage,
    sales_funnel,
    value_by_month,
)
from app.services.deal_service import deal_service

log = structlog.get_logger()

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


async def generate_dashboard_pdf() -> bytes:
    """Generate a PDF report of the current dashboard data."""
    deals = await deal_service.get_all_deals(limit=200)

    # Get leads from Postgres
    async for session in get_db():
        lead_repo = LeadRepository(session)
        contacts = await lead_repo.get_all_as_dicts(limit=200)
        break

    kpis = compute_kpis(deals)
    charts = {
        "deals_by_stage": deals_by_stage(deals),
        "sales_funnel": sales_funnel(deals),
        "value_by_month": value_by_month(deals),
        "contacts_by_month": contacts_by_month(contacts),
    }

    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("dashboard_report.html")
    html_content = template.render(
        kpis=kpis,
        charts=charts,
        deals=deals[:50],
        contacts=contacts[:50],
        generated_at=generated_at,
    )

    from weasyprint import HTML

    pdf_bytes = HTML(string=html_content).write_pdf()
    log.info("PDF generated", size_bytes=len(pdf_bytes))
    return pdf_bytes
