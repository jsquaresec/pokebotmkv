from services.battle_timer_service import BattleTimerService

def run():
    svc = BattleTimerService()
    svc.start_turn(1, 30)
    assert svc.remaining(1) >= 0
    assert svc.expired(1) is False
    svc.clear(1)
    assert svc.remaining(1) == 0
    print("battle timer service tests passed")

if __name__ == "__main__":
    run()
