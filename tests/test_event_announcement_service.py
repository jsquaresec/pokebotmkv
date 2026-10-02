from services.event_announcement_service import EventAnnouncementService

def run():
    svc = EventAnnouncementService()
    assert "started" in svc.start_message("double_rewards")
    assert "No live events" in svc.status_message([])
    print("event announcement service tests passed")

if __name__ == "__main__":
    run()
