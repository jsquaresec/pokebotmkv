class EconomyBalanceService:
    def __init__(self):
        self.values = {
            "base_catch_coins": 60,
            "base_battle_win_coins": 100,
            "market_listing_fee_rate": 0.05,
            "market_sale_fee_rate": 0.08,
        }

    def snapshot(self) -> dict:
        return dict(self.values)

    def set_value(self, key: str, value: float) -> dict:
        if key not in self.values:
            raise ValueError("Unknown economy balance key")
        if value <= 0:
            raise ValueError("Value must be positive")
        self.values[key] = value
        return dict(self.values)
