class RulesetLegalityService:
    def validate_team_for_ruleset(self, team: list, ruleset: dict) -> None:
        max_team_size = int(ruleset.get("max_team_size", 6))
        if len(team) > max_team_size:
            raise ValueError(f"Ruleset allows only {max_team_size} Pokémon")

    def validate_action_for_ruleset(self, action_type: str, value, ruleset: dict) -> None:
        if action_type == "item" and not ruleset.get("items_allowed", True):
            raise ValueError("Items are disabled in this ruleset")
