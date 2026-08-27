from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.ticket import Ticket
from app.repositories.base import BaseRepository


class TicketRepository(BaseRepository[Ticket]):
    def __init__(self, session: AsyncSession):
        super().__init__(Ticket, session)

    async def create_ticket(
        self,
        nome: str,
        email: str,
        descricao: str,
        prioridade: str = "media",
        cargo: str = "",
        company_id: int | None = None,
    ) -> Ticket:
        ticket = Ticket(
            nome=nome,
            email=email,
            descricao=descricao,
            prioridade=prioridade,
            cargo=cargo,
            company_id=company_id,
        )
        return await self.create(ticket)
