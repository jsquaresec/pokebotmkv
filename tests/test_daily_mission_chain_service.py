from services.daily_mission_chain_service import DailyMissionChainService

def run():
    svc = DailyMissionChainService()
    svc.advance(1, "catch_1", 1)
    summary = svc.summary(1)
    assert any(m["code"] == "catch_1" and m["complete"] for m in summary)
    print("daily mission chain service tests passed")

if __name__ == "__main__":
    run()
