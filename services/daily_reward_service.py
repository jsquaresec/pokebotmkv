from datetime import datetime, timedelta, timezone
from repositories.daily_rewards import DailyRewardRepository
from repositories.users import UserRepository


class DailyRewardService:
    @staticmethod
    def reward_for_streak(streak):
        return min(10000, 1000 + (max(1, streak) - 1) * 100)

    def __init__(self, repo: DailyRewardRepository):
        self.repo = repo

    async def claim(self, discord_id: int, now=None):
        """Lock the trainer; caller commits the claim and gold together."""
        user = await UserRepository(self.repo.session).get_by_discord_id_locked(discord_id)
        if user is None:
            raise ValueError("Use /start first to create your trainer.")
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is not None:
            now = now.astimezone(timezone.utc).replace(tzinfo=None)
        latest = await self.repo.latest_for_user(discord_id)
        next_claim = datetime.combine(now.date() + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
        if latest is not None and latest.created_at.date() >= now.date():
            return dict(claimed=False, reward=0, streak=latest.streak_count,
                        balance=user.balance, next_claim=int(next_claim.timestamp()))
        streak = latest.streak_count + 1 if latest and latest.created_at.date() == now.date() - timedelta(days=1) else 1
        reward = self.reward_for_streak(streak)
        await self.repo.create(discord_id, streak, created_at=now)
        user.balance += reward
        await self.repo.session.flush()
        return dict(claimed=True, reward=reward, streak=streak,
                    balance=user.balance, next_claim=int(next_claim.timestamp()))

