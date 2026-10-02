from core.game_gui import gui_send
import discord
from discord import app_commands
from discord.ext import commands
from core.maintenance import maintenance_mode_enabled

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="admin_maintenance", description="View maintenance mode state")
    async def admin_maintenance(self, interaction: discord.Interaction):
        await gui_send(interaction, f"Maintenance mode: {maintenance_mode_enabled()}")

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
