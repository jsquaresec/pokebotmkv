from services.battle_ui_polish_service import BattleUIPolishService

def run():
    svc = BattleUIPolishService()
    bar = svc.hp_bar(15, 20)
    assert "[" in bar and "]" in bar
    view = svc.render_turn_state("Pikachu", 15, 20, "Bulbasaur", 8, 20, 3)
    assert "Turn 3" in view
    assert "Pikachu" in view
    print("battle ui polish service tests passed")

if __name__ == "__main__":
    run()
