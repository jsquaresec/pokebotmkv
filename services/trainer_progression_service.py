class TrainerProgressionService:
    @staticmethod
    def required_xp(level: int) -> int:
        return level * level * 100

    def grant(self, user, amount: int):
        user.trainer_xp += max(0, amount)
        user.season_xp += max(0, amount)
        gained = 0
        while user.trainer_level < 100 and user.trainer_xp >= self.required_xp(user.trainer_level):
            user.trainer_xp -= self.required_xp(user.trainer_level)
            user.trainer_level += 1
            gained += 1
        return gained
