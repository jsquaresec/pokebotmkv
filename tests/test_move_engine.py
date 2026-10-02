from battle.move_engine import MoveEngine

def run():
    engine = MoveEngine("data/moves.json")
    tackle = engine.get_move("Tackle")
    assert tackle is not None
    assert tackle["power"] == 40

    attacker = {"name": "Pikachu", "attack": 12, "discord_id": 1}
    defender = {"name": "Bulbasaur", "hp": 30, "defense": 10, "discord_id": 2, "status": None}
    state = {"finished": False, "winner_discord_id": None, "log": []}
    engine.resolve_move(attacker, defender, "Thunder Shock", state)
    assert defender["hp"] < 30
    assert len(state["log"]) >= 2

    defender2 = {"name": "Bulbasaur", "hp": 30, "defense": 10, "attack": 10, "discord_id": 2, "status": None}
    state2 = {"finished": False, "winner_discord_id": None, "log": []}
    engine.resolve_move(attacker, defender2, "Growl", state2)
    assert defender2["attack"] == 10
    assert defender2["stat_stages"]["attack"] == -1
    print("move engine tests passed")

if __name__ == "__main__":
    run()
