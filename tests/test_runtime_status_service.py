from services.runtime_status_service import RuntimeStatusService

def run():
    svc = RuntimeStatusService()
    snap = svc.snapshot()
    assert snap["bot_status"] == "ready"
    text = svc.render()
    assert "api_status" in text
    print("runtime status service tests passed")

if __name__ == "__main__":
    run()
