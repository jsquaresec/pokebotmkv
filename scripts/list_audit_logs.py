import asyncio
from core.database import SessionLocal, init_models
from repositories.audit_logs import AuditLogRepository

async def main():
    await init_models()
    async with SessionLocal() as session:
        rows = await AuditLogRepository(session).latest(50)
        if not rows:
            print("No audit logs.")
            return
        for row in rows:
            print({
                "id": row.id,
                "event_type": row.event_type,
                "actor_discord_id": row.actor_discord_id,
                "target_id": row.target_id,
                "details": row.details,
            })

if __name__ == "__main__":
    asyncio.run(main())
