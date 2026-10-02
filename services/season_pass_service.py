from sqlalchemy import select
from models.season_reward_claim import SeasonRewardClaim


SEASON_CODE = "launch_v80"
REWARDS = {1: ("poke_ball", 5), 2: ("great_ball", 3), 3: ("rare_candy", 1), 4: ("ultra_ball", 3), 5: ("master_ball", 1)}


class SeasonPassService:
    XP_PER_TIER = 500

    @classmethod
    def tier(cls, season_xp: int):
        return min(5, season_xp // cls.XP_PER_TIER)

    def __init__(self, session, inventory):
        self.session, self.inventory = session, inventory

    async def claim(self, user, tier: int):
        if tier not in REWARDS or self.tier(user.season_xp) < tier:
            raise ValueError("That reward tier is not unlocked.")
        existing = (
            await self.session.execute(
                select(SeasonRewardClaim).where(
                    SeasonRewardClaim.discord_id == user.discord_id,
                    SeasonRewardClaim.season_code == SEASON_CODE,
                    SeasonRewardClaim.tier == tier,
                )
            )
        ).scalar_one_or_none()
        if existing:
            raise ValueError("That tier was already claimed.")
        sku, quantity = REWARDS[tier]
        self.session.add(SeasonRewardClaim(discord_id=user.discord_id, season_code=SEASON_CODE, tier=tier))
        await self.inventory.add_item(user.discord_id, sku, quantity)
        await self.session.flush()
        return sku, quantity
