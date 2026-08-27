from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.deal import Deal
from app.repositories.base import BaseRepository


class DealRepository(BaseRepository[Deal]):
    def __init__(self, session: AsyncSession):
        super().__init__(Deal, session)

    async def get_by_lead_id(self, lead_id: int) -> Deal | None:
        result = await self.session.execute(select(Deal).where(Deal.lead_id == lead_id))
        return result.scalar_one_or_none()

    async def create_deal(
        self,
        nome: str,
        valor: float = 0.0,
        estagio: str = "",
        pipeline: str = "",
        data_close: datetime | None = None,
        lead_id: int | None = None,
    ) -> Deal:
        deal = Deal(
            nome=nome,
            valor=valor,
            estagio=estagio,
            pipeline=pipeline,
            data_close=data_close,
            lead_id=lead_id,
        )
        return await self.create(deal)

    async def get_all_as_dicts(self, limit: int = 100) -> list[dict]:
        """Return deals as dicts compatible with analytics_service functions."""
        result = await self.session.execute(
            select(Deal).order_by(Deal.criado_em.desc()).limit(limit)
        )
        deals = result.scalars().all()
        return [
            {
                "id": str(d.id),
                "nome": d.nome,
                "valor": d.valor,
                "estagio": d.estagio,
                "pipeline": d.pipeline,
                "data_close": str(d.data_close) if d.data_close else "",
                "criado_em": str(d.criado_em),
            }
            for d in deals
        ]
