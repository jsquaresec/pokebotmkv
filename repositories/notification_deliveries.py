from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from models.notification_delivery import NotificationDelivery

class NotificationDeliveryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, event_type: str, recipient_discord_id: int, related_battle_id: int | None, status: str, payload_json: str, retry_count: int = 0) -> NotificationDelivery:
        row = NotificationDelivery(
            event_type=event_type,
            recipient_discord_id=recipient_discord_id,
            related_battle_id=related_battle_id,
            status=status,
            payload_json=payload_json,
            retry_count=retry_count,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def latest_for_recipient(self, recipient_discord_id: int, limit: int = 25) -> list[NotificationDelivery]:
        result = await self.session.execute(
            select(NotificationDelivery)
            .where(NotificationDelivery.recipient_discord_id == recipient_discord_id)
            .order_by(desc(NotificationDelivery.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def latest_all(self, limit: int = 50) -> list[NotificationDelivery]:
        result = await self.session.execute(
            select(NotificationDelivery)
            .order_by(desc(NotificationDelivery.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def queued(self, limit: int = 50) -> list[NotificationDelivery]:
        result = await self.session.execute(
            select(NotificationDelivery)
            .where(NotificationDelivery.status == "queued")
            .order_by(desc(NotificationDelivery.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def dead_lettered(self, limit: int = 50) -> list[NotificationDelivery]:
        result = await self.session.execute(
            select(NotificationDelivery)
            .where(NotificationDelivery.status == "dead_lettered")
            .order_by(desc(NotificationDelivery.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def save(self, row: NotificationDelivery) -> NotificationDelivery:
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def stats(self) -> dict:
        total = await self.session.scalar(select(func.count(NotificationDelivery.id)))
        queued = await self.session.scalar(select(func.count(NotificationDelivery.id)).where(NotificationDelivery.status == "queued"))
        sent = await self.session.scalar(select(func.count(NotificationDelivery.id)).where(NotificationDelivery.status == "sent"))
        failed = await self.session.scalar(select(func.count(NotificationDelivery.id)).where(NotificationDelivery.status == "failed"))
        dead_lettered = await self.session.scalar(select(func.count(NotificationDelivery.id)).where(NotificationDelivery.status == "dead_lettered"))
        return {
            "total": int(total or 0),
            "queued": int(queued or 0),
            "sent": int(sent or 0),
            "failed": int(failed or 0),
            "dead_lettered": int(dead_lettered or 0),
        }
