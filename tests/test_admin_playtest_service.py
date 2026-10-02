from services.admin_playtest_service import AdminPlaytestService

def run():
    svc = AdminPlaytestService()
    grant = svc.grant_test_currency(1001, 5000)
    reset = svc.reset_user_state(1001)
    assert grant["amount"] == 5000
    assert reset["status"] == "reset"
    print("admin playtest service tests passed")

if __name__ == "__main__":
    run()
