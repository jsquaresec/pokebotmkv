from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.inventory_item import InventoryItem

class InventoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_item(self, owner_discord_id: int, sku: str):
        result = await self.session.execute(
            select(InventoryItem).where(InventoryItem.owner_discord_id == owner_discord_id, InventoryItem.sku == sku)
        )
        return result.scalar_one_or_none()

    async def add_item(self, owner_discord_id: int, sku: str, quantity: int):
        row = await self.get_item(owner_discord_id, sku)
        if row is None:
            row = InventoryItem(owner_discord_id=owner_discord_id, sku=sku, quantity=quantity)
            self.session.add(row)
        else:
            row.quantity += quantity
        await self.session.flush()
        return row

    async def list_for_owner(self, owner_discord_id: int):
        result = await self.session.execute(select(InventoryItem).where(InventoryItem.owner_discord_id == owner_discord_id))
        return list(result.scalars().all())

    async def get_item_locked(self, owner_discord_id: int, sku: str):
        result = await self.session.execute(
            select(InventoryItem).where(InventoryItem.owner_discord_id == owner_discord_id, InventoryItem.sku == sku).with_for_update()
        )
        return result.scalar_one_or_none()
