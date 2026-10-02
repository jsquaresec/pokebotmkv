class SpawnBalanceService:
    def __init__(self):
        self.weights = {
            "common": 60,
            "uncommon": 25,
            "rare": 10,
            "epic": 4,
            "legendary": 1,
        }

    def get_weights(self) -> dict:
        return dict(self.weights)

    def set_weight(self, rarity: str, value: int) -> dict:
        if rarity not in self.weights:
            raise ValueError("Unknown rarity")
        if value <= 0:
            raise ValueError("Weight must be positive")
        self.weights[rarity] = value
        return dict(self.weights)
