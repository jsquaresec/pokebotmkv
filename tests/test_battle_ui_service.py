from services.battle_ui_service import BattleUIService

def run():
    svc = BattleUIService()
    bar = svc.hp_bar(15, 20)
    assert "[" in bar and "]" in bar
    state = {
        "turn": 2,
        "player_one": {"active": {"name": "Pikachu", "level": 8, "hp": 15, "max_hp": 20}},
        "player_two": {"active": {"name": "Bulbasaur", "level": 7, "hp": 10, "max_hp": 22}},
    }
    text = svc.render_battle_view(1, state, 20)
    assert "Battle #1" in text
    print("battle ui service tests passed")

if __name__ == "__main__":
    run()
