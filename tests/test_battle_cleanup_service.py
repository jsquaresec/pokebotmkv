import asyncio
from services.battle_cleanup_service import BattleCleanupService

class DummyBattle:
    def __init__(self, finished):
        self.finished = finished

class DummySession:
    def __init__(self):
        self.deleted = False
        self.committed = False
    async def delete(self, _obj):
        self.deleted = True
    async def commit(self):
        self.committed = True

async def main():
    service = BattleCleanupService()

    session = DummySession()
    battle = DummyBattle(False)
    await service.mark_finished(session, battle)
    assert battle.finished is True
    assert session.committed is True

    session2 = DummySession()
    battle2 = DummyBattle(True)
    await service.delete_finished(session2, battle2)
    assert session2.deleted is True
    assert session2.committed is True

    session3 = DummySession()
    battle3 = DummyBattle(False)
    try:
        await service.delete_finished(session3, battle3)
        raise AssertionError("Expected delete failure")
    except ValueError:
        pass

    print("battle cleanup service tests passed")

if __name__ == "__main__":
    asyncio.run(main())
