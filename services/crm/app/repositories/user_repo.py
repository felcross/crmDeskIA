from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.user import User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> User | None:
        result = await self.session.execute(select(User).where(User.google_id == google_id))
        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        name: str,
        google_id: str | None = None,
        role: UserRole = UserRole.ADMIN,
        avatar_url: str | None = None,
    ) -> User:
        user = User(email=email, name=name, google_id=google_id, role=role, avatar_url=avatar_url)
        return await self.create(user)
