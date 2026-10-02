from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.wild_encounter import WildEncounter


class WildEncounterRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def active_in_channel(self, channel_id: int, lock: bool = False):
        stmt = select(WildEncounter).where(
            WildEncounter.channel_id == channel_id,
            WildEncounter.status == "open",
            WildEncounter.expires_at > datetime.utcnow(),
        ).order_by(WildEncounter.id.desc()).limit(1)
        if lock:
            stmt = stmt.with_for_update()
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create(self, **values):
        encounter = WildEncounter(**values)
        self.session.add(encounter)
        await self.session.flush()
        return encounter

    async def expire_old(self) -> int:
        rows = (await self.session.execute(select(WildEncounter).where(
            WildEncounter.status == "open", WildEncounter.expires_at <= datetime.utcnow()
        ).with_for_update())).scalars().all()
        from services.wild_battle_service import WildBattleService
        await WildBattleService.expire(self.session)
        return len(rows)
