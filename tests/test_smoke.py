from services.ranked_service import RankedService
from services.ruleset_legality_service import RulesetLegalityService

def run():
    ranked = RankedService()
    a, b = ranked.apply_result(1000, 1000, 1.0)
    assert a > 1000
    assert b < 1000

    rules = RulesetLegalityService()
    rules.validate_team_for_ruleset([1, 2, 3], {"max_team_size": 6})
    try:
        rules.validate_team_for_ruleset([1, 2, 3, 4, 5, 6, 7], {"max_team_size": 6})
        raise AssertionError("Expected validation failure")
    except ValueError:
        pass

    try:
        rules.validate_action_for_ruleset("item", "Potion", {"items_allowed": False})
        raise AssertionError("Expected item restriction failure")
    except ValueError:
        pass

    print("smoke tests passed")

if __name__ == "__main__":
    run()
