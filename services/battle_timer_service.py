import time

class BattleTimerService:
    def __init__(self):
        self.deadlines: dict[int, float] = {}

    def start_turn(self, battle_id: int, seconds: int = 30) -> None:
        self.deadlines[battle_id] = time.time() + seconds

    def remaining(self, battle_id: int) -> int:
        end = self.deadlines.get(battle_id)
        if end is None:
            return 0
        return max(0, int(end - time.time()))

    def expired(self, battle_id: int) -> bool:
        end = self.deadlines.get(battle_id)
        return False if end is None else time.time() >= end

    def clear(self, battle_id: int) -> None:
        self.deadlines.pop(battle_id, None)
