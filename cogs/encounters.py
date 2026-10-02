from core.game_gui import gui_send, gui_defer
from core.choice_buttons import reply
from core.wild_battle_view import WildBattleView, SpawnLobbyView, battle_card
from services.wild_battle_service import WildBattleService, load_battle
from services.encounter_ui import encounter_card
from datetime import datetime
import asyncio
import logging
from collections import defaultdict
import random
import discord
from discord import app_commands
from discord.ext import commands, tasks
from config import settings
from core.database import SessionLocal
from repositories.inventory import InventoryRepository
from repositories.users import UserRepository
from repositories.wild_encounters import WildEncounterRepository
from services.encounter_v70_service import CATCH_GOLD_REWARD, EncounterV70Service


class EncounterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.activity = defaultdict(int)
        self.spawn_lock = asyncio.Lock()
        self.cleanup_expired.start()

    def cog_unload(self):
        self.cleanup_expired.cancel()

    @tasks.loop(seconds=15)
    async def cleanup_expired(self):
        async with SessionLocal() as session:
            async with session.begin():
                await WildBattleService.expire(session)

    @cleanup_expired.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()

    async def _spawn(self, channel, trainer_discord_id):
        async with self.spawn_lock:
            async with SessionLocal() as session:
                async with session.begin():
                    encounter = await EncounterV70Service(session).spawn(channel.guild.id, channel.id, trainer_discord_id)
                    view = SpawnLobbyView(encounter, self.open_encounter)
                    embed = encounter_card(encounter)
                    embed.set_field_at(2, name="Private battle controls", value="Click **Open private encounter** to use your own GUI.", inline=False)
                    message = await channel.send(
                        embed=embed,
                        view=view,
                    )
                    view.message = message
                    encounter.message_id = message.id

    def encounter_view(self, row, owner_id):
        return WildBattleView(row, self.battle_action, owner_id)

    async def battle_action(self, interaction, encounter_id, kind, value, turn):
        async with SessionLocal() as session:
            async with session.begin():
                row = await WildBattleService(session).apply(
                    encounter_id, interaction.channel_id, interaction.user.id, kind, value, turn)
        # A trainer finishing their private battle must not retire the public
        # spawn; other trainers can battle the same spawn independently.
        return row

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        self.activity[message.channel.id] += 1
        if self.activity[message.channel.id] >= settings.spawn_message_threshold:
            self.activity[message.channel.id] = 0
            try:
                await self._spawn(message.channel, message.author.id)
            except ValueError:
                pass  # An encounter is already active.
            except discord.HTTPException:
                logging.getLogger(__name__).exception("Could not announce wild encounter")

    @app_commands.command(name="spawn", description="Spawn a wild Pokémon in this channel")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def spawn(self, interaction: discord.Interaction):
        await gui_defer(interaction, ephemeral=True)
        try:
            await self._spawn(interaction.channel, interaction.user.id)
        except ValueError as exc:
            await gui_send(interaction, str(exc), ephemeral=True)
            return
        except discord.HTTPException:
            await gui_send(interaction, 
                "I couldn't post the spawn. Check my View Channel and Send Messages permissions.",
                ephemeral=True,
            )
            return
        self.activity[interaction.channel_id] = 0
        await gui_send(interaction, "A wild Pokémon has spawned!", ephemeral=True)

    @spawn.error
    async def spawn_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await gui_send(interaction, 
                "You need Manage Server permission to use /spawn.", ephemeral=True
            )
        else:
            raise error

    @app_commands.command(name="encounter", description="Show the active wild encounter")
    async def encounter(self, interaction: discord.Interaction):
        await gui_defer(interaction)
        await self.open_encounter(interaction)

    async def open_encounter(self, interaction, encounter_id=None):
        async with SessionLocal() as session:
            row = await WildEncounterRepository(session).active_in_channel(interaction.channel_id)
            if not row or (encounter_id is not None and row.id != encounter_id):
                await gui_send(interaction, "There is no active encounter here.", ephemeral=True)
                return
            view = self.encounter_view(row, interaction.user.id)
            message = await gui_send(interaction, 
                embed=battle_card(row, owner_id=interaction.user.id), view=view
            )
            view.message = message

    @app_commands.command(name="wild_attack", description="Weaken the active wild Pokémon")
    async def wild_attack(self, interaction: discord.Interaction):
        await self.encounter.callback(self, interaction)

    async def attack_encounter(self, interaction, encounter_id=None, notify=True):
        async with SessionLocal() as session:
            try:
                async with session.begin():
                    row = await EncounterV70Service(session).attack(interaction.channel_id, random.randint(4, 12), encounter_id)
            except ValueError as exc:
                if not notify:
                    raise
                await reply(interaction, str(exc), ephemeral=True)
                return
        if notify:
            await reply(interaction, f"You attacked **{row.species}**. HP: {row.current_hp}/{row.max_hp}")
        return row

    @app_commands.command(name="throw", description="Throw a Poké Ball at the active encounter")
    async def throw(self, interaction: discord.Interaction):
        await self.encounter.callback(self, interaction)

    async def throw_ball(self, interaction, ball, encounter_id=None, notify=True):
        async with SessionLocal() as session:
            try:
                async with session.begin():
                    mon = await EncounterV70Service(session).attempt_catch(
                        interaction.channel_id, interaction.user.id, ball,
                        UserRepository(session), InventoryRepository(session),
                        encounter_id=encounter_id,
                    )
            except ValueError as exc:
                if not notify:
                    raise
                await reply(interaction, str(exc), ephemeral=True)
                return
        if not notify:
            return mon
        if mon:
            await reply(interaction, 
                f"Caught **{mon.species}** (Lv. {mon.level}, {mon.iv_percent}% IV){' ✨' if mon.shiny else ''}!"
                f"\nYou earned **{CATCH_GOLD_REWARD} gold**!"
            )
        else:
            await reply(interaction, "The Pokémon broke free!")
        return mon


async def setup(bot):
    await bot.add_cog(EncounterCog(bot))
