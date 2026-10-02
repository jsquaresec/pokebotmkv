from services.battle_action_service import BattleActionService

def run():
    service = BattleActionService()
    state = {
        "finished": False,
        "pending_action_p1": None,
        "pending_action_p2": None,
        "player_one": {"discord_id": 111},
        "player_two": {"discord_id": 222},
    }
    state = service.submit_move(state, 111, "Tackle")
    assert state["pending_action_p1"] == {"type": "move", "move_name": "Tackle"}
    state = service.submit_switch(state, 222, 2)
    assert state["pending_action_p2"] == {"type": "switch", "target_slot": 2}
    assert service.both_ready(state) is True
    print("battle action service tests passed")

if __name__ == "__main__":
    run()
