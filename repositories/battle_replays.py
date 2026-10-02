from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.battle_replay import BattleReplay

class BattleReplayRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, battle_id: int, battle_type: str, replay_json: str) -> BattleReplay:
        replay = BattleReplay(battle_id=battle_id, battle_type=battle_type, replay_json=replay_json)
        self.session.add(replay)
        await self.session.commit()
        await self.session.refresh(replay)
        return replay

    async def get_by_battle_id(self, battle_id: int) -> BattleReplay | None:
        result = await self.session.execute(select(BattleReplay).where(BattleReplay.battle_id == battle_id))
        return result.scalar_one_or_none()
