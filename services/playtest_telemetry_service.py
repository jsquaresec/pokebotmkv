from datetime import datetime

class PlaytestTelemetryService:
    def __init__(self):
        self.events = []

    def record(self, event_type: str, user_id: int | None = None, details: dict | None = None):
        row = {
            "event_type": event_type,
            "user_id": user_id,
            "details": details or {},
            "created_at": datetime.utcnow().isoformat(),
        }
        self.events.append(row)
        return row

    def recent(self, limit: int = 25):
        return list(self.events[-limit:])

    def count_by_type(self) -> dict:
        counts = {}
        for row in self.events:
            counts[row["event_type"]] = counts.get(row["event_type"], 0) + 1
        return counts
