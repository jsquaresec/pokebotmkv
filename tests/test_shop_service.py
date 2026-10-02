import asyncio
from unittest.mock import AsyncMock, patch
from services.shop_service import ShopService

class DummyUser:
    def __init__(self):
        self.discord_id = 1001
        self.balance = 500

class DummyInventoryRepo:
    def __init__(self):
        self.session = self
        self.rows = []
    async def add_item(self, owner_discord_id, sku, quantity):
        row = type("R", (), {"owner_discord_id": owner_discord_id, "sku": sku, "quantity": quantity})()
        self.rows.append(row)
        return row
    async def commit(self):
        return None

async def main():
    user = DummyUser()
    repo = DummyInventoryRepo()
    svc = ShopService(repo, "data/shop_catalog.json")
    with patch("services.daily_mission_service.DailyMissionService.record", new=AsyncMock()):
        result = await svc.purchase(user, "poke_ball", 2)
    assert result["total"] == 200
    assert user.balance == 300
    print("shop service tests passed")

if __name__ == "__main__":
    asyncio.run(main())
