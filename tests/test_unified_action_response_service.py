from services.unified_action_response_service import UnifiedActionResponseService

def run():
    svc = UnifiedActionResponseService()
    assert "✅" in svc.success("Ok", "Done")
    assert "Next" in svc.next_steps(["A", "B"])
    print("unified action response service tests passed")

if __name__ == "__main__":
    run()
