from services.login_streak_service import LoginStreakService

def run():
    svc = LoginStreakService()
    one = svc.check_in(1, "2026-04-23T10:00:00")
    assert one["streak"] == 1
    two = svc.check_in(1, "2026-04-24T10:00:00")
    assert two["streak"] == 2
    print("login streak service tests passed")

if __name__ == "__main__":
    run()
