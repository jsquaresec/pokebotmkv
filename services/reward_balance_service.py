class RewardBalanceService:
    def adjusted_coins(self, base: int, multiplier: float = 1.0) -> int:
        return max(1, int(base * multiplier))

    def adjusted_xp(self, base: int, multiplier: float = 1.0) -> int:
        return max(1, int(base * multiplier))
