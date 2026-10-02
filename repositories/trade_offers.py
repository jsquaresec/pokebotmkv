from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from models.trade_offer import TradeOffer

class TradeOfferRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, from_discord_id: int, to_discord_id: int, offered_json: str, requested_json: str, status: str = "open"):
        row = TradeOffer(
            from_discord_id=from_discord_id,
            to_discord_id=to_discord_id,
            offered_json=offered_json,
            requested_json=requested_json,
            status=status,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def latest(self, limit: int = 50):
        result = await self.session.execute(select(TradeOffer).order_by(desc(TradeOffer.created_at)).limit(limit))
        return list(result.scalars().all())

    async def get(self, offer_id: int, lock: bool = False):
        stmt = select(TradeOffer).where(TradeOffer.id == offer_id)
        if lock:
            stmt = stmt.with_for_update()
        return (await self.session.execute(stmt)).scalar_one_or_none()
