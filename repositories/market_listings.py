from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.market_listing import MarketListing
from models.pokemon import PokemonInstance


class MarketListingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, listing_id: int, lock: bool = False):
        stmt = select(MarketListing).where(MarketListing.id == listing_id)
        if lock:
            stmt = stmt.with_for_update()
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create(self, pokemon_id: int, seller_discord_id: int, price: int):
        row = MarketListing(pokemon_id=pokemon_id, seller_discord_id=seller_discord_id, price=price)
        self.session.add(row)
        await self.session.flush()
        return row

    async def search(self, species: str | None = None, max_price: int | None = None, limit: int = 20):
        stmt = select(MarketListing, PokemonInstance).join(PokemonInstance).where(MarketListing.status == "active")
        if species:
            stmt = stmt.where(PokemonInstance.species.ilike(f"%{species}%"))
        if max_price is not None:
            stmt = stmt.where(MarketListing.price <= max_price)
        stmt = stmt.order_by(MarketListing.price.asc(), MarketListing.id.asc()).limit(min(max(limit, 1), 50))
        return list((await self.session.execute(stmt)).all())

