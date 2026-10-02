from fastapi import APIRouter
from services.redis_queue_service import RedisQueueService

router = APIRouter(prefix="/queue", tags=["queue"])

@router.get("/events")
async def queue_events():
    queue = RedisQueueService()
    return {
        "battle_events": await queue.peek_recent("battle_events", 25),
        "queue_events": await queue.peek_recent("queue_events", 25),
    }
