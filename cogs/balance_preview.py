from core.game_gui import gui_send
import discord
from core.choice_buttons import choose, reply
from discord.ext import commands
from discord import app_commands
from services.spawn_balance_service import SpawnBalanceService
from services.economy_balance_service import EconomyBalanceService
from services.battle_reward_scaler_service import BattleRewardScalerService

_SPAWN = SpawnBalanceService()
_ECON = EconomyBalanceService()
_SCALE = BattleRewardScalerService()

class BalancePreviewCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="balance_spawn_preview")
    async def balance_spawn_preview(self, interaction: discord.Interaction):
        weights = _SPAWN.get_weights()
        lines = [f"{k}: {v}" for k, v in weights.items()]
        await gui_send(interaction, "\n".join(lines), ephemeral=True)

    @app_commands.command(name="balance_economy_preview")
    async def balance_economy_preview(self, interaction: discord.Interaction):
        snap = _ECON.snapshot()
        lines = [f"{k}: {v}" for k, v in snap.items()]
        await gui_send(interaction, "\n".join(lines), ephemeral=True)

    @app_commands.command(name="balance_battle_preview")
    async def balance_battle_preview(self, interaction: discord.Interaction):
        await choose(interaction, "Choose a battle tier.",
                     [(tier, tier) for tier in ("Bronze", "Silver", "Gold", "Elite")], self.select_tier)

    async def select_tier(self, interaction, tier):
        scaled = _SCALE.scale(100, 200, tier)
        await reply(interaction,
            f"Tier: {tier}\nCoins: {scaled['coins']}\nXP: {scaled['xp']}",
            ephemeral=True,
        )

async def setup(bot):
    await bot.add_cog(BalancePreviewCog(bot))
