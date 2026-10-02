import asyncio
from services.audit_service import AuditService

class DummyRow:
    def __init__(self, event_type, actor_discord_id, target_id, details):
        self.event_type = event_type
        self.actor_discord_id = actor_discord_id
        self.target_id = target_id
        self.details = details

class DummyRepo:
    def __init__(self):
        self.rows = []

    async def create(self, event_type, actor_discord_id, target_id, details=""):
        row = DummyRow(event_type, actor_discord_id, target_id, details)
        self.rows.append(row)
        return row

async def main():
    repo = DummyRepo()
    service = AuditService(repo)
    row = await service.log("battle_finalized", 123, 9, "winner=123")
    assert row.event_type == "battle_finalized"
    assert row.actor_discord_id == 123
    assert row.target_id == 9
    assert row.details == "winner=123"
    print("audit service tests passed")

if __name__ == "__main__":
    asyncio.run(main())
