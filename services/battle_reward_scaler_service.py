class BattleRewardScalerService:
    def scale(self, base_coins: int, base_xp: int, winner_tier: str) -> dict:
        mult = {
            "Bronze": 1.0,
            "Silver": 1.1,
            "Gold": 1.25,
            "Elite": 1.5,
        }.get(winner_tier, 1.0)
        return {
            "coins": int(base_coins * mult),
            "xp": int(base_xp * mult),
        }
