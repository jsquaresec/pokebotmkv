import random

class RarityService:
    RARITY_WEIGHTS = {
        "common": 60,
        "uncommon": 25,
        "rare": 10,
        "epic": 4,
        "legendary": 1,
    }

    RARITY_STYLES = {
        "common": {"emoji": "⚪", "label": "COMMON"},
        "uncommon": {"emoji": "🟢", "label": "UNCOMMON"},
        "rare": {"emoji": "🔵", "label": "RARE"},
        "epic": {"emoji": "🟣", "label": "EPIC"},
        "legendary": {"emoji": "🟡", "label": "LEGENDARY"},
    }

    def roll_rarity(self) -> str:
        pool = []
        for rarity, weight in self.RARITY_WEIGHTS.items():
            pool.extend([rarity] * weight)
        return random.choice(pool)

    def style_for(self, rarity: str) -> dict:
        return self.RARITY_STYLES.get(rarity, self.RARITY_STYLES["common"])

    def reward_multiplier(self, rarity: str) -> float:
        return {
            "common": 1.0,
            "uncommon": 1.2,
            "rare": 1.5,
            "epic": 2.0,
            "legendary": 3.0,
        }.get(rarity, 1.0)
