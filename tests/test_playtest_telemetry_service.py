from services.playtest_telemetry_service import PlaytestTelemetryService

def run():
    svc = PlaytestTelemetryService()
    svc.record("catch", 1, {"species": "Pikachu"})
    svc.record("battle", 1, {"result": "win"})
    counts = svc.count_by_type()
    assert counts["catch"] == 1
    assert counts["battle"] == 1
    assert len(svc.recent()) == 2
    print("playtest telemetry service tests passed")

if __name__ == "__main__":
    run()
