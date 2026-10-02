from core.game_gui import gui_send
import discord
from discord import app_commands
from discord.ext import commands
from core.database import SessionLocal
from services.social_service import SocialService


class SocialCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="friend_add", description="Send a friend request")
    async def add(self, interaction: discord.Interaction, user: discord.User):
        async with SessionLocal() as session:
            try:
                async with session.begin():
                    row = await SocialService(session).request(interaction.user.id, user.id)
            except ValueError as exc:
                await gui_send(interaction, str(exc), ephemeral=True)
                return
        await gui_send(interaction, f"Friend request #{row.id} sent to {user.mention}.")

    @app_commands.command(name="friend_accept", description="Accept a friend request")
    async def accept(self, interaction: discord.Interaction, request_id: int):
        async with SessionLocal() as session:
            try:
                async with session.begin():
                    await SocialService(session).accept(interaction.user.id, request_id)
            except ValueError as exc:
                await gui_send(interaction, str(exc), ephemeral=True)
                return
        await gui_send(interaction, "Friend request accepted.")

    @app_commands.command(name="friends", description="List your friends")
    async def friends(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            ids = await SocialService(session).list_friends(interaction.user.id)
        await gui_send(interaction, 
            " · ".join(f"<@{x}>" for x in ids) or "No friends yet.", ephemeral=not bool(ids)
        )


async def setup(bot):
    await bot.add_cog(SocialCog(bot))
