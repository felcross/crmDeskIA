from fastapi import APIRouter, Query

from app.models.common import ResponseEnvelope
from app.models.market import CurrencyHistoryResponse, CurrencyQuoteResponse, HistoryPoint
from app.services.market_service import awesomeapi_service

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/quotes", response_model=ResponseEnvelope[CurrencyQuoteResponse])
async def get_quotes(
    pairs: str = Query("USD-BRL,EUR-BRL", description="Comma-separated currency pairs"),
):
    """Get current currency quotes."""
    quotes = await awesomeapi_service.get_last_quotes(pairs=pairs)
    return ResponseEnvelope(data=CurrencyQuoteResponse(quotes=quotes))


@router.get("/history/{moeda}", response_model=ResponseEnvelope[CurrencyHistoryResponse])
async def get_history(
    moeda: str,
    dias: int = Query(30, ge=1, le=360, description="Number of days (max 360)"),
):
    """Get daily historical quotes for a currency pair."""
    data = await awesomeapi_service.get_daily_history(moeda=moeda, dias=dias)
    return ResponseEnvelope(
        data=CurrencyHistoryResponse(
            moeda=moeda,
            dias=dias,
            data=[HistoryPoint(**p) for p in data],
        )
    )
