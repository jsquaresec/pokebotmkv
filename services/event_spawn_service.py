class EventSpawnService:
    def choose_rarity(self, base_rarity: str, event_code: str | None):
        if event_code == "legendary_hour":
            return "legendary"
        if event_code == "rare_surge" and base_rarity == "common":
            return "rare"
        return base_rarity

    def reward_multiplier(self, event_code: str | None) -> float:
        if event_code == "double_rewards":
            return 2.0
        if event_code == "rare_surge":
            return 1.25
        return 1.0
