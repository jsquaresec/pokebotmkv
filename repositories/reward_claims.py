from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from models.reward_claim import RewardClaim

class RewardClaimRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, recipient_discord_id: int, reward_type: str, amount: int, related_battle_id: int | None, details_json: str) -> RewardClaim:
        row = RewardClaim(
            recipient_discord_id=recipient_discord_id,
            reward_type=reward_type,
            amount=amount,
            related_battle_id=related_battle_id,
            details_json=details_json,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def latest(self, limit: int = 50) -> list[RewardClaim]:
        result = await self.session.execute(select(RewardClaim).order_by(desc(RewardClaim.created_at)).limit(limit))
        return list(result.scalars().all())
