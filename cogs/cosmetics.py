from core.game_gui import gui_send
import discord
from discord import app_commands
from discord.ext import commands
from core.database import SessionLocal
from repositories.cosmetics import CosmeticRepository
from services.cosmetic_service import CosmeticService

class CosmeticsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="cosmetics", description="Browse active cosmetics")
    async def cosmetics(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            rows = await CosmeticService(CosmeticRepository(session)).browse_active()
            if not rows:
                await gui_send(interaction, "No active cosmetics right now.", ephemeral=True)
                return
            lines = [f"#{x.id} {x.name} | {x.cosmetic_type} | {x.rarity}" for x in rows]
            await gui_send(interaction, "\n".join(lines))

async def setup(bot: commands.Bot):
    await bot.add_cog(CosmeticsCog(bot))
