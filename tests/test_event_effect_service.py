from services.event_effect_service import EventEffectService

def run():
    svc = EventEffectService()
    assert svc.xp_multiplier() == 1
    svc.set_flag("double_xp_weekend", True)
    assert svc.xp_multiplier() == 2
    svc.set_flag("rare_spawn_hour", True)
    assert svc.spawn_bias() == "uncommon"
    print("event effect service tests passed")

if __name__ == "__main__":
    run()
