import json
from repositories.active_battles import ActiveBattleRepository
from battle.engine import TurnEngine
from battle.party_builder import build_team_state

class BattleService:
    def __init__(self, repo: ActiveBattleRepository):
        self.repo = repo
        self.engine = TurnEngine()

    def _build_state(self, p1_id: int, p2_id: int, p1_team: list, p2_team: list) -> dict:
        if not isinstance(p1_team, (list, tuple)):
            p1_team = [p1_team]
        if not isinstance(p2_team, (list, tuple)):
            p2_team = [p2_team]
        p1_state = build_team_state(p1_team)
        p2_state = build_team_state(p2_team)
        p1_state["discord_id"] = p1_id
        p2_state["discord_id"] = p2_id
        p1_state["requires_replacement"] = False
        p2_state["requires_replacement"] = False
        p1_state["active"]["discord_id"] = p1_id
        p2_state["active"]["discord_id"] = p2_id
        for side, owner in ((p1_state, p1_id), (p2_state, p2_id)):
            for mon in side["bench"]:
                mon["discord_id"] = owner

        return {
            "turn": 1,
            "finished": False,
            "winner_discord_id": None,
            "pending_action_p1": None,
            "pending_action_p2": None,
            "player_one": p1_state,
            "player_two": p2_state,
            "log": [],
        }

    async def create_ranked_battle(self, p1_id: int, p2_id: int, p1_team: list, p2_team: list):
        state = self._build_state(p1_id, p2_id, p1_team, p2_team)
        return await self.repo.create("ranked", p1_id, p2_id, json.dumps(state))

    def load_state(self, battle) -> dict:
        return json.loads(battle.state_json)

    async def save_state(self, battle, state: dict) -> None:
        await self.repo.save(battle, json.dumps(state), bool(state["finished"]))

    def apply_move(self, state: dict, actor_discord_id: int) -> dict:
        players = {state["player_one"]["discord_id"], state["player_two"]["discord_id"]}
        if actor_discord_id not in players:
            raise ValueError("You are not part of this battle.")
        return self.engine.resolve_turn(state)
