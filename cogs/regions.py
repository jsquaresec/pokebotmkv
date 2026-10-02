from core.game_gui import gui_send
from core.choice_buttons import choose, reply
import discord
from discord.ext import commands
from discord import app_commands
from services.multi_region_content_registry_service import MultiRegionContentRegistryService

_REG = MultiRegionContentRegistryService()

class RegionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="region_summary")
    async def region_summary(self, interaction: discord.Interaction):
        counts = _REG.counts()
        lines = [f"{region.title()}: {count}" for region, count in counts.items()]
        lines.append(f"Total unique species loaded: {len(_REG.all_species())}")
        await gui_send(interaction, "\n".join(lines), ephemeral=True)

    @app_commands.command(name="region_pool")
    async def region_pool(self, interaction: discord.Interaction):
        await choose(interaction, "Choose a region.",
                     [(name.title(), name) for name in _REG.counts()], self.select_region)

    async def select_region(self, interaction, region):
        pool = _REG.region_pool(region)
        if not pool:
            await reply(interaction, f"No region pool found for {region}.", ephemeral=True)
            return
        preview = ", ".join(pool[:25])
        if len(pool) > 25:
            preview += ", ..."
        await reply(interaction, 
            f"{region.title()} pool ({len(pool)} species):\n{preview}",
            ephemeral=True,
        )

async def setup(bot):
    await bot.add_cog(RegionCog(bot))
