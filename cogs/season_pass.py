from core.game_gui import gui_send
import discord
from discord import app_commands
from discord.ext import commands
from core.database import SessionLocal
from repositories.inventory import InventoryRepository
from repositories.users import UserRepository
from services.season_pass_service import SeasonPassService


class SeasonPassCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="season_pass", description="View seasonal progression")
    async def status(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            user = await UserRepository(session).get_by_discord_id(interaction.user.id)
        if not user:
            await gui_send(interaction, "Use `/start` first.", ephemeral=True)
            return
        tier = SeasonPassService.tier(user.season_xp)
        await gui_send(interaction, 
            f"Season XP: **{user.season_xp}** · Tier: **{tier}/5** · Next: **{(tier + 1) * 500 if tier < 5 else 'MAX'}**"
        )

    @app_commands.command(name="season_claim", description="Claim an unlocked seasonal reward")
    async def claim(self, interaction: discord.Interaction, tier: int):
        async with SessionLocal() as session:
            user = await UserRepository(session).get_by_discord_id(interaction.user.id)
            if not user:
                await gui_send(interaction, "Use `/start` first.", ephemeral=True)
                return
            try:
                async with session.begin_nested():
                    sku, quantity = await SeasonPassService(session, InventoryRepository(session)).claim(user, tier)
                await session.commit()
            except ValueError as exc:
                await gui_send(interaction, str(exc), ephemeral=True)
                return
        await gui_send(interaction, f"Claimed **{quantity}x {sku}** from tier {tier}.")


async def setup(bot):
    await bot.add_cog(SeasonPassCog(bot))
