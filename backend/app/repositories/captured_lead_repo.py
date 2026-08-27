from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.captured_lead import CapturedLead
from app.repositories.base import BaseRepository


class CapturedLeadRepository(BaseRepository[CapturedLead]):
    def __init__(self, session: AsyncSession):
        super().__init__(CapturedLead, session)

    async def create_lead(
        self,
        nome: str,
        email: str,
        telefone: str = "",
        interesse: str = "",
        hubspot_contact_id: str | None = None,
        captured_by_user_id: int | None = None,
    ) -> CapturedLead:
        lead = CapturedLead(
            nome=nome,
            email=email,
            telefone=telefone,
            interesse=interesse,
            hubspot_contact_id=hubspot_contact_id,
            captured_by_user_id=captured_by_user_id,
        )
        return await self.create(lead)
