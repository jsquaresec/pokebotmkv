from repositories.achievements import AchievementRepository


ACHIEVEMENTS = {
    "first_catch": "First Catch",
    "collector_10": "Collector I",
    "collector_100": "Collector II",
    "dex_25": "Pokédex Explorer",
    "dex_100": "Pokédex Researcher",
    "millionaire": "Coin Millionaire",
}


class AchievementService:
    def __init__(self, session):
        self.repo = AchievementRepository(session)

    async def evaluate(self, discord_id: int, species_seen: int, total_catches: int, balance: int):
        earned = []
        checks = {
            "first_catch": total_catches >= 1,
            "collector_10": total_catches >= 10,
            "collector_100": total_catches >= 100,
            "dex_25": species_seen >= 25,
            "dex_100": species_seen >= 100,
            "millionaire": balance >= 1_000_000,
        }
        for code, qualifies in checks.items():
            if qualifies:
                _, created = await self.repo.unlock(discord_id, code)
                if created:
                    earned.append(ACHIEVEMENTS[code])
        return earned
