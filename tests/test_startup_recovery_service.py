import json
import asyncio
from services.startup_recovery_service import StartupRecoveryService

class DummyBattle:
    def __init__(self, battle_id, finished, state_json):
        self.id = battle_id
        self.battle_type = "ranked"
        self.finished = finished
        self.state_json = state_json

class DummyResult:
    def __init__(self, rows):
        self._rows = rows
    def scalars(self):
        return self
    def all(self):
        return self._rows

class DummySession:
    def __init__(self, rows):
        self.rows = rows
    async def execute(self, _query):
        unfinished = [x for x in self.rows if not x.finished]
        return DummyResult(unfinished)

async def main():
    valid_state = json.dumps({
        "turn": 2,
        "finished": False,
        "winner_discord_id": None,
        "pending_action_p1": None,
        "pending_action_p2": {"type": "attack"},
        "player_one": {"name": "Pikachu"},
        "player_two": {"name": "Eevee"},
        "log": [],
    })
    bad_state = json.dumps({"turn": 1})
    rows = [
        DummyBattle(1, False, valid_state),
        DummyBattle(2, True, valid_state),
        DummyBattle(3, False, bad_state),
    ]
    session = DummySession(rows)
    service = StartupRecoveryService()
    out = await service.scan_active_battles(session)
    assert len(out) == 2
    assert any(x.get("battle_id") == 1 for x in out)
    assert any(x.get("battle_id") == 3 and "error" in x for x in out)
    print("startup recovery service tests passed")

if __name__ == "__main__":
    asyncio.run(main())
