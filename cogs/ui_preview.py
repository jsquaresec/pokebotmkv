from core.game_gui import gui_send
import discord
from discord.ext import commands
from discord import app_commands
from services.premium_embed_theme_service import PremiumEmbedThemeService
from services.battle_presentation_service import BattlePresentationService
from services.unified_action_response_service import UnifiedActionResponseService

_THEME = PremiumEmbedThemeService()
_BATTLE = BattlePresentationService()
_RESP = UnifiedActionResponseService()

class UIPreviewCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ui_profile_preview")
    async def ui_profile_preview(self, interaction: discord.Interaction):
        text = "\n".join([
            _THEME.title_block("Trainer Profile", "Premium Layout Preview"),
            _THEME.stat_line("Coins", "1250"),
            _THEME.stat_line("Tier", "Gold"),
            _THEME.stat_line("Prestige", "2"),
            "",
            _RESP.next_steps(["Try /battle_view", "Visit /market_quote", "Check /rotation_status"]),
        ])
        await gui_send(interaction, text, ephemeral=True)

    @app_commands.command(name="ui_battle_preview")
    async def ui_battle_preview(self, interaction: discord.Interaction):
        p1 = {"name": "Pikachu", "level": 12, "hp": 34, "max_hp": 50}
        p2 = {"name": "Charizard", "level": 18, "hp": 61, "max_hp": 80}
        await gui_send(interaction, _BATTLE.render_battle_card(p1, p2, 4, 18), ephemeral=True)

    @app_commands.command(name="ui_result_preview")
    async def ui_result_preview(self, interaction: discord.Interaction):
        msg = _RESP.success("Battle Complete", _BATTLE.render_result_card("Matthew", 250, 320, "✨ Shiny chain increased"))
        await gui_send(interaction, msg, ephemeral=True)

async def setup(bot):
    await bot.add_cog(UIPreviewCog(bot))
