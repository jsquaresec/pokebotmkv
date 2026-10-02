import discord
from discord import app_commands
from discord.ext import commands
from core.game_gui import dashboard


class GuiCog(commands.Cog):
    @app_commands.command(name="menu", description="Open the PokeBot graphical dashboard")
    async def menu(self, interaction: discord.Interaction):
        await dashboard(interaction)


async def setup(bot):
    await bot.add_cog(GuiCog())
