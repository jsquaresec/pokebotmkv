import json
from repositories.battle_replays import BattleReplayRepository

class ReplayService:
    def __init__(self, repo: BattleReplayRepository):
        self.repo = repo

    async def save_replay(self, battle_id: int, battle_type: str, state: dict):
        payload = {
            "battle_id": battle_id,
            "battle_type": battle_type,
            "winner_discord_id": state.get("winner_discord_id"),
            "turn": state.get("turn"),
            "log": state.get("log", []),
        }
        return await self.repo.create(battle_id, battle_type, json.dumps(payload))
