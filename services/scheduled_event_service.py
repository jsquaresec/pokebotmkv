from datetime import datetime

class ScheduledEventService:
    def __init__(self):
        self.events = []

    def schedule(self, code: str, start_iso: str, end_iso: str):
        event = {"code": code, "start": start_iso, "end": end_iso}
        self.events.append(event)
        return event

    def active_events(self, now_iso: str | None = None):
        now = datetime.fromisoformat(now_iso) if now_iso else datetime.utcnow()
        active = []
        for e in self.events:
            start = datetime.fromisoformat(e["start"])
            end = datetime.fromisoformat(e["end"])
            if start <= now <= end:
                active.append(e)
        return active

    def current_code(self, now_iso: str | None = None):
        active = self.active_events(now_iso)
        return active[0]["code"] if active else None
