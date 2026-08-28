from pydantic import BaseModel


class KPICardResponse(BaseModel):
    title: str
    value: float


class KPIResponse(BaseModel):
    total_deals: int
    pipeline_value: float
    average_ticket: float
    closed_deals: int


class ChartDataPoint(BaseModel):
    label: str
    value: float


class ChartResponse(BaseModel):
    chart_type: str
    title: str
    data: list[ChartDataPoint]


class DealResponse(BaseModel):
    id: str
    nome: str
    valor: float
    estagio: str
    pipeline: str
    data_close: str | None = ""
    criado_em: str


class LeadResponse(BaseModel):
    id: str
    nome: str
    email: str | None = ""
    telefone: str | None = ""
    status_lead: str | None = ""
    criado_em: str


class DashboardChartsResponse(BaseModel):
    deals_by_stage: ChartResponse
    sales_funnel: ChartResponse
    value_by_month: ChartResponse
    contacts_by_month: ChartResponse
