import json
from repositories.reward_claims import RewardClaimRepository

class RewardService:
    def __init__(self, repo: RewardClaimRepository):
        self.repo = repo

    async def grant_battle_win(self, recipient_discord_id: int, battle_id: int, coins: int, xp: int):
        return await self.repo.create(
            recipient_discord_id=recipient_discord_id,
            reward_type="battle_win",
            amount=coins,
            related_battle_id=battle_id,
            details_json=json.dumps({"coins": coins, "xp": xp}),
        )

    async def recent(self, limit: int = 50):
        return await self.repo.latest(limit)
