import json
from pathlib import Path
from repositories.inventory import InventoryRepository

class ShopService:
    def __init__(self, inventory_repo: InventoryRepository, path: str = "data/shop_catalog.json"):
        self.inventory_repo = inventory_repo
        self.catalog = json.loads(Path(path).read_text(encoding="utf-8"))

    def get_catalog(self):
        return self.catalog

    def get_item(self, sku: str):
        for item in self.catalog:
            if item["sku"] == sku:
                return item
        return None

    async def purchase(self, user, sku: str, quantity: int = 1):
        item = self.get_item(sku)
        if item is None:
            raise ValueError("Unknown item.")
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        total = item["price"] * quantity
        if user.balance < total:
            raise ValueError("Not enough balance.")
        user.balance -= total
        row = await self.inventory_repo.add_item(user.discord_id, sku, quantity)
        from services.daily_mission_service import DailyMissionService
        await DailyMissionService(self.inventory_repo.session).record(user.discord_id, 'shop')
        await self.inventory_repo.session.commit()
        return {"item": item, "quantity": quantity, "total": total, "inventory": row}

