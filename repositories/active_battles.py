from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from models.active_battle import ActiveBattle

class ActiveBattleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, battle_type: str, p1: int, p2: int, state_json: str) -> ActiveBattle:
        battle = ActiveBattle(
            battle_type=battle_type,
            player_one_discord_id=p1,
            player_two_discord_id=p2,
            state_json=state_json,
            finished=False,
        )
        self.session.add(battle)
        await self.session.commit()
        await self.session.refresh(battle)
        return battle

    async def get_for_user(self, discord_id: int) -> ActiveBattle | None:
        result = await self.session.execute(
            select(ActiveBattle).where(
                or_(
                    ActiveBattle.player_one_discord_id == discord_id,
                    ActiveBattle.player_two_discord_id == discord_id,
                ),
                ActiveBattle.finished.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, battle_id: int) -> ActiveBattle | None:
        result = await self.session.execute(select(ActiveBattle).where(ActiveBattle.id == battle_id))
        return result.scalar_one_or_none()

    async def save(self, battle: ActiveBattle, state_json: str, finished: bool) -> ActiveBattle:
        battle.state_json = state_json
        battle.finished = finished
        await self.session.commit()
        await self.session.refresh(battle)
        return battle
