import asyncio
from core.database import SessionLocal, init_models
from services.startup_recovery_service import StartupRecoveryService

async def main():
    await init_models()
    async with SessionLocal() as session:
        service = StartupRecoveryService()
        rows = await service.scan_active_battles(session)
        if not rows:
            print("No unfinished battles found.")
            return
        for row in rows:
            print(row)

if __name__ == "__main__":
    asyncio.run(main())
