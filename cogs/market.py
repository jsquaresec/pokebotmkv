from core.game_gui import gui_send
import discord
from discord import app_commands
from discord.ext import commands
from core.database import SessionLocal
from repositories.market_listings import MarketListingRepository
from services.market_v70_service import MarketV70Service


class MarketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="market_search", description="Search active Pokémon listings")
    async def search(self, interaction: discord.Interaction, species: str | None = None, max_price: int | None = None):
        async with SessionLocal() as session:
            rows = await MarketListingRepository(session).search(species, max_price)
        if not rows:
            await gui_send(interaction, "No matching listings.", ephemeral=True)
            return
        lines = [f"#{listing.id} · {mon.species} Lv.{mon.level} · {mon.iv_percent}% IV · {listing.price:,} coins" for listing, mon in rows]
        await gui_send(interaction, "\n".join(lines))

    @app_commands.command(name="market_list", description="List one of your Pokémon for sale")
    async def list_pokemon(self, interaction: discord.Interaction, pokemon_id: int, price: int):
        async with SessionLocal() as session:
            try:
                async with session.begin():
                    listing, fee = await MarketV70Service(session).list_pokemon(interaction.user.id, pokemon_id, price)
            except ValueError as exc:
                await gui_send(interaction, str(exc), ephemeral=True)
                return
        await gui_send(interaction, f"Listed Pokémon #{pokemon_id} as market #{listing.id}. Fee: {fee} coins.")

    @app_commands.command(name="market_buy", description="Buy a Pokémon listing")
    async def buy(self, interaction: discord.Interaction, listing_id: int):
        async with SessionLocal() as session:
            try:
                async with session.begin():
                    mon, fee = await MarketV70Service(session).buy(interaction.user.id, listing_id, str(interaction.id))
            except ValueError as exc:
                await gui_send(interaction, str(exc), ephemeral=True)
                return
        await gui_send(interaction, f"Purchased **{mon.species}** from listing #{listing_id}. Sale fee: {fee} coins.")

    @app_commands.command(name="market_remove", description="Remove your active listing")
    async def remove(self, interaction: discord.Interaction, listing_id: int):
        async with SessionLocal() as session:
            try:
                async with session.begin():
                    await MarketV70Service(session).cancel(interaction.user.id, listing_id)
            except ValueError as exc:
                await gui_send(interaction, str(exc), ephemeral=True)
                return
        await gui_send(interaction, f"Removed listing #{listing_id}.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(MarketCog(bot))
