from core.game_gui import gui_send
import json
import discord
from discord import app_commands
from discord.ext import commands
from core.database import SessionLocal
from repositories.active_battles import ActiveBattleRepository
from repositories.audit_logs import AuditLogRepository
from services.battle_recovery_service import BattleRecoveryService
from services.startup_recovery_service import StartupRecoveryService
from services.battle_cleanup_service import BattleCleanupService
from services.audit_service import AuditService

class AdminDebugCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.recovery = BattleRecoveryService()
        self.startup_recovery = StartupRecoveryService()
        self.cleanup = BattleCleanupService()

    @app_commands.command(name="debug_active_battle", description="Debug: show your current active battle summary")
    async def debug_active_battle(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            repo = ActiveBattleRepository(session)
            battle = await repo.get_for_user(interaction.user.id)
            if battle is None:
                await gui_send(interaction, "No active battle found.", ephemeral=True)
                return
            summary = self.recovery.summarize(battle)
            lines = [f"{k}: {v}" for k, v in summary.items()]
            await gui_send(interaction, "\n".join(lines), ephemeral=True)

    @app_commands.command(name="debug_battle_state", description="Debug: show raw JSON state for a battle ID")
    async def debug_battle_state(self, interaction: discord.Interaction, battle_id: int):
        async with SessionLocal() as session:
            repo = ActiveBattleRepository(session)
            battle = await repo.get_by_id(battle_id)
            if battle is None:
                await gui_send(interaction, "Battle not found.", ephemeral=True)
                return
            state = self.recovery.parse_state(battle.state_json)
            pretty = json.dumps(state, indent=2)
            if len(pretty) > 1800:
                pretty = pretty[:1800] + "\n...truncated..."
            await gui_send(interaction, f"```json\n{pretty}\n```", ephemeral=True)

    @app_commands.command(name="debug_list_active_battles", description="Debug: list unfinished battles")
    async def debug_list_active_battles(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            rows = await self.startup_recovery.scan_active_battles(session)
            if not rows:
                await gui_send(interaction, "No unfinished battles.", ephemeral=True)
                return
            lines = []
            for row in rows[:10]:
                lines.append(str(row))
            await gui_send(interaction, "\n".join(lines), ephemeral=True)

    @app_commands.command(name="debug_cleanup_finished_battle", description="Debug: delete a finished battle by ID")
    async def debug_cleanup_finished_battle(self, interaction: discord.Interaction, battle_id: int):
        async with SessionLocal() as session:
            repo = ActiveBattleRepository(session)
            audit = AuditService(AuditLogRepository(session))
            battle = await repo.get_by_id(battle_id)
            if battle is None:
                await gui_send(interaction, "Battle not found.", ephemeral=True)
                return
            try:
                await self.cleanup.delete_finished(session, battle)
            except ValueError as exc:
                await gui_send(interaction, str(exc), ephemeral=True)
                return
            await audit.log("battle_cleanup_deleted", interaction.user.id, battle_id, "finished battle deleted")
            await gui_send(interaction, f"Finished battle #{battle_id} deleted.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminDebugCog(bot))
