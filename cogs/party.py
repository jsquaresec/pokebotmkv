from core.game_gui import gui_send, gui_defer
from core.party_builder import PartyBuilder
import discord
from discord import app_commands
from discord.ext import commands
from core.database import SessionLocal
from repositories.users import UserRepository
from repositories.pokemon import PokemonRepository
from repositories.party import PartyRepository

class PartyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="pokemon_center", description="Restore your whole party's HP and PP for 500 gold")
    async def pokemon_center(self, interaction: discord.Interaction):
        from core.choice_buttons import choose
        await choose(interaction,
            "🏥 **Pokémon Center**\nRestore every party Pokémon to full HP and PP, including fainted Pokémon.\n"
            "**Price: 500 gold total.** You cannot heal during battle.",
            [("Heal party — 500 gold", True), ("Cancel", False)], self.center_choice)

    async def center_choice(self, interaction, heal):
        if not heal:
            await gui_send(interaction, "Pokémon Center visit cancelled. No gold was charged.", ephemeral=True)
            return
        from services.pokemon_center_service import PokemonCenterService
        try:
            async with SessionLocal() as session:
                async with session.begin():
                    count, balance = await PokemonCenterService(session).heal_party(interaction.user.id)
        except ValueError as exc:
            await gui_send(interaction, str(exc), ephemeral=True)
            return
        receipt = discord.Embed(title="🏥 Your party is fully healed!",
            description=f"Restored **{count} Pokémon** to full HP and PP.", color=discord.Color.green())
        receipt.add_field(name="Gold spent", value="500 gold")
        receipt.add_field(name="Gold remaining", value=f"**{balance:,} gold**")
        await gui_send(interaction, embed=receipt, ephemeral=True)

    @app_commands.command(name="party_set", description="Build your party by clicking Pokémon")
    async def party_set(self, interaction: discord.Interaction):
        await gui_defer(interaction, ephemeral=True, thinking=True)
        async with SessionLocal() as session:
            user = await UserRepository(session).get_by_discord_id(interaction.user.id)
            if user is None:
                await gui_send(interaction, "Use `/start` first.", ephemeral=True)
                return
            mons = await PokemonRepository(session).get_by_owner(user.id)
            available = sorted((mon for mon in mons if not mon.locked), key=lambda mon: mon.id)
            if not available:
                await gui_send(interaction, "You have no available Pokémon. Catch one or choose a starter first.", ephemeral=True)
                return
            slots = await PartyRepository(session).get_party(user.id)
        view = PartyBuilder(interaction.user.id, available, [slot.pokemon_id for slot in slots], self.save_party)
        await gui_send(interaction, embed=view.embed(), view=view, ephemeral=True)

    async def save_party(self, interaction, ids):
        try:
            if len(ids) > 6 or len(ids) != len(set(ids)):
                raise ValueError("Choose up to six different Pokémon.")
            async with SessionLocal() as session:
                async with session.begin():
                    user = await UserRepository(session).get_by_discord_id_locked(interaction.user.id)
                    if not user:
                        raise ValueError("Use /start first.")
                    from sqlalchemy import select
                    from models.pokemon import PokemonInstance
                    from models.party import PartySlot
                    busy = (await session.execute(select(PokemonInstance.id).join(
                        PartySlot, PartySlot.pokemon_id == PokemonInstance.id).where(
                        PartySlot.owner_id == user.id, PokemonInstance.locked.is_(True)).limit(1))).scalar_one_or_none()
                    if busy is not None:
                        raise ValueError("Finish your wild battle before changing your party.")
                    repo = PokemonRepository(session)
                    for pid in sorted(ids):
                        mon = await repo.get_by_id_locked(pid)
                        if not mon or mon.owner_id != user.id or mon.locked:
                            raise ValueError(f"Pokémon #{pid} is no longer available. Remove it or reopen /party_set.")
                    await PartyRepository(session).replace_party(user.id, ids)
        except ValueError as exc:
            await gui_send(interaction, str(exc), ephemeral=True)
            return False
        await gui_send(interaction, f"Party saved with {len(ids)} Pokémon!", ephemeral=True)
        return True

    @app_commands.command(name="party_view", description="View your active party")
    async def party_view(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            user_repo = UserRepository(session)
            party_repo = PartyRepository(session)
            pokemon_repo = PokemonRepository(session)
            user = await user_repo.get_by_discord_id(interaction.user.id)
            if user is None:
                await gui_send(interaction, "Use `/start` first.", ephemeral=True)
                return

            slots = await party_repo.get_party(user.id)
            if not slots:
                await gui_send(interaction, "Your party is empty.", ephemeral=True)
                return

            lines = []
            for slot in slots:
                mon = await pokemon_repo.get_by_id(slot.pokemon_id)
                if mon is not None:
                    lines.append(f"Slot {slot.slot_index}: #{mon.id} {mon.species} Lv.{mon.level}")
            await gui_send(interaction, "\n".join(lines))

async def setup(bot: commands.Bot):
    await bot.add_cog(PartyCog(bot))
