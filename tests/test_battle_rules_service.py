from services.battle_rules_service import BattleRulesService

def run():
    rules = BattleRulesService()
    assert rules.validate_move_choice("Pikachu", "Thunder Shock") == "Thunder Shock"
    try:
        rules.validate_move_choice("Pikachu", "Vine Whip")
        raise AssertionError("Expected illegal move failure")
    except ValueError:
        pass

    player_state = {
        "bench": [
            {"name": "Eevee", "hp": 10},
            {"name": "Charmander", "hp": 0},
        ]
    }
    assert rules.validate_switch_target(player_state, 2) == 0
    try:
        rules.validate_switch_target(player_state, 3)
        raise AssertionError("Expected fainted switch target failure")
    except ValueError:
        pass
    print("battle rules service tests passed")

if __name__ == "__main__":
    run()
