from core.game_gui import gui_send
import discord
from discord import app_commands
from discord.ext import commands
from core.database import SessionLocal
from repositories.live_events import LiveEventRepository
from services.live_event_service import LiveEventService

class LiveEventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="live_events", description="View active live events")
    async def live_events(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            rows = await LiveEventService(LiveEventRepository(session)).list_active()
            if not rows:
                await gui_send(interaction, "No active live events right now.", ephemeral=True)
                return
            lines = [f"#{x.id} {x.name} | {x.event_type}" for x in rows]
            await gui_send(interaction, "\n".join(lines))

async def setup(bot: commands.Bot):
    await bot.add_cog(LiveEventsCog(bot))
