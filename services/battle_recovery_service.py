import json

class BattleRecoveryService:
    def parse_state(self, state_json: str) -> dict:
        state = json.loads(state_json)
        required_keys = {
            "turn",
            "finished",
            "winner_discord_id",
            "pending_action_p1",
            "pending_action_p2",
            "player_one",
            "player_two",
            "log",
        }
        missing = required_keys - set(state.keys())
        if missing:
            raise ValueError(f"Battle state missing keys: {sorted(missing)}")
        return state

    def summarize(self, battle) -> dict:
        state = self.parse_state(battle.state_json)
        return {
            "battle_id": battle.id,
            "battle_type": battle.battle_type,
            "finished": battle.finished,
            "turn": state["turn"],
            "player_one": state["player_one"]["name"],
            "player_two": state["player_two"]["name"],
            "p1_ready": state["pending_action_p1"] is not None,
            "p2_ready": state["pending_action_p2"] is not None,
            "log_count": len(state["log"]),
        }
