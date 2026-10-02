from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import SessionLocal
from repositories.inventory import InventoryRepository

router = APIRouter(prefix="/inventory", tags=["inventory"])

async def get_session():
    async with SessionLocal() as session:
        yield session

@router.get("/recent/{discord_id}")
async def inventory_recent(discord_id: int, session: AsyncSession = Depends(get_session)):
    rows = await InventoryRepository(session).list_for_owner(discord_id)
    return [{"id": r.id, "owner_discord_id": r.owner_discord_id, "sku": r.sku, "quantity": r.quantity} for r in rows]
