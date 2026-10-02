import asyncio
from sqlalchemy import select
from core.database import SessionLocal, init_models
from models.active_battle import ActiveBattle
from services.battle_recovery_service import BattleRecoveryService

async def main():
    await init_models()
    recovery = BattleRecoveryService()
    async with SessionLocal() as session:
        result = await session.execute(select(ActiveBattle).where(ActiveBattle.finished.is_(False)))
        rows = list(result.scalars().all())
        if not rows:
            print("No active battles.")
            return
        for row in rows:
            try:
                summary = recovery.summarize(row)
                print(summary)
            except Exception as exc:
                print({"battle_id": row.id, "error": str(exc)})

if __name__ == "__main__":
    asyncio.run(main())
