from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import SessionLocal
from repositories.queue_entries import QueueEntryRepository
from repositories.active_battles import ActiveBattleRepository

router = APIRouter(prefix="/admin/ops", tags=["admin_ops"])

async def get_session():
    async with SessionLocal() as session:
        yield session

@router.post("/queue/reset")
async def reset_queue(session: AsyncSession = Depends(get_session)):
    repo = QueueEntryRepository(session)
    rows = await repo.list_entries()
    removed = 0
    for row in list(rows):
        await repo.delete(row)
        removed += 1
    return {"removed_queue_entries": removed}

@router.post("/battle/{battle_id}/force-finish")
async def force_finish_battle(battle_id: int, session: AsyncSession = Depends(get_session)):
    repo = ActiveBattleRepository(session)
    battle = await repo.get_by_id(battle_id)
    if battle is None:
        return {"ok": False, "error": "battle not found"}
    battle.finished = True
    await session.commit()
    return {"ok": True, "battle_id": battle_id, "finished": True}
