"""
Analytics Service — Chart data computation.

Ported from analytics.py, adapted for async + structured output.
"""

import pandas as pd
import structlog

from app.models.dashboard import ChartDataPoint, ChartResponse

log = structlog.get_logger()

# Color palette (matches current Streamlit app)
COLORS = {
    "indigo": "#6366f1",
    "cyan": "#22d3ee",
    "emerald": "#34d399",
    "amber": "#fbbf24",
    "rose": "#fb7185",
    "violet": "#a78bfa",
    "sky": "#38bdf8",
    "orange": "#fb923c",
}


def deals_by_stage(deals: list[dict]) -> ChartResponse:
    if not deals:
        return ChartResponse(chart_type="bar", title="Deals por Estágio", data=[])

    df = pd.DataFrame(deals)
    counts = df["estagio"].value_counts()

    return ChartResponse(
        chart_type="bar",
        title="Deals por Estágio",
        data=[ChartDataPoint(label=str(k), value=float(v)) for k, v in counts.items()],
    )


def sales_funnel(deals: list[dict]) -> ChartResponse:
    if not deals:
        return ChartResponse(chart_type="funnel", title="Funil de Vendas", data=[])

    df = pd.DataFrame(deals)
    stage_order = [
        "appointmentscheduled", "qualifiedtobuy", "presentationscheduled",
        "decisionmakerbought", "closedwon", "closedlost",
    ]
    counts = df["estagio"].value_counts()

    ordered = []
    for stage in stage_order:
        if stage in counts:
            ordered.append(ChartDataPoint(label=stage, value=float(counts[stage])))

    return ChartResponse(chart_type="funnel", title="Funil de Vendas", data=ordered)


def value_by_month(deals: list[dict]) -> ChartResponse:
    if not deals:
        return ChartResponse(chart_type="line", title="Valor por Mês", data=[])

    df = pd.DataFrame(deals)
    df["criado_em"] = pd.to_datetime(df["criado_em"], errors="coerce")
    df = df.dropna(subset=["criado_em"])
    df["mes"] = df["criado_em"].dt.tz_localize(None).dt.to_period("M").astype(str)

    monthly = df.groupby("mes")["valor"].sum().sort_index()

    return ChartResponse(
        chart_type="line",
        title="Valor por Mês",
        data=[ChartDataPoint(label=str(k), value=float(v)) for k, v in monthly.items()],
    )


def contacts_by_month(contacts: list[dict]) -> ChartResponse:
    if not contacts:
        return ChartResponse(chart_type="bar", title="Contatos por Mês", data=[])

    df = pd.DataFrame(contacts)
    df["criado_em"] = pd.to_datetime(df["criado_em"], errors="coerce")
    df = df.dropna(subset=["criado_em"])
    df["mes"] = df["criado_em"].dt.tz_localize(None).dt.to_period("M").astype(str)

    monthly = df.groupby("mes").size().sort_index()

    return ChartResponse(
        chart_type="bar",
        title="Contatos por Mês",
        data=[ChartDataPoint(label=str(k), value=float(v)) for k, v in monthly.items()],
    )


def compute_kpis(deals: list[dict]) -> dict:
    if not deals:
        return {"total_deals": 0, "pipeline_value": 0.0, "average_ticket": 0.0, "closed_deals": 0}

    df = pd.DataFrame(deals)
    total = len(df)
    pipeline = float(df["valor"].sum())
    avg = float(df["valor"].mean()) if total > 0 else 0.0
    closed = int(len(df[df["estagio"] == "closedwon"]))

    return {
        "total_deals": total,
        "pipeline_value": pipeline,
        "average_ticket": avg,
        "closed_deals": closed,
    }
