from core.game_gui import gui_send
from core.choice_buttons import choose, reply
import json
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from core.database import SessionLocal
from repositories.users import UserRepository
from repositories.inventory import InventoryRepository
from repositories.trade_offers import TradeOfferRepository
from services.shop_service import ShopService
from services.trade_service import TradeService
from repositories.pokemon import PokemonRepository
from services.idempotency_service import IdempotencyService

SHOP_CATALOG = json.loads(
    (Path(__file__).resolve().parents[1] / "data" / "shop_catalog.json").read_text(encoding="utf-8")
)

class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="shop", description="Browse and buy items with buttons")
    async def shop(self, interaction: discord.Interaction):
        await self.buy_menu(interaction)

    @app_commands.command(name="buy", description="Choose an item and quantity with buttons")
    async def buy(self, interaction: discord.Interaction):
        await self.buy_menu(interaction)

    async def buy_menu(self, interaction):
        await choose(interaction, "Choose an item. Select a quantity next to complete your purchase.",
                     [(f'{i["name"]} — {i["price"]:,} gold', i["sku"]) for i in SHOP_CATALOG], self.buy_quantity)

    async def buy_quantity(self, interaction, sku):
        item = next(i for i in SHOP_CATALOG if i["sku"] == sku)

        async def purchase(click, quantity):
            await self.purchase(click, sku, quantity)

        await choose(interaction, f'Buy **{item["name"]}**: click a quantity to purchase.',
                     [(f'{q} × — {q * item["price"]:,} gold', q) for q in (1, 5, 10, 25)], purchase)

    async def purchase(self, interaction, sku, quantity):
        async with SessionLocal() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_discord_id_locked(interaction.user.id)
            if user is None:
                await reply(interaction, "Use `/start` first.", ephemeral=True)
                return
            repo = InventoryRepository(session)
            svc = ShopService(repo)
            try:
                result = await svc.purchase(user, sku, quantity)
            except ValueError as exc:
                await reply(interaction, str(exc), ephemeral=True)
                return
            receipt = discord.Embed(title="Purchase complete", color=0x2ECC71)
            receipt.add_field(name="Item", value=f'{quantity} × {result["item"]["name"]}', inline=False)
            receipt.add_field(name="Gold spent", value=f'🪙 {result["total"]:,} gold')
            receipt.add_field(name="Gold remaining", value=f'**🪙 {user.balance:,} gold**')
            await gui_send(interaction, embed=receipt, ephemeral=True)

    @app_commands.command(name="inventory", description="View your inventory")
    async def inventory(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            repo = InventoryRepository(session)
            rows = await repo.list_for_owner(interaction.user.id)
            if not rows:
                await gui_send(interaction, "Your inventory is empty.", ephemeral=True)
                return
            lines = [f"{r.sku}: {r.quantity}" for r in rows]
            await gui_send(interaction, "\n".join(lines))

    @app_commands.command(name="trade_offer", description="Create a simple trade offer")
    async def trade_offer(self, interaction: discord.Interaction, to_discord_id: int,
                          offered_qty: app_commands.Range[int, 1] = 1,
                          requested_qty: app_commands.Range[int, 1] = 1):
        options = [(item["name"], item["sku"]) for item in SHOP_CATALOG]

        async def offered(click, offered_sku):
            async def requested(selection, requested_sku):
                await self.create_trade(selection, to_discord_id, offered_sku, offered_qty,
                                        requested_sku, requested_qty)
            await choose(click, "Choose the item you want in return. Clicking creates the offer.", options, requested)

        await choose(interaction, "Choose the item you want to offer.", options, offered)

    async def create_trade(self, interaction, to_discord_id, offered_sku, offered_qty, requested_sku, requested_qty):
        async with SessionLocal() as session:
            svc = TradeService(TradeOfferRepository(session))
            offer = await svc.create_offer(
                interaction.user.id,
                to_discord_id,
                {"sku": offered_sku, "quantity": offered_qty},
                {"sku": requested_sku, "quantity": requested_qty},
            )
            await reply(interaction, f"Created trade offer #{offer.id} to {to_discord_id}.")

    @app_commands.command(name="trade_accept", description="Accept and settle a trade atomically")
    async def trade_accept(self, interaction: discord.Interaction, offer_id: int):
        async with SessionLocal() as session:
            svc = TradeService(TradeOfferRepository(session))
            try:
                async with session.begin():
                    await IdempotencyService(session).acquire("trade_accept", str(interaction.id), interaction.user.id)
                    await svc.settle(offer_id, interaction.user.id, session, UserRepository(session), InventoryRepository(session), PokemonRepository(session))
            except ValueError as exc:
                await gui_send(interaction, str(exc), ephemeral=True)
                return
        await gui_send(interaction, f"Trade #{offer_id} completed.")

    @app_commands.command(name="trade_cancel", description="Cancel an open trade")
    async def trade_cancel(self, interaction: discord.Interaction, offer_id: int):
        async with SessionLocal() as session:
            svc = TradeService(TradeOfferRepository(session))
            try:
                async with session.begin():
                    await svc.cancel(offer_id, interaction.user.id, session)
            except ValueError as exc:
                await gui_send(interaction, str(exc), ephemeral=True)
                return
        await gui_send(interaction, f"Trade #{offer_id} cancelled.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(EconomyCog(bot))
