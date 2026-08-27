"""
Reports API — PDF generation endpoints.
"""

import io
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.middleware.rate_limit import limiter
from app.services.report_service import generate_dashboard_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate")
@limiter.limit("5/minute")
async def generate_report(request: Request):
    """Generate a dashboard PDF report and return it as a file download."""
    pdf_bytes = await generate_dashboard_pdf()

    filename = f"crm-dashboard-{datetime.now().strftime('%Y%m%d-%H%M%S')}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )
