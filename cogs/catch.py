from core.game_gui import gui_send
import discord
from discord.ext import commands
from discord import app_commands
from services.rarity_service import RarityService
from services.embed_factory import EmbedFactory
from services.reward_feedback_service import RewardFeedbackService

_CATCH_STREAKS = {}

class CatchCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rarity = RarityService()
        self.embed_factory = EmbedFactory()
        self.rewards = RewardFeedbackService()

    @app_commands.command(name="spawn_preview")
    async def spawn_preview(self, interaction: discord.Interaction):
        rarity = self.rarity.roll_rarity()
        style = self.rarity.style_for(rarity)
        msg = self.embed_factory.spawn_card("Bulbasaur", f'{style["emoji"]} {style["label"]}', 5)
        await gui_send(interaction, msg)

    @app_commands.command(name="catch_preview")
    async def catch_preview(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        _CATCH_STREAKS[user_id] = _CATCH_STREAKS.get(user_id, 0) + 1
        rarity = self.rarity.roll_rarity()
        rewards = self.rewards.catch_rewards(self.rarity.reward_multiplier(rarity), _CATCH_STREAKS[user_id] - 1)
        msg = self.embed_factory.catch_card("Pikachu", rarity, 7, rewards, ["Try /profile", "Try /battle", "Visit /shop"])
        await gui_send(interaction, msg)

async def setup(bot):
    await bot.add_cog(CatchCog(bot))
