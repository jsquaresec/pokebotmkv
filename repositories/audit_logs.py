from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from models.audit_log import AuditLog

class AuditLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, event_type: str, actor_discord_id: int | None, target_id: int | None, details: str = "") -> AuditLog:
        row = AuditLog(
            event_type=event_type,
            actor_discord_id=actor_discord_id,
            target_id=target_id,
            details=details,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def latest(self, limit: int = 25) -> list[AuditLog]:
        result = await self.session.execute(select(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit))
        return list(result.scalars().all())
