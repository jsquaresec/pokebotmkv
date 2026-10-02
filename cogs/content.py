from core.game_gui import gui_send
import discord
from discord.ext import commands
from discord import app_commands
from services.pokemon_content_registry_service import PokemonContentRegistryService
from services.pokemon_variation_service import PokemonVariationService
from services.featured_rotation_service import FeaturedRotationService
from services.mass_spawn_pool_service import MassSpawnPoolService
from services.content_rotation_announcement_service import ContentRotationAnnouncementService

_REG = PokemonContentRegistryService()
_VAR = PokemonVariationService()
_ROT = FeaturedRotationService()
_POOL = MassSpawnPoolService()
_ANN = ContentRotationAnnouncementService()

class ContentCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="pokedex_summary")
    async def pokedex_summary(self, interaction: discord.Interaction):
        total_species = len(_REG.all_species())
        total_forms = _REG.total_forms()
        await gui_send(interaction, 
            f"Species loaded: **{total_species}**\nForms loaded: **{total_forms}**\nVariants enabled: **Shiny / Alpha / Shadow / Radiant**",
            ephemeral=True,
        )

    @app_commands.command(name="pokemon_forms")
    async def pokemon_forms(self, interaction: discord.Interaction, species: str):
        forms = _REG.forms_for(species)
        if not forms:
            await gui_send(interaction, f"No special forms registered for {species}.", ephemeral=True)
            return
        await gui_send(interaction, f"{species} forms: " + ", ".join(forms), ephemeral=True)

    @app_commands.command(name="rotation_status")
    async def rotation_status(self, interaction: discord.Interaction):
        key = _ROT.current_rotation_key()
        pool = _ROT.current_pool()
        await gui_send(interaction, _ANN.rotation_message(key, pool), ephemeral=True)

    @app_commands.command(name="spawn_mass_preview")
    async def spawn_mass_preview(self, interaction: discord.Interaction):
        species = _POOL.random_species()
        form = _VAR.random_form(species)
        display = _VAR.build_display_name(species, form=form, shiny=True)
        await gui_send(interaction, _ANN.variant_message(display))

async def setup(bot):
    await bot.add_cog(ContentCog(bot))
