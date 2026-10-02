from core.game_gui import gui_send
import discord
from discord import app_commands
from discord.ext import commands
from services.system_health_v80_service import SystemHealthV80Service


class SystemV80Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="game_status", description="Show PokeBot runtime status")
    async def status(self, interaction: discord.Interaction):
        data = SystemHealthV80Service.snapshot(self.bot)
        await gui_send(interaction, 
            f"PokeBot **v{data['version']}** · {data['status'].title()}\nSpecies: {data['species']} · Commands: {data['commands']} · Extensions: {data['extensions']} · Content errors: {data['content_errors']}"
        )

    @app_commands.command(name="game_guide", description="Show the main gameplay path")
    async def guide(self, interaction: discord.Interaction):
        await gui_send(interaction, 
            "Open **/menu** or click **Home** below.\n\n"
            "👤 **Trainer:** create your profile and choose a starter.\n"
            "🔴 **Catching:** weaken wild Pokémon and click a ball.\n"
            "🎒 **Pokémon & Party:** browse your collection and build a team.\n"
            "⚔️ **Battles & Ranked:** join the queue and choose moves.\n"
            "🛒 **Shop & Trading:** buy items, trade, or browse auctions.\n"
            "🎁 **Daily & Seasons:** check in and claim rewards.\n"
            "🤝 **Friends & Guilds:** connect with other trainers."
        )


async def setup(bot):
    await bot.add_cog(SystemV80Cog(bot))
