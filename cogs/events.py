from core.game_gui import gui_send
import discord
from discord.ext import commands
from discord import app_commands
from services.scheduled_event_service import ScheduledEventService
from services.event_announcement_service import EventAnnouncementService

_EVENTS = ScheduledEventService()
_ANN = EventAnnouncementService()

class EventCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="event_schedule")
    async def event_schedule(self, interaction: discord.Interaction, code: str, start_iso: str, end_iso: str):
        event = _EVENTS.schedule(code, start_iso, end_iso)
        await gui_send(interaction, _ANN.start_message(event["code"]), ephemeral=True)

    @app_commands.command(name="event_status")
    async def event_status(self, interaction: discord.Interaction):
        active = [e["code"] for e in _EVENTS.active_events()]
        await gui_send(interaction, _ANN.status_message(active), ephemeral=True)

async def setup(bot):
    await bot.add_cog(EventCog(bot))
