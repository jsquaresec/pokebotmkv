import asyncio
import json
from services.trade_service import TradeService

class DummyOffer:
    def __init__(self, id=1):
        self.id = id

class DummyRepo:
    def __init__(self):
        self.rows = []
    async def create(self, from_discord_id, to_discord_id, offered_json, requested_json, status="open"):
        self.rows.append((from_discord_id, to_discord_id, offered_json, requested_json, status))
        return DummyOffer(1)
    async def latest(self, limit=50):
        return self.rows[:limit]

async def main():
    svc = TradeService(DummyRepo())
    offer = await svc.create_offer(1, 2, {"sku": "poke_ball", "quantity": 1}, {"sku": "potion", "quantity": 1})
    assert offer.id == 1
    print("trade service tests passed")

if __name__ == "__main__":
    asyncio.run(main())
