"""
Market Service — AwesomeAPI integration for currency quotes.

Reuses the RedisCache pattern from the existing backend.
"""

import httpx
import structlog

from app.cache.redis_cache import redis_cache
from app.config import settings

log = structlog.get_logger()

BASE_URL = "https://economia.awesomeapi.com.br"
CACHE_TTL = 10 * 60  # 10 minutes (without API key)
CACHE_TTL_WITH_KEY = 15 * 60  # 15 minutes (with API key)
STALE_TTL = 60 * 60  # 1 hour — serve stale data if API fails


class AwesomeAPIService:
    """Adapter for AwesomeAPI currency exchange rates."""

    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def connect(self):
        self._client = httpx.AsyncClient(base_url=BASE_URL, timeout=10.0)

    async def disconnect(self):
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("AwesomeAPIService not connected. Call connect() first.")
        return self._client

    @property
    def cache_ttl(self) -> int:
        return CACHE_TTL_WITH_KEY if settings.awesomeapi_key else CACHE_TTL

    async def _get(self, endpoint: str, params: dict | None = None) -> dict | list:
        try:
            resp = await self.client.get(endpoint, params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            log.error("AwesomeAPI error", status=e.response.status_code, body=e.response.text)
            raise
        except httpx.RequestError as e:
            log.error("AwesomeAPI network error", error=str(e))
            raise

    async def get_last_quotes(self, pairs: str = "USD-BRL,EUR-BRL") -> list[dict]:
        """Get current quotes for currency pairs.

        Args:
            pairs: Comma-separated currency pairs (e.g., "USD-BRL,EUR-BRL")
        """
        cache_key = f"market:last:{pairs}"
        stale_key = f"market:stale:{pairs}"
        cached = await redis_cache.get(cache_key)
        if cached is not None:
            log.info("Cache HIT — market quotes", pairs=pairs)
            return cached

        log.info("Fetching quotes from AwesomeAPI", pairs=pairs)
        try:
            data = await self._get(f"/json/last/{pairs}")
        except Exception as e:
            log.warning("AwesomeAPI failed, trying stale cache", error=str(e))
            stale = await redis_cache.get(stale_key)
            if stale is not None:
                log.info("Serving stale cached quotes", pairs=pairs)
                return stale
            raise

        quotes = []
        # AwesomeAPI returns {"USDBRL": {...}, "EURBRL": {...}}
        if isinstance(data, dict):
            for key, val in data.items():
                if isinstance(val, dict):
                    quotes.append({
                        "code": val.get("code", ""),
                        "codein": val.get("codein", ""),
                        "name": val.get("name", ""),
                        "bid": float(val.get("bid", 0)),
                        "ask": float(val.get("ask", 0)),
                        "varBid": float(val.get("varBid", 0)),
                        "pctChange": float(val.get("pctChange", 0)),
                        "high": float(val.get("high", 0)),
                        "low": float(val.get("low", 0)),
                        "timestamp": int(val.get("timestamp", 0)),
                    })

        await redis_cache.set(cache_key, quotes, ttl_seconds=self.cache_ttl)
        await redis_cache.set(stale_key, quotes, ttl_seconds=STALE_TTL)
        log.info("Quotes loaded", count=len(quotes))
        return quotes

    async def get_daily_history(self, moeda: str = "USD-BRL", dias: int = 30) -> list[dict]:
        """Get daily historical quotes for a currency pair.

        Args:
            moeda: Currency pair (e.g., "USD-BRL")
            dias: Number of days (max 360)
        """
        dias = min(dias, 360)
        cache_key = f"market:history:{moeda}:{dias}"
        cached = await redis_cache.get(cache_key)
        if cached is not None:
            log.info("Cache HIT — market history", moeda=moeda, dias=dias)
            return cached

        log.info("Fetching history from AwesomeAPI", moeda=moeda, dias=dias)
        data = await self._get(f"/json/daily/{moeda}/{dias}")

        history = []
        if isinstance(data, list):
            for item in data:
                history.append({
                    "timestamp": int(item.get("timestamp", 0)),
                    "bid": float(item.get("bid", 0)),
                    "ask": float(item.get("ask", 0)),
                })

        await redis_cache.set(cache_key, history, ttl_seconds=self.cache_ttl)
        log.info("History loaded", moeda=moeda, points=len(history))
        return history


awesomeapi_service = AwesomeAPIService()
