import asyncio
import json
from services.reward_service import RewardService

class DummyRow:
    def __init__(self, recipient_discord_id, reward_type, amount, related_battle_id, details_json):
        self.id = 1
        self.recipient_discord_id = recipient_discord_id
        self.reward_type = reward_type
        self.amount = amount
        self.related_battle_id = related_battle_id
        self.details_json = details_json

class DummyRepo:
    def __init__(self):
        self.rows = []

    async def create(self, recipient_discord_id, reward_type, amount, related_battle_id, details_json):
        row = DummyRow(recipient_discord_id, reward_type, amount, related_battle_id, details_json)
        self.rows.append(row)
        return row

    async def latest(self, limit=50):
        return self.rows[:limit]

async def main():
    repo = DummyRepo()
    svc = RewardService(repo)
    row = await svc.grant_battle_win(1001, 77, 100, 50)
    assert row.amount == 100
    details = json.loads(row.details_json)
    assert details["xp"] == 50
    recent = await svc.recent()
    assert len(recent) == 1
    print("reward service tests passed")

if __name__ == "__main__":
    asyncio.run(main())
