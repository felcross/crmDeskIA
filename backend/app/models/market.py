from pydantic import BaseModel


class CurrencyQuote(BaseModel):
    code: str
    codein: str
    name: str
    bid: float
    ask: float
    varBid: float  # noqa: N815
    pctChange: float  # noqa: N815
    high: float
    low: float
    timestamp: int


class CurrencyQuoteResponse(BaseModel):
    quotes: list[CurrencyQuote]


class HistoryPoint(BaseModel):
    timestamp: int
    bid: float
    ask: float


class CurrencyHistoryResponse(BaseModel):
    moeda: str
    dias: int
    data: list[HistoryPoint]
