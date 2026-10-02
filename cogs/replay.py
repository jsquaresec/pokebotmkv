from core.game_gui import gui_send
import json
import discord
from discord import app_commands
from discord.ext import commands
from core.database import SessionLocal
from repositories.battle_replays import BattleReplayRepository

class ReplayCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="replay_view", description="View a replay summary by battle ID")
    async def replay_view(self, interaction: discord.Interaction, battle_id: int):
        async with SessionLocal() as session:
            repo = BattleReplayRepository(session)
            replay = await repo.get_by_battle_id(battle_id)
            if replay is None:
                await gui_send(interaction, "Replay not found.", ephemeral=True)
                return
            payload = json.loads(replay.replay_json)
            lines = payload.get("log", [])[-10:]
            await gui_send(interaction, f'Replay #{battle_id} | Winner Discord ID: {payload.get("winner_discord_id")}\n' + "\n".join(lines))

async def setup(bot: commands.Bot):
    await bot.add_cog(ReplayCog(bot))
