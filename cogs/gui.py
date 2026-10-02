import logging

import discord
from discord import app_commands
from discord.ext import commands
from core.game_gui import dashboard, gui_send


class GuiCog(commands.Cog):
    @app_commands.command(name="menu", description="Open the PokeBot graphical dashboard")
    async def menu(self, interaction: discord.Interaction):
        # dashboard() only inspects the in-memory command tree, so respond
        # directly. Deferring with thinking=True here can leave Discord's
        # "Bot is thinking..." placeholder behind when an older private panel
        # is being reused or was manually dismissed.
        interaction.extras["gui_force_new_panel"] = True
        await dashboard(interaction)

    @menu.error
    async def menu_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        logging.getLogger(__name__).error(
            "The /menu command failed",
            exc_info=(type(error), error, error.__traceback__),
        )
        try:
            await gui_send(
                interaction,
                "The menu could not be opened. Please try /menu again.",
                ephemeral=True,
            )
        except discord.HTTPException:
            logging.getLogger(__name__).exception("Could not send the /menu error response")


async def setup(bot):
    await bot.add_cog(GuiCog())
