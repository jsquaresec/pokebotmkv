from services.event_spawn_service import EventSpawnService

def run():
    svc = EventSpawnService()
    assert svc.choose_rarity("common", "legendary_hour") == "legendary"
    assert svc.reward_multiplier("double_rewards") == 2.0
    print("event spawn service tests passed")

if __name__ == "__main__":
    run()
