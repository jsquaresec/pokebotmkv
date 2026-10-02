class BattleCleanupService:
    async def mark_finished(self, session, battle) -> None:
        battle.finished = True
        await session.commit()

    async def delete_finished(self, session, battle) -> None:
        if not battle.finished:
            raise ValueError("Cannot delete an unfinished battle.")
        await session.delete(battle)
        await session.commit()
