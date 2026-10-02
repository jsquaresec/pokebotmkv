from fastapi import APIRouter
from core.database import SessionLocal
from repositories.live_events import LiveEventRepository

router = APIRouter(prefix="/live-events", tags=["live-events"])

@router.get("")
async def list_live_events():
    async with SessionLocal() as session:
        rows = await LiveEventRepository(session).list_active()
        return [{"id": x.id, "name": x.name, "event_type": x.event_type} for x in rows]
