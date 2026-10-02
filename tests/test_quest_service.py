import asyncio
from services.quest_service import QuestService

class DummyQuest:
    def __init__(self, code, target):
        self.quest_code = code
        self.target_value = target
        self.progress_value = 0
        self.status = "active"

class DummyRepo:
    def __init__(self):
        self.rows = {}
    async def get_or_create(self, discord_id, quest_code, target_value):
        key = (discord_id, quest_code)
        if key not in self.rows:
            self.rows[key] = DummyQuest(quest_code, target_value)
        return self.rows[key]
    async def list_for_user(self, discord_id):
        return [v for (uid, _), v in self.rows.items() if uid == discord_id]
    async def save(self, row):
        return row

async def main():
    svc = QuestService(DummyRepo())
    rows = await svc.ensure_defaults(1001)
    assert len(rows) == 2
    row = await svc.add_progress(1001, "catch_3", 3)
    assert row.status == "complete"
    claimed = await svc.claim(1001, "catch_3")
    assert claimed["reward"] == 150
    print("quest service tests passed")

if __name__ == "__main__":
    asyncio.run(main())
