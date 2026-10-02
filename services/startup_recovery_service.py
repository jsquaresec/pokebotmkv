from sqlalchemy import select
from models.active_battle import ActiveBattle
from services.battle_recovery_service import BattleRecoveryService

class StartupRecoveryService:
    def __init__(self):
        self.recovery = BattleRecoveryService()

    async def scan_active_battles(self, session) -> list[dict]:
        result = await session.execute(select(ActiveBattle).where(ActiveBattle.finished.is_(False)))
        rows = list(result.scalars().all())
        summaries = []
        for row in rows:
            try:
                summaries.append(self.recovery.summarize(row))
            except Exception as exc:
                summaries.append({"battle_id": row.id, "error": str(exc)})
        return summaries
