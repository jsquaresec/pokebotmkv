class RewardFeedbackService:
    def catch_rewards(self, rarity_multiplier: float, catch_streak: int = 0) -> dict:
        base_xp = int(100 * rarity_multiplier)
        base_coins = int(60 * rarity_multiplier)
        bonus_xp = 20 * catch_streak if catch_streak > 0 else 0
        return {
            "XP": base_xp + bonus_xp,
            "Coins": base_coins,
            "Streak Bonus": f"+{bonus_xp} XP" if bonus_xp else "None",
        }
