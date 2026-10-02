from datetime import datetime, timedelta

class SeasonService:
    def __init__(self):
        self.season_name = "Season Alpha"
        self.started_at = datetime.utcnow()
        self.ends_at = self.started_at + timedelta(days=30)

    def snapshot(self) -> dict:
        remaining = self.ends_at - datetime.utcnow()
        return {
            "season_name": self.season_name,
            "started_at": self.started_at.isoformat(),
            "ends_at": self.ends_at.isoformat(),
            "days_remaining": max(0, remaining.days),
        }

    def reward_for_tier(self, tier: str) -> dict:
        rewards = {
            "Bronze": {"coins": 200, "title": "Bronze Competitor"},
            "Silver": {"coins": 400, "title": "Silver Competitor"},
            "Gold": {"coins": 700, "title": "Gold Competitor"},
            "Elite": {"coins": 1200, "title": "Elite Competitor"},
        }
        return rewards.get(tier, rewards["Bronze"])
