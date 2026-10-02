from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base
from sqlalchemy import Index, text


class Auction(Base):
    __tablename__ = "auctions"
    __table_args__ = (Index("uq_auction_active_pokemon", "pokemon_id", unique=True,
                           postgresql_where=text("status = 'active'"), sqlite_where=text("status = 'active'")),)
    id: Mapped[int] = mapped_column(primary_key=True)
    pokemon_id: Mapped[int] = mapped_column(ForeignKey("pokemon_instances.id"), index=True)
    seller_discord_id: Mapped[int] = mapped_column(BigInteger, index=True)
    highest_bidder_discord_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    starting_bid: Mapped[int] = mapped_column(Integer)
    current_bid: Mapped[int] = mapped_column(Integer)
    bid_increment: Mapped[int] = mapped_column(Integer, default=100)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuctionBid(Base):
    __tablename__ = "auction_bids"
    id: Mapped[int] = mapped_column(primary_key=True)
    auction_id: Mapped[int] = mapped_column(ForeignKey("auctions.id"), index=True)
    bidder_discord_id: Mapped[int] = mapped_column(BigInteger, index=True)
    amount: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
