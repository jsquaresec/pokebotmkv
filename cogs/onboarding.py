from core.game_gui import gui_send
import discord
from discord.ext import commands
from discord import app_commands
from services.onboarding_guide_service import OnboardingGuideService
from services.response_formatter_service import ResponseFormatterService

_GUIDE = OnboardingGuideService()
_FMT = ResponseFormatterService()

class OnboardingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="start_game")
    async def start_game(self, interaction: discord.Interaction):
        body = "Open **/menu** to begin your adventure.\n\n" + _GUIDE.quick_start() + "\n\nUse Home below to explore Trainer, Catching, and Shop & Trading."
        await gui_send(interaction, _FMT.section("Welcome to PokeBot", body), ephemeral=True)

    @app_commands.command(name="help_game")
    async def help_game(self, interaction: discord.Interaction):
        tips = _FMT.bullet_lines(_GUIDE.beginner_tips())
        text = _FMT.section("Quick Start", _GUIDE.quick_start()) + "\n\n" + _FMT.section("Beginner Tips", tips)
        await gui_send(interaction, text, ephemeral=True)

async def setup(bot):
    await bot.add_cog(OnboardingCog(bot))
