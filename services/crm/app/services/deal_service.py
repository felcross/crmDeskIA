"""
Deal Service — CRUD operations for deals.
"""

import structlog

from app.dependencies import get_db
from app.repositories.deal_repo import DealRepository

log = structlog.get_logger()


class DealService:
    """Manages deal CRUD operations against Postgres."""

    async def get_all_deals(self, limit: int = 100) -> list[dict]:
        """Get all deals as dicts (compatible with analytics_service)."""
        async for session in get_db():
            repo = DealRepository(session)
            return await repo.get_all_as_dicts(limit=limit)
        return []

    async def create_deal(
        self,
        nome: str,
        valor: float = 0.0,
        estagio: str = "",
        pipeline: str = "",
        data_close=None,
        lead_id: int | None = None,
    ) -> dict:
        """Create a new deal."""
        async for session in get_db():
            repo = DealRepository(session)
            deal = await repo.create_deal(
                nome=nome,
                valor=valor,
                estagio=estagio,
                pipeline=pipeline,
                data_close=data_close,
                lead_id=lead_id,
            )
            await session.commit()
            return {
                "id": str(deal.id),
                "nome": deal.nome,
                "valor": deal.valor,
                "estagio": deal.estagio,
                "pipeline": deal.pipeline,
                "data_close": str(deal.data_close) if deal.data_close else "",
                "criado_em": str(deal.criado_em),
            }
        return {}


deal_service = DealService()
