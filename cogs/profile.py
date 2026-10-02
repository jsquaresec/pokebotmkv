from core.game_gui import gui_send
from core.choice_buttons import choose, reply
import discord
from discord import app_commands
from discord.ext import commands
from core.database import SessionLocal
from repositories.users import UserRepository
from repositories.ranked_profiles import RankedProfileRepository
from repositories.pokemon import PokemonRepository
from services.user_service import UserService
from services.species_service import SpeciesService
from services.pokemon_service import PokemonService

STARTERS = {"Bulbasaur", "Charmander", "Squirtle"}

class ProfileCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="start", description="Create your trainer profile")
    async def start(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            user_repo = UserRepository(session)
            ranked_repo = RankedProfileRepository(session)
            service = UserService(user_repo, ranked_repo)
            user = await service.get_or_create_user(interaction.user.id, str(interaction.user))
            await gui_send(interaction, f"Trainer profile ready for **{user.username}**. Balance: **{user.balance}**")

    @app_commands.command(name="choose_starter", description="Choose your starter Pokémon")
    async def choose_starter(self, interaction: discord.Interaction):
        await choose(interaction, "Choose your starter Pokémon.",
                     [(name, name) for name in sorted(STARTERS)], self.select_starter)

    async def select_starter(self, interaction, starter):
        starter = starter.strip().title()
        if starter not in STARTERS:
            await reply(interaction, "Starter must be Bulbasaur, Charmander, or Squirtle.", ephemeral=True)
            return
        async with SessionLocal() as session:
            user_repo = UserRepository(session)
            ranked_repo = RankedProfileRepository(session)
            pokemon_repo = PokemonRepository(session)
            user_service = UserService(user_repo, ranked_repo)
            species_service = SpeciesService()
            pokemon_service = PokemonService(pokemon_repo, species_service)

            user = await user_service.get_or_create_user(interaction.user.id, str(interaction.user))
            existing = await pokemon_repo.get_by_owner(user.id)
            if existing:
                await reply(interaction, "You already have Pokémon. Starter can only be chosen once.", ephemeral=True)
                return

            mon = await pokemon_service.create_pokemon(user.id, starter, level=5)
            await reply(interaction, f"You chose **{mon.species}** as your starter!")

    @app_commands.command(name="profile", description="View your trainer profile")
    async def profile(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_discord_id(interaction.user.id)
            if user is None:
                await gui_send(interaction, "Use `/start` first.", ephemeral=True)
                return
            embed = discord.Embed(title=f"{interaction.user.display_name}'s Trainer Profile", color=0x5865F2)
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.add_field(name="Balance", value=str(user.balance), inline=True)
            embed.add_field(name="Trainer Level", value=str(user.trainer_level), inline=True)
            embed.add_field(name="Trainer XP", value=str(user.trainer_xp), inline=True)
            embed.add_field(name="Season XP", value=str(user.season_xp), inline=True)
            embed.add_field(name="Title", value=user.selected_title, inline=True)
            embed.description = user.bio or "No trainer bio set."
            await gui_send(interaction, embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(ProfileCog(bot))
