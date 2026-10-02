from services.spawn_balance_service import SpawnBalanceService

def run():
    svc = SpawnBalanceService()
    weights = svc.get_weights()
    assert weights["common"] > weights["legendary"]
    updated = svc.set_weight("rare", 12)
    assert updated["rare"] == 12
    print("spawn balance service tests passed")

if __name__ == "__main__":
    run()
