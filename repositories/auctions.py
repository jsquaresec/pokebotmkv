from datetime import datetime
from sqlalchemy import select
from models.auction import Auction, AuctionBid
from models.pokemon import PokemonInstance


class AuctionRepository:
    def __init__(self, session):
        self.session = session

    async def get(self, auction_id: int, lock: bool = False):
        stmt = select(Auction).where(Auction.id == auction_id)
        if lock:
            stmt = stmt.with_for_update()
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create(self, **values):
        row = Auction(**values)
        self.session.add(row)
        await self.session.flush()
        return row

    async def add_bid(self, auction_id: int, bidder_discord_id: int, amount: int):
        row = AuctionBid(auction_id=auction_id, bidder_discord_id=bidder_discord_id, amount=amount)
        self.session.add(row)
        await self.session.flush()
        return row

    async def active(self, limit: int = 20):
        stmt = (
            select(Auction, PokemonInstance)
            .join(PokemonInstance)
            .where(Auction.status == "active")
            .order_by(Auction.ends_at)
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).all())

    async def expired_ids(self, limit: int = 100):
        stmt = select(Auction.id).where(Auction.status == "active", Auction.ends_at <= datetime.utcnow()).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())
