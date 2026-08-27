from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.company import Company
from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    def __init__(self, session: AsyncSession):
        super().__init__(Company, session)

    async def get_by_nome_case_insensitive(self, nome: str) -> Company | None:
        result = await self.session.execute(
            select(Company).where(func.lower(Company.nome) == nome.lower())
        )
        return result.scalar_one_or_none()

    async def create_company(
        self, nome: str, origem: str, deal_id: int | None = None
    ) -> Company:
        company = Company(nome=nome, origem=origem, deal_id=deal_id)
        return await self.create(company)
