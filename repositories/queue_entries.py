from sqlalchemy import asc, select
from sqlalchemy.ext.asyncio import AsyncSession
from models.queue_entry import QueueEntry

class QueueEntryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_discord_id(self, discord_id: int) -> QueueEntry | None:
        result = await self.session.execute(select(QueueEntry).where(QueueEntry.discord_id == discord_id))
        return result.scalar_one_or_none()

    async def enqueue(self, discord_id: int, rating: int) -> QueueEntry:
        row = QueueEntry(discord_id=discord_id, rating=rating)
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def list_entries(self) -> list[QueueEntry]:
        result = await self.session.execute(select(QueueEntry).order_by(asc(QueueEntry.created_at)))
        return list(result.scalars().all())

    async def delete(self, entry: QueueEntry) -> None:
        await self.session.delete(entry)
        await self.session.commit()
