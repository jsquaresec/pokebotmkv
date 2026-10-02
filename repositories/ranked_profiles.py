from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from models.ranked_profile import RankedProfile

class RankedProfileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_owner(self, owner_id: int) -> RankedProfile | None:
        result = await self.session.execute(select(RankedProfile).where(RankedProfile.owner_id == owner_id))
        return result.scalar_one_or_none()

    async def create(self, owner_id: int, rating: int) -> RankedProfile:
        profile = RankedProfile(owner_id=owner_id, rating=rating)
        self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def top_profiles(self, limit: int = 10) -> list[RankedProfile]:
        result = await self.session.execute(select(RankedProfile).order_by(desc(RankedProfile.rating)).limit(limit))
        return list(result.scalars().all())
