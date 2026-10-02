from repositories.quests import QuestRepository

class QuestService:
    DEFAULTS = {
        "catch_3": 3,
        "win_1_battle": 1,
    }

    def __init__(self, repo: QuestRepository):
        self.repo = repo

    async def ensure_defaults(self, discord_id: int):
        rows = []
        for code, target in self.DEFAULTS.items():
            rows.append(await self.repo.get_or_create(discord_id, code, target))
        return rows

    async def add_progress(self, discord_id: int, quest_code: str, amount: int = 1):
        target = self.DEFAULTS.get(quest_code, 1)
        row = await self.repo.get_or_create(discord_id, quest_code, target)
        if row.status != "claimed":
            row.progress_value = min(row.target_value, row.progress_value + amount)
            if row.progress_value >= row.target_value:
                row.status = "complete"
            await self.repo.save(row)
        return row

    async def claim(self, discord_id: int, quest_code: str):
        row = await self.repo.get_or_create(discord_id, quest_code, self.DEFAULTS.get(quest_code, 1))
        if row.status != "complete":
            raise ValueError("Quest is not complete.")
        row.status = "claimed"
        await self.repo.save(row)
        reward = 150 if quest_code == "catch_3" else 250
        return {"quest": row, "reward": reward}
