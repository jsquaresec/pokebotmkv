from services.scheduled_event_service import ScheduledEventService

def run():
    svc = ScheduledEventService()
    svc.schedule("double_rewards", "2026-04-01T00:00:00", "2026-12-31T23:59:59")
    active = svc.active_events("2026-06-01T12:00:00")
    assert len(active) == 1
    assert svc.current_code("2026-06-01T12:00:00") == "double_rewards"
    print("scheduled event service tests passed")

if __name__ == "__main__":
    run()
