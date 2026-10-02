from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.live_event import LiveEvent

class LiveEventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_active(self) -> list[LiveEvent]:
        result = await self.session.execute(select(LiveEvent).where(LiveEvent.is_active.is_(True)))
        return list(result.scalars().all())
