from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.quest_progress import QuestProgress

class QuestRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, discord_id: int, quest_code: str, target_value: int):
        result = await self.session.execute(
            select(QuestProgress).where(QuestProgress.recipient_discord_id == discord_id, QuestProgress.quest_code == quest_code)
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = QuestProgress(recipient_discord_id=discord_id, quest_code=quest_code, target_value=target_value, progress_value=0, status="active")
            self.session.add(row)
            await self.session.commit()
            await self.session.refresh(row)
        return row

    async def list_for_user(self, discord_id: int):
        result = await self.session.execute(select(QuestProgress).where(QuestProgress.recipient_discord_id == discord_id))
        return list(result.scalars().all())

    async def save(self, row):
        await self.session.commit()
        await self.session.refresh(row)
        return row
