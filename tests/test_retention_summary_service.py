from services.retention_summary_service import RetentionSummaryService

def run():
    svc = RetentionSummaryService()
    text = svc.render({"streak": 3, "status": "checked_in"}, [{"code": "catch_1", "progress": 1, "target": 1, "complete": True}])
    assert "Login streak" in text
    assert "catch_1" in text
    print("retention summary service tests passed")

if __name__ == "__main__":
    run()
