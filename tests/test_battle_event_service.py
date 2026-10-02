import asyncio
from services.battle_event_service import BattleEventService

class DummyRedisQueue:
    def __init__(self):
        self.rows = []
    async def push(self, queue_name, payload):
        self.rows.append((queue_name, payload))
        return True
    async def peek_recent(self, queue_name, limit=20):
        return [payload for q, payload in self.rows if q == queue_name][-limit:]

async def main():
    queue = DummyRedisQueue()
    service = BattleEventService(queue)
    ok = await service.publish_match_created(12, 1001, 1002)
    assert ok is True
    rows = await service.recent_events()
    assert rows[0]["battle_id"] == 12
    assert rows[0]["type"] == "ranked_match_created"
    print("battle event service tests passed")

if __name__ == "__main__":
    asyncio.run(main())
