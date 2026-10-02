from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from models.daily_reward_claim import DailyRewardClaim

class DailyRewardRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def latest_for_user(self, discord_id: int):
        result = await self.session.execute(
            select(DailyRewardClaim)
            .where(DailyRewardClaim.recipient_discord_id == discord_id)
            .order_by(desc(DailyRewardClaim.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create(self, discord_id: int, streak_count: int, created_at=None):
        row = DailyRewardClaim(recipient_discord_id=discord_id, streak_count=streak_count)
        if created_at is not None:
            row.created_at = created_at
        self.session.add(row)
        await self.session.flush()
        await self.session.refresh(row)
        return row

