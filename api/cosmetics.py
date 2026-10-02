from fastapi import APIRouter
from core.database import SessionLocal
from repositories.cosmetics import CosmeticRepository

router = APIRouter(prefix="/cosmetics", tags=["cosmetics"])

@router.get("")
async def list_cosmetics():
    async with SessionLocal() as session:
        rows = await CosmeticRepository(session).list_active()
        return [{"id": x.id, "name": x.name, "type": x.cosmetic_type, "rarity": x.rarity} for x in rows]
