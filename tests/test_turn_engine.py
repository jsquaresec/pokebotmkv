from battle.engine import TurnEngine

def run():
    engine = TurnEngine()
    state = {
        "turn": 1,
        "finished": False,
        "winner_discord_id": None,
        "pending_action_p1": {"type": "move", "move_name": "Quick Attack"},
        "pending_action_p2": {"type": "move", "move_name": "Tackle"},
        "player_one": {
            "discord_id": 1,
            "active_slot": 0,
            "requires_replacement": False,
            "active": {"discord_id": 1, "name": "Pikachu", "hp": 20, "max_hp": 20, "attack": 12, "defense": 7, "speed": 10, "status": None},
            "bench": [{"name": "Eevee", "hp": 18, "max_hp": 18, "attack": 9, "defense": 9, "speed": 9, "status": None}],
        },
        "player_two": {
            "discord_id": 2,
            "active_slot": 0,
            "requires_replacement": False,
            "active": {"discord_id": 2, "name": "Bulbasaur", "hp": 22, "max_hp": 22, "attack": 9, "defense": 9, "speed": 12, "status": None},
            "bench": [{"name": "Squirtle", "hp": 20, "max_hp": 20, "attack": 8, "defense": 10, "speed": 8, "status": None}],
        },
        "log": [],
    }
    assert engine.first_actor(state) == "player_one"
    state = engine.resolve_turn(state)
    assert len(state["log"]) >= 2

    state2 = {
        "turn": 1,
        "finished": False,
        "winner_discord_id": None,
        "pending_action_p1": {"type": "switch", "target_slot": 2},
        "pending_action_p2": {"type": "move", "move_name": "Vine Whip"},
        "player_one": {
            "discord_id": 1,
            "active_slot": 0,
            "requires_replacement": False,
            "active": {"discord_id": 1, "name": "Squirtle", "hp": 20, "max_hp": 20, "attack": 8, "defense": 10, "speed": 7, "status": None},
            "bench": [{"name": "Pikachu", "hp": 16, "max_hp": 16, "attack": 11, "defense": 7, "speed": 12, "status": None}],
        },
        "player_two": {
            "discord_id": 2,
            "active_slot": 0,
            "requires_replacement": False,
            "active": {"discord_id": 2, "name": "Bulbasaur", "hp": 16, "max_hp": 16, "attack": 11, "defense": 7, "speed": 12, "status": None},
            "bench": [],
        },
        "log": [],
    }
    state2 = engine.resolve_turn(state2)
    assert state2["player_one"]["active"]["name"] == "Pikachu"
    print("turn engine tests passed")

if __name__ == "__main__":
    run()
