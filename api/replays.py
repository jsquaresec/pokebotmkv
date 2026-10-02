import json
from fastapi import APIRouter, HTTPException
from core.database import SessionLocal
from repositories.battle_replays import BattleReplayRepository

router = APIRouter(prefix="/replays", tags=["replays"])

@router.get("/{battle_id}")
async def replay_summary(battle_id: int):
    async with SessionLocal() as session:
        repo = BattleReplayRepository(session)
        replay = await repo.get_by_battle_id(battle_id)
        if replay is None:
            raise HTTPException(status_code=404, detail="Replay not found")
        return json.loads(replay.replay_json)
