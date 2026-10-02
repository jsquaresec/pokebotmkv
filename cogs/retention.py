from core.game_gui import gui_send, gui_defer
from core.choice_buttons import choose, reply
import discord
from discord.ext import commands
from discord import app_commands
from core.database import SessionLocal
from repositories.daily_rewards import DailyRewardRepository
from services.daily_reward_service import DailyRewardService







class RetentionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="daily_checkin", description="Claim daily gold and grow your streak")
    async def daily_checkin(self, interaction: discord.Interaction):
        await gui_defer(interaction)
        async with SessionLocal() as session:
            try:
                result = await DailyRewardService(DailyRewardRepository(session)).claim(interaction.user.id)
                await session.commit()
            except ValueError as exc:
                await gui_send(interaction, str(exc), ephemeral=True)
                return
        title = f"Claimed **{result['reward']:,} gold!**" if result['claimed'] else "You already claimed today's reward."
        await gui_send(interaction,
            f"{title}\n🔥 Streak: **{result['streak']} days**\n"
            f"💰 Balance: **{result['balance']:,} gold**\n"
            f"Next consecutive check-in: **{DailyRewardService.reward_for_streak(result['streak'] + 1):,} gold**\n"
            f"Available <t:{result['next_claim']}:R>.\n"
            "Check in every UTC day to keep your streak. Missing a day resets it to 1,000 gold. Daily rewards cap at 10,000 gold.",
            ephemeral=True)

    @app_commands.command(name="daily_missions", description="View daily missions and claim random item rewards")
    async def daily_missions(self, interaction: discord.Interaction):
        from core.daily_mission_view import show_missions
        await show_missions(interaction)

async def setup(bot):
    await bot.add_cog(RetentionCog(bot))



