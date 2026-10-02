from core.game_gui import gui_send, gui_defer
from core.choice_buttons import choose, reply
import discord
from discord import app_commands
from discord.ext import commands
from core.database import SessionLocal
from repositories.achievements import AchievementRepository
from repositories.inventory import InventoryRepository
from repositories.pokedex import PokedexRepository
from repositories.pokemon import PokemonRepository
from repositories.users import UserRepository
from services.achievement_service import ACHIEVEMENTS, AchievementService
from services.content_registry_v70 import ContentRegistryV70
from services.item_action_service import ItemActionService
from services.moveset_v80_service import MovesetV80Service
from services.progression_v70_service import ProgressionV70Service


class TrainerV80Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="pokedex", description="View your Pokédex completion")
    async def pokedex(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            summary = await PokedexRepository(session).summary(interaction.user.id)
            user = await UserRepository(session).get_by_discord_id(interaction.user.id)
            if user:
                async with session.begin_nested():
                    earned = await AchievementService(session).evaluate(interaction.user.id, summary["species_seen"], summary["total_catches"], user.balance)
                await session.commit()
            else:
                earned = []
        suffix = f"\nNew achievements: {', '.join(earned)}" if earned else ""
        await gui_send(interaction, 
            f"Species caught: **{summary['species_seen']}/1025** · Total catches: **{summary['total_catches']}**{suffix}"
        )

    @app_commands.command(name="achievements", description="View unlocked achievements")
    async def achievements(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            rows = await AchievementRepository(session).list_for(interaction.user.id)
        names = [ACHIEVEMENTS.get(row.code, row.code) for row in rows]
        await gui_send(interaction, " · ".join(names) or "No achievements unlocked yet.", ephemeral=not bool(names))

    @app_commands.command(name="profile_edit", description="Update your trainer bio")
    async def profile_edit(self, interaction: discord.Interaction, bio: str):
        if len(bio) > 240:
            await gui_send(interaction, "Bio must be 240 characters or fewer.", ephemeral=True)
            return
        async with SessionLocal() as session:
            user = await UserRepository(session).get_by_discord_id(interaction.user.id)
            if not user:
                await gui_send(interaction, "Use `/start` first.", ephemeral=True)
                return
            user.bio = bio
            await session.commit()
        await gui_send(interaction, "Trainer bio updated.", ephemeral=True)

    @app_commands.command(name="item_use", description="Use an item on one of your Pokémon")
    async def item_use(self, interaction: discord.Interaction, pokemon_id: int):
        async def use(click, sku):
            await self.use_item(click, pokemon_id, sku)

        await choose(interaction, "Choose an item to use on your Pokémon.",
                     [(name.replace("_", " ").title(), name)
                      for name in (*ItemActionService.HEALING, "rare_candy", "ether")], use)

    async def use_item(self, interaction, pokemon_id, sku):
        async with SessionLocal() as session:
            user = await UserRepository(session).get_by_discord_id(interaction.user.id)
            if not user:
                await reply(interaction, "Use `/start` first.", ephemeral=True)
                return
            try:
                async with session.begin_nested():
                    mon, result = await ItemActionService(session, InventoryRepository(session), PokemonRepository(session)).use(
                        interaction.user.id, user.id, pokemon_id, sku
                    )
                await session.commit()
            except ValueError as exc:
                await reply(interaction, str(exc), ephemeral=True)
                return
        await reply(interaction, f"**{mon.display_name}** {result}.")

    @app_commands.command(name="pokemon_evolve", description="Evolve an eligible Pokémon")
    async def evolve(self, interaction: discord.Interaction, pokemon_id: int):
        async with SessionLocal() as session:
            user = await UserRepository(session).get_by_discord_id(interaction.user.id)
            mon = await PokemonRepository(session).get_by_id_locked(pokemon_id)
            if not user or not mon or mon.owner_id != user.id or mon.locked:
                await gui_send(interaction, "That Pokémon is unavailable.", ephemeral=True)
                return
            old = mon.species
            try:
                ProgressionV70Service().evolve(mon, ContentRegistryV70())
                await session.commit()
            except ValueError as exc:
                await gui_send(interaction, str(exc), ephemeral=True)
                return
        await gui_send(interaction, f"Your **{old}** evolved into **{mon.species}**!")

    @app_commands.command(name="move_learn", description="Teach a legal move to your Pokémon")
    async def move_learn(self, interaction: discord.Interaction, pokemon_id: int):
        await gui_defer(interaction, ephemeral=True, thinking=True)
        async with SessionLocal() as session:
            user = await UserRepository(session).get_by_discord_id(interaction.user.id)
            mon = await PokemonRepository(session).get_by_id(pokemon_id)
            if not user or not mon or mon.owner_id != user.id or mon.locked:
                await reply(interaction, "That Pokémon is unavailable.", ephemeral=True)
                return
            slots = MovesetV80Service.load(mon)
            known = {slot["name"] for slot in slots}
            moves = [name for name in ContentRegistryV70().legal_moves(mon.species, mon.level) if name not in known]

        async def learn(click, move):
            if len(slots) < 4:
                await self.learn_move(click, pokemon_id, move, None)
            else:
                async def replace(selection, slot):
                    await self.learn_move(selection, pokemon_id, move, slot, slots)
                await choose(click, "Choose the move to replace.",
                             [(f'Replace {i + 1}: {slot["name"]}', i + 1) for i, slot in enumerate(slots)], replace)

        await choose(interaction, "Choose a move to learn. Only moves supported by the battle engine are shown.", [(name, name) for name in moves], learn)

    async def learn_move(self, interaction, pokemon_id, move, replace_slot, expected_slots=None):
        async with SessionLocal() as session:
            user = await UserRepository(session).get_by_discord_id(interaction.user.id)
            mon = await PokemonRepository(session).get_by_id_locked(pokemon_id)
            if not user or not mon or mon.owner_id != user.id or mon.locked:
                await reply(interaction, "That Pokémon is unavailable.", ephemeral=True)
                return
            if expected_slots is not None and MovesetV80Service.load(mon) != expected_slots:
                await reply(interaction, "The moveset changed. Open /move_learn again.", ephemeral=True)
                return
            try:
                slots = MovesetV80Service().learn(mon, move, ContentRegistryV70(), replace_slot)
                await session.commit()
            except ValueError as exc:
                await reply(interaction, str(exc), ephemeral=True)
                return
        await reply(interaction, "Moves: " + ", ".join(x["name"] for x in slots))


async def setup(bot):
    await bot.add_cog(TrainerV80Cog(bot))
