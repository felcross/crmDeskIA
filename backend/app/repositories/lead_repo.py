from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.lead import Lead
from app.repositories.base import BaseRepository


class LeadRepository(BaseRepository[Lead]):
    def __init__(self, session: AsyncSession):
        super().__init__(Lead, session)

    async def create_lead(
        self,
        nome: str,
        email: str | None = None,
        telefone: str | None = None,
        status_lead: str | None = None,
    ) -> Lead:
        lead = Lead(
            nome=nome,
            email=email,
            telefone=telefone,
            status_lead=status_lead,
        )
        return await self.create(lead)

    async def get_all_as_dicts(self, limit: int = 100) -> list[dict]:
        """Return leads as dicts compatible with dashboard response format."""
        result = await self.session.execute(
            select(Lead).order_by(Lead.criado_em.desc()).limit(limit)
        )
        leads = result.scalars().all()
        return [
            {
                "id": str(lead.id),
                "nome": lead.nome,
                "email": lead.email or "",
                "telefone": lead.telefone or "",
                "status_lead": lead.status_lead or "",
                "criado_em": str(lead.criado_em),
            }
            for lead in leads
        ]
