from core.game_gui import gui_send
import discord
from discord.ext import commands
from discord import app_commands
from services.playtest_telemetry_service import PlaytestTelemetryService
from services.runtime_status_service import RuntimeStatusService
from services.admin_playtest_service import AdminPlaytestService

_TELEMETRY = PlaytestTelemetryService()
_STATUS = RuntimeStatusService()
_ADMIN = AdminPlaytestService()

class AdminPlaytestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="playtest_status")
    async def playtest_status(self, interaction: discord.Interaction):
        await gui_send(interaction, _STATUS.render(), ephemeral=True)

    @app_commands.command(name="playtest_log")
    async def playtest_log(self, interaction: discord.Interaction, event_type: str):
        row = _TELEMETRY.record(event_type, interaction.user.id, {"source": "manual"})
        await gui_send(interaction, f"Logged event: {row['event_type']}", ephemeral=True)

    @app_commands.command(name="playtest_events")
    async def playtest_events(self, interaction: discord.Interaction):
        counts = _TELEMETRY.count_by_type()
        if not counts:
            await gui_send(interaction, "No playtest events logged yet.", ephemeral=True)
            return
        text = "\n".join(f"{k}: {v}" for k, v in counts.items())
        await gui_send(interaction, text, ephemeral=True)

    @app_commands.command(name="grant_test_currency")
    async def grant_test_currency(self, interaction: discord.Interaction, user_id: int, amount: int):
        row = _ADMIN.grant_test_currency(user_id, amount)
        _TELEMETRY.record("grant_test_currency", interaction.user.id, row)
        await gui_send(interaction, 
            f"Granted test currency: user {row['user_id']} amount {row['amount']}",
            ephemeral=True,
        )

    @app_commands.command(name="reset_test_user")
    async def reset_test_user(self, interaction: discord.Interaction, user_id: int):
        row = _ADMIN.reset_user_state(user_id)
        _TELEMETRY.record("reset_test_user", interaction.user.id, row)
        await gui_send(interaction, 
            f"Reset test state for user {row['user_id']}",
            ephemeral=True,
        )

async def setup(bot):
    await bot.add_cog(AdminPlaytestCog(bot))
