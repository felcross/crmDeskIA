from pydantic import BaseModel


class ReportRequest(BaseModel):
    report_type: str = "dashboard"
    date_range: str = "30d"


class ReportResponse(BaseModel):
    filename: str
    content_type: str = "application/pdf"
    size_bytes: int


class CSVAnalysisRequest(BaseModel):
    filename: str


class CSVAnalysisResponse(BaseModel):
    suggestions: list[str]
    charts: list[dict]
    summary: str
