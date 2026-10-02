from datetime import datetime
from repositories.market_listings import MarketListingRepository
from repositories.pokemon import PokemonRepository
from repositories.users import UserRepository
from services.market_fee_service import MarketFeeService
from services.idempotency_service import IdempotencyService
from services.transfer_guard import ensure_not_in_party


class MarketV70Service:
    def __init__(self, session):
        self.session = session
        self.listings = MarketListingRepository(session)
        self.pokemon = PokemonRepository(session)
        self.users = UserRepository(session)
        self.fees = MarketFeeService()

    async def list_pokemon(self, seller_discord_id: int, pokemon_id: int, price: int):
        if price < 10:
            raise ValueError("Minimum listing price is 10 coins.")
        seller = await self.users.get_by_discord_id_locked(seller_discord_id)
        mon = await self.pokemon.get_by_id_locked(pokemon_id)
        if not seller or not mon or mon.owner_id != seller.id:
            raise ValueError("You do not own that Pokémon.")
        if mon.locked:
            raise ValueError("That Pokémon is already locked in another activity.")
        if mon.favorite:
            raise ValueError("Remove favorite protection before listing this Pokémon.")
        fee = self.fees.listing_fee(price)
        await ensure_not_in_party(self.session, mon.id)
        if seller.balance < fee:
            raise ValueError("You cannot afford the listing fee.")
        seller.balance -= fee
        mon.locked = True
        row = await self.listings.create(mon.id, seller_discord_id, price)
        return row, fee

    async def buy(self, buyer_discord_id: int, listing_id: int, request_key: str | None = None):
        if request_key:
            await IdempotencyService(self.session).acquire("market_buy", request_key, buyer_discord_id)
        listing = await self.listings.get(listing_id, lock=True)
        if not listing or listing.status != "active":
            raise ValueError("That listing is no longer available.")
        if listing.seller_discord_id == buyer_discord_id:
            raise ValueError("You cannot buy your own listing.")
        buyer = await self.users.get_by_discord_id_locked(buyer_discord_id)
        seller = await self.users.get_by_discord_id_locked(listing.seller_discord_id)
        mon = await self.pokemon.get_by_id_locked(listing.pokemon_id)
        if not buyer or not seller or not mon or mon.owner_id != seller.id or not mon.locked:
            raise ValueError("Listing ownership validation failed.")
        if buyer.balance < listing.price:
            raise ValueError("Not enough coins.")
        sale_fee = self.fees.sale_fee(listing.price)
        buyer.balance -= listing.price
        seller.balance += listing.price - sale_fee
        mon.owner_id = buyer.id
        mon.locked = False
        listing.status = "sold"
        listing.buyer_discord_id = buyer_discord_id
        listing.completed_at = datetime.utcnow()
        await self.session.flush()
        return mon, sale_fee

    async def cancel(self, seller_discord_id: int, listing_id: int):
        listing = await self.listings.get(listing_id, lock=True)
        if not listing or listing.status != "active" or listing.seller_discord_id != seller_discord_id:
            raise ValueError("Active listing not found for this seller.")
        mon = await self.pokemon.get_by_id_locked(listing.pokemon_id)
        mon.locked = False
        listing.status = "cancelled"
        listing.completed_at = datetime.utcnow()
        await self.session.flush()
        return listing
