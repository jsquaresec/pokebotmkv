from services.economy_balance_service import EconomyBalanceService

def run():
    svc = EconomyBalanceService()
    snap = svc.snapshot()
    assert "base_catch_coins" in snap
    updated = svc.set_value("base_battle_win_coins", 140)
    assert updated["base_battle_win_coins"] == 140
    print("economy balance service tests passed")

if __name__ == "__main__":
    run()
