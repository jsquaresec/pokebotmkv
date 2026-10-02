from datetime import datetime, timedelta

class LoginStreakService:
    def __init__(self):
        self.last_seen = {}
        self.streaks = {}

    def check_in(self, user_id: int, now_iso: str | None = None):
        now = datetime.fromisoformat(now_iso) if now_iso else datetime.utcnow()
        last = self.last_seen.get(user_id)
        streak = self.streaks.get(user_id, 0)

        if last is None:
            streak = 1
        else:
            delta = now - last
            if delta < timedelta(hours=20):
                return {"streak": streak, "status": "already_checked_in"}
            if delta <= timedelta(hours=48):
                streak += 1
            else:
                streak = 1

        self.last_seen[user_id] = now
        self.streaks[user_id] = streak
        return {"streak": streak, "status": "checked_in"}
