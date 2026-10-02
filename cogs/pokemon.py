from core.game_gui import gui_send, gui_defer, ResultView
import discord
from core.choice_buttons import choose, reply
from discord import app_commands
from discord.ext import commands
from core.database import SessionLocal
from repositories.users import UserRepository
from repositories.pokemon import PokemonRepository
from services.moveset_v80_service import MovesetV80Service
from services.encounter_ui import artwork


class PokemonCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="pc", description="View your Pokémon and their current HP")
    async def pc(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            user_repo = UserRepository(session)
            pokemon_repo = PokemonRepository(session)
            user = await user_repo.get_by_discord_id(interaction.user.id)
            if user is None:
                await gui_send(interaction, "Use `/start` first.", ephemeral=True)
                return

            mons = await pokemon_repo.get_by_owner(user.id)
            if not mons:
                await gui_send(interaction, "You do not have any Pokémon yet.", ephemeral=True)
                return

            lines = []
            for mon in sorted(mons, key=lambda mon: mon.id):
                shiny = " ✨" if mon.shiny else ""
                ratio = max(0, min(1, mon.current_hp / max(1, mon.max_hp)))
                filled = max(1 if ratio else 0, round(ratio * 10))
                indicator = "🟢" if ratio > .5 else "🟡" if ratio > .2 else "🔴"
                status = " · **Fainted**" if mon.current_hp <= 0 else ""
                name = discord.utils.escape_markdown(mon.display_name)
                lines.append(f"**#{mon.id} {name}{shiny}** · Lv.{mon.level}\n"
                             f"{indicator} **HP: {mon.current_hp}/{mon.max_hp}**{status}\n"
                             f"`{'█' * filled}{'░' * (10 - filled)}`")
            pages = ["\n\n".join(lines[i:i + 10]) for i in range(0, len(lines), 10)]
            view = ResultView(interaction.user.id, pages, f"Your PC · {len(mons)} Pokémon")
            await gui_send(interaction, embed=view.embed(), view=view)

    @app_commands.command(name="pokemon_info", description="Inspect one of your Pokémon")
    async def pokemon_info(self, interaction: discord.Interaction):
        await gui_defer(interaction, ephemeral=True, thinking=True)
        async with SessionLocal() as session:
            user = await UserRepository(session).get_by_discord_id(interaction.user.id)
            if not user:
                await gui_send(interaction, "Use `/start` first.", ephemeral=True)
                return
            mons = await PokemonRepository(session).get_by_owner(user.id)
            if not mons:
                await gui_send(interaction, "You do not have any Pokémon yet. Choose a starter or catch one first.", ephemeral=True)
                return
            options = [(f'{"✨ " if mon.shiny else ""}{mon.display_name} · Lv.{mon.level} · #{mon.id}', mon.id)
                       for mon in sorted(mons, key=lambda mon: mon.id)]
        await choose(interaction, "Choose a Pokémon to inspect.", options, self.show_pokemon_info)

    async def show_pokemon_info(self, interaction, pokemon_id):
        async with SessionLocal() as session:
            user = await UserRepository(session).get_by_discord_id(interaction.user.id)
            mon = await PokemonRepository(session).get_by_id(pokemon_id)
            if not user or not mon or mon.owner_id != user.id:
                await gui_send(interaction, "You do not own that Pokémon.", ephemeral=True)
                return
            moves = MovesetV80Service.load(mon)
            move_text = ", ".join(f"{m['name']} ({m['pp']}/{m['max_pp']})" for m in moves) or "None"
            embed = discord.Embed(
                title=f"{'✨ ' if mon.shiny else ''}{mon.display_name}",
                description=f"{mon.species} · Level {mon.level}",
                color=0xF1C40F if mon.shiny else 0x5865F2,
            )
            artwork(embed, mon.species, shiny=mon.shiny, full_size=True)
            embed.add_field(name="Type", value=f"{mon.primary_type.title()} / {mon.secondary_type.title() if mon.secondary_type else '—'}")
            embed.add_field(name="Health", value=f"{mon.current_hp}/{mon.max_hp} HP")
            embed.add_field(name="IV", value=f"{mon.iv_percent}%")
            embed.add_field(name="Nature", value=mon.nature)
            embed.add_field(name="Ability", value=mon.ability)
            embed.add_field(name="Gender", value=mon.gender.title())
            embed.add_field(name="Moves", value=move_text, inline=False)
            from services.content_registry_v70 import ContentRegistryV70
            data = ContentRegistryV70().species(mon.species)
            if data:
                embed.add_field(name="Pokédex", value=f'#{data["dex_number"]:04d}')
                embed.add_field(name="Stats", value=f'Attack {mon.attack} · Defense {mon.defense} · Speed {mon.speed}', inline=False)
                if data.get('evolves_to'):
                    evolution = f'{data["evolves_to"]} at level {data["evolution_level"]} — use Pokémon Evolve.'
                elif data.get('evolutions'):
                    evolution = ' / '.join(dict.fromkeys(e['target'] for e in data['evolutions'])) + '\nRequires a special evolution method; not currently available in this bot.'
                else:
                    evolution = 'Final stage — no further evolution.'
                embed.add_field(name="Evolution", value=evolution[:1024], inline=False)
            embed.set_footer(text=f"Pokémon #{mon.id} • Artwork: PokéAPI")
            await gui_send(interaction, embed=embed, ephemeral=True)

    @app_commands.command(name="pokemon_search", description="Filter your Pokémon collection")
    async def pokemon_search(
        self,
        interaction: discord.Interaction,
        species: str | None = None,
        min_iv: app_commands.Range[float, 0, 100] = 0.0,
        page: app_commands.Range[int, 1, 1000000] = 1,
    ):
        async def select_shiny(click, shiny):
            async def select_favorites(selection, favorites_only):
                await self.search_results(selection, species, shiny, favorites_only, min_iv, page)
            await choose(click, "Filter by favorites.",
                         [("All Pokémon", False), ("Favorites only", True)], select_favorites)
        await choose(interaction, "Filter by shiny status.",
                     [("Any", None), ("Shiny", True), ("Non-shiny", False)], select_shiny)

    async def search_results(self, interaction, species, shiny, favorites_only, min_iv, page):
        async with SessionLocal() as session:
            user = await UserRepository(session).get_by_discord_id(interaction.user.id)
            if not user:
                await reply(interaction, "Use `/start` first.", ephemeral=True)
                return
            rows = await PokemonRepository(session).search(
                user.id, species, shiny, True if favorites_only else None, min_iv, page=page
            )
        text = "\n".join(
            f"#{m.id} {'⭐ ' if m.favorite else ''}{m.display_name} · Lv.{m.level} · {m.iv_percent}% IV" for m in rows
        )
        await reply(interaction, text or "No matches.", ephemeral=not bool(rows))

    @app_commands.command(name="pokemon_nickname", description="Set or clear a Pokémon nickname")
    async def nickname(self, interaction: discord.Interaction, pokemon_id: int, nickname: str | None = None):
        async with SessionLocal() as session:
            user = await UserRepository(session).get_by_discord_id(interaction.user.id)
            mon = await PokemonRepository(session).get_by_id_locked(pokemon_id)
            if not user or not mon or mon.owner_id != user.id:
                await gui_send(interaction, "You do not own that Pokémon.", ephemeral=True)
                return
            if nickname and (len(nickname) > 40 or not nickname.replace(" ", "").isalnum()):
                await gui_send(interaction, 
                    "Nicknames must be 40 characters or fewer and contain only letters, numbers, and spaces.",
                    ephemeral=True,
                )
                return
            mon.nickname = nickname or None
            await session.commit()
        await gui_send(interaction, f"Nickname updated to **{mon.display_name}**.")

    @app_commands.command(name="pokemon_favorite", description="Toggle favorite protection")
    async def favorite(self, interaction: discord.Interaction, pokemon_id: int):
        async with SessionLocal() as session:
            user = await UserRepository(session).get_by_discord_id(interaction.user.id)
            mon = await PokemonRepository(session).get_by_id_locked(pokemon_id)
            if not user or not mon or mon.owner_id != user.id:
                await gui_send(interaction, "You do not own that Pokémon.", ephemeral=True)
                return
            mon.favorite = not mon.favorite
            await session.commit()
        await gui_send(interaction, 
            f"Favorite protection {'enabled' if mon.favorite else 'disabled'} for **{mon.display_name}**."
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(PokemonCog(bot))
