from core.game_gui import gui_send
import discord
from discord.ext import commands
from discord import app_commands
from services.guild_service import GuildService

_GUILD = GuildService()

class GuildCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="guild_create")
    async def create(self, interaction: discord.Interaction, name: str):
        try:
            _GUILD.create_guild(interaction.user.id, name)
            await gui_send(interaction, f"Guild **{name}** created.")
        except Exception as e:
            await gui_send(interaction, str(e), ephemeral=True)

    @app_commands.command(name="guild_join")
    async def join(self, interaction: discord.Interaction, name: str):
        try:
            _GUILD.join_guild(interaction.user.id, name)
            await gui_send(interaction, f"Joined **{name}**.")
        except Exception as e:
            await gui_send(interaction, str(e), ephemeral=True)

    @app_commands.command(name="guild_leave")
    async def leave(self, interaction: discord.Interaction, name: str):
        try:
            _GUILD.leave_guild(interaction.user.id, name)
            await gui_send(interaction, f"Left **{name}**.")
        except Exception as e:
            await gui_send(interaction, str(e), ephemeral=True)

async def setup(bot):
    await bot.add_cog(GuildCog(bot))
