import json
from services.battle_recovery_service import BattleRecoveryService

class DummyBattle:
    def __init__(self):
        self.id = 7
        self.battle_type = "ranked"
        self.finished = False
        self.state_json = json.dumps({
            "turn": 3,
            "finished": False,
            "winner_discord_id": None,
            "pending_action_p1": {"type": "attack"},
            "pending_action_p2": None,
            "player_one": {"name": "Pikachu"},
            "player_two": {"name": "Bulbasaur"},
            "log": ["Pikachu hit Bulbasaur"],
        })

def run():
    service = BattleRecoveryService()
    battle = DummyBattle()
    state = service.parse_state(battle.state_json)
    assert state["turn"] == 3
    summary = service.summarize(battle)
    assert summary["battle_id"] == 7
    assert summary["p1_ready"] is True
    assert summary["p2_ready"] is False
    assert summary["player_one"] == "Pikachu"
    assert summary["player_two"] == "Bulbasaur"

    bad_json = json.dumps({"turn": 1})
    try:
        service.parse_state(bad_json)
        raise AssertionError("Expected failure for missing keys")
    except ValueError:
        pass

    print("battle recovery service tests passed")

if __name__ == "__main__":
    run()
