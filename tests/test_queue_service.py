import asyncio
from datetime import datetime

from services.queue_service import QueueService

class Entry:
    def __init__(self, discord_id, rating):
        self.discord_id = discord_id
        self.rating = rating
        self.created_at = datetime.utcnow()

class DummyRepo:
    def __init__(self):
        self.entries = []

    async def get_by_discord_id(self, discord_id):
        for e in self.entries:
            if e.discord_id == discord_id:
                return e
        return None

    async def enqueue(self, discord_id, rating):
        row = Entry(discord_id, rating)
        self.entries.append(row)
        return row

    async def list_entries(self):
        return list(self.entries)

    async def delete(self, entry):
        self.entries.remove(entry)

async def main():
    repo = DummyRepo()
    service = QueueService(repo)

    result = await service.join_or_match(100, 1000)
    assert result["status"] == "queued"

    result = await service.join_or_match(200, 1010)
    assert result["status"] == "matched"
    assert set(result["players"]) == {100, 200}

    result = await service.join_or_match(300, 980)
    assert result["status"] == "queued"
    left = await service.leave(300)
    assert left is True
    print("queue service tests passed")

if __name__ == "__main__":
    asyncio.run(main())
