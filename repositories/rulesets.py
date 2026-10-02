from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.ruleset import Ruleset

class RulesetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self) -> list[Ruleset]:
        result = await self.session.execute(select(Ruleset))
        return list(result.scalars().all())
