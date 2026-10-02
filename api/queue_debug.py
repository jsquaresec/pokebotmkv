from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import SessionLocal
from repositories.queue_entries import QueueEntryRepository
from services.redis_queue_service import RedisQueueService

router = APIRouter(prefix="/queue", tags=["queue"])

async def get_session():
    async with SessionLocal() as session:
        yield session

@router.get("/status")
async def queue_status(session: AsyncSession = Depends(get_session)):
    repo = QueueEntryRepository(session)
    rows = await repo.list_entries()
    redis_queue = RedisQueueService()
    redis_events = await redis_queue.length("queue_events")
    redis_battle_events = await redis_queue.length("battle_events")
    return {
        "db_queue_entries": len(rows),
        "redis_queue_events": redis_events,
        "redis_battle_events": redis_battle_events,
    }
