"""
CSV Analysis API — upload CSV and receive AI-powered analysis suggestions.
"""

from fastapi import APIRouter, Request, UploadFile, File, HTTPException

from app.middleware.rate_limit import limiter
from app.services.csv_service import analyze_and_suggest

router = APIRouter(prefix="/reports", tags=["reports", "csv-analysis"])


@router.post("/csv-upload")
@limiter.limit("5/minute")
async def csv_upload(request: Request, file: UploadFile = File(...)):
    """Upload a CSV file and receive AI-generated analysis suggestions with chart configs.

    Returns:
        - suggestions: list of analysis suggestion strings
        - charts: list of chart configuration dicts (type, labels, data, axes)
        - summary: text summary of the dataset
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        result = analyze_and_suggest(content)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to analyze CSV: {e!s}")

    return result
