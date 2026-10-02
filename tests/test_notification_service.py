import asyncio
import json
from services.notification_service import NotificationService

class DummyRow:
    def __init__(self, event_type, recipient_discord_id, related_battle_id, status, payload_json, retry_count=0):
        self.id = 1
        self.event_type = event_type
        self.recipient_discord_id = recipient_discord_id
        self.related_battle_id = related_battle_id
        self.status = status
        self.payload_json = payload_json
        self.retry_count = retry_count

class DummyRepo:
    def __init__(self):
        self.rows = []

    async def create(self, event_type, recipient_discord_id, related_battle_id, status, payload_json, retry_count=0):
        row = DummyRow(event_type, recipient_discord_id, related_battle_id, status, payload_json, retry_count)
        self.rows.append(row)
        return row

    async def latest_for_recipient(self, recipient_discord_id, limit=25):
        return [r for r in self.rows if r.recipient_discord_id == recipient_discord_id][:limit]

    async def latest_all(self, limit=50):
        return self.rows[:limit]

    async def stats(self):
        total = len(self.rows)
        queued = len([r for r in self.rows if r.status == "queued"])
        sent = len([r for r in self.rows if r.status == "sent"])
        failed = len([r for r in self.rows if r.status == "failed"])
        return {"total": total, "queued": queued, "sent": sent, "failed": failed}

async def main():
    repo = DummyRepo()
    service = NotificationService(repo)
    row = await service.record_match_created(1001, 55, {"battle_id": 55, "player_one_discord_id": 1001})
    assert row.event_type == "ranked_match_created"
    assert row.related_battle_id == 55
    assert row.retry_count == 0
    assert json.loads(row.payload_json)["battle_id"] == 55
    recent = await service.recent_for_recipient(1001, 10)
    assert len(recent) == 1
    stats = await service.stats()
    assert stats["queued"] == 1
    print("notification service tests passed")

if __name__ == "__main__":
    asyncio.run(main())
