from core.game_gui import gui_send
import discord
from discord import app_commands
from discord.ext import commands, tasks
from core.database import SessionLocal
from repositories.auctions import AuctionRepository
from services.auction_service import AuctionService


class AuctionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settle_expired.start()

    def cog_unload(self):
        self.settle_expired.cancel()

    @tasks.loop(minutes=1)
    async def settle_expired(self):
        async with SessionLocal() as session:
            ids = await AuctionRepository(session).expired_ids()
        for auction_id in ids:
            async with SessionLocal() as session:
                try:
                    async with session.begin():
                        await AuctionService(session).settle(auction_id)
                except ValueError:
                    continue

    @settle_expired.before_loop
    async def before_settle(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="auction_search", description="Browse active auctions")
    async def search(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            rows = await AuctionRepository(session).active()
        text = "\n".join(
            f"#{a.id} · {m.species} Lv.{m.level} · bid {max(a.starting_bid, a.current_bid):,} · ends <t:{int(a.ends_at.timestamp())}:R>"
            for a, m in rows
        )
        await gui_send(interaction, text or "No active auctions.", ephemeral=not bool(rows))

    @app_commands.command(name="auction_start", description="Start a Pokémon auction")
    async def start(
        self, interaction: discord.Interaction, pokemon_id: int, hours: int, starting_bid: int, bid_increment: int = 100
    ):
        async with SessionLocal() as session:
            try:
                async with session.begin():
                    row = await AuctionService(session).start(
                        interaction.user.id, pokemon_id, hours, starting_bid, bid_increment
                    )
            except ValueError as exc:
                await gui_send(interaction, str(exc), ephemeral=True)
                return
        await gui_send(interaction, 
            f"Auction #{row.id} started; ends <t:{int(row.ends_at.timestamp())}:R>."
        )

    @app_commands.command(name="auction_bid", description="Bid on an auction")
    async def bid(self, interaction: discord.Interaction, auction_id: int, amount: int):
        async with SessionLocal() as session:
            try:
                async with session.begin():
                    row = await AuctionService(session).bid(
                        interaction.user.id, auction_id, amount, str(interaction.id)
                    )
            except ValueError as exc:
                await gui_send(interaction, str(exc), ephemeral=True)
                return
        await gui_send(interaction, f"You lead auction #{row.id} at **{row.current_bid:,}** coins.")

    @app_commands.command(name="auction_finalize", description="Finalize an ended auction")
    async def finalize(self, interaction: discord.Interaction, auction_id: int):
        async with SessionLocal() as session:
            try:
                async with session.begin():
                    row, mon, fee = await AuctionService(session).settle(auction_id)
            except ValueError as exc:
                await gui_send(interaction, str(exc), ephemeral=True)
                return
        await gui_send(interaction, 
            f"Auction #{row.id} finished: **{mon.species}** · status {row.status} · fee {fee}."
        )


async def setup(bot):
    await bot.add_cog(AuctionCog(bot))
