from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_discord_id(self, discord_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.discord_id == discord_id))
        return result.scalar_one_or_none()

    async def get_by_discord_id_locked(self, discord_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.discord_id == discord_id).with_for_update())
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create(self, discord_id: int, username: str, balance: int = 1000) -> User:
        user = User(discord_id=discord_id, username=username, balance=balance)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
