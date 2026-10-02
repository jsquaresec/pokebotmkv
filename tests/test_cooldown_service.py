from services.cooldown_service import CooldownService

def run():
    svc = CooldownService()
    ok, _ = svc.check("buy", 1, 3)
    assert ok is True
    ok2, rem2 = svc.check("buy", 1, 3)
    assert ok2 is False
    assert rem2 >= 1
    svc.clear("buy", 1)
    ok3, _ = svc.check("buy", 1, 3)
    assert ok3 is True
    print("cooldown service tests passed")

if __name__ == "__main__":
    run()
