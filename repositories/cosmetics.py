from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.cosmetic import Cosmetic

class CosmeticRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_active(self) -> list[Cosmetic]:
        result = await self.session.execute(select(Cosmetic).where(Cosmetic.is_active.is_(True)))
        return list(result.scalars().all())
