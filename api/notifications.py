import json
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import SessionLocal
from repositories.notification_deliveries import NotificationDeliveryRepository
from services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])

async def get_session():
    async with SessionLocal() as session:
        yield session

@router.get("/recent")
async def recent_notifications(session: AsyncSession = Depends(get_session)):
    rows = await NotificationService(NotificationDeliveryRepository(session)).recent_all(50)
    return [
        {
            "id": r.id,
            "event_type": r.event_type,
            "recipient_discord_id": r.recipient_discord_id,
            "related_battle_id": r.related_battle_id,
            "status": r.status,
            "retry_count": r.retry_count,
            "payload": json.loads(r.payload_json),
        }
        for r in rows
    ]

@router.get("/stats")
async def notification_stats(session: AsyncSession = Depends(get_session)):
    return await NotificationService(NotificationDeliveryRepository(session)).stats()

@router.get("/dead-letter")
async def dead_letter_notifications(session: AsyncSession = Depends(get_session)):
    rows = await NotificationDeliveryRepository(session).dead_lettered(50)
    return [
        {
            "id": r.id,
            "event_type": r.event_type,
            "recipient_discord_id": r.recipient_discord_id,
            "related_battle_id": r.related_battle_id,
            "status": r.status,
            "retry_count": r.retry_count,
            "payload": json.loads(r.payload_json),
        }
        for r in rows
    ]
