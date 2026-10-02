from services.battle_presentation_service import BattlePresentationService

def run():
    svc = BattlePresentationService()
    card = svc.render_battle_card(
        {"name": "Pikachu", "level": 10, "hp": 20, "max_hp": 30},
        {"name": "Bulbasaur", "level": 9, "hp": 18, "max_hp": 25},
        3,
        20,
    )
    assert "Turn 3" in card
    assert "Pikachu" in card
    print("battle presentation service tests passed")

if __name__ == "__main__":
    run()
