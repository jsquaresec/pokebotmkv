from sqlalchemy import select
from models.achievement import Achievement


class AchievementRepository:
    def __init__(self, session):
        self.session = session

    async def unlock(self, discord_id: int, code: str):
        row = (
            await self.session.execute(
                select(Achievement).where(Achievement.discord_id == discord_id, Achievement.code == code)
            )
        ).scalar_one_or_none()
        if row:
            return row, False
        row = Achievement(discord_id=discord_id, code=code)
        self.session.add(row)
        await self.session.flush()
        return row, True

    async def list_for(self, discord_id: int):
        return list(
            (await self.session.execute(select(Achievement).where(Achievement.discord_id == discord_id)))
            .scalars()
            .all()
        )
