from services.season_service import SeasonService

def run():
    svc = SeasonService()
    snap = svc.snapshot()
    assert "season_name" in snap
    reward = svc.reward_for_tier("Gold")
    assert reward["coins"] == 700
    print("season service tests passed")

if __name__ == "__main__":
    run()
