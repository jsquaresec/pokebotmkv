from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base
from sqlalchemy import Index, text


class MarketListing(Base):
    __tablename__ = "market_listings"
    __table_args__ = (Index("uq_market_active_pokemon", "pokemon_id", unique=True,
                           postgresql_where=text("status = 'active'"), sqlite_where=text("status = 'active'")),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pokemon_id: Mapped[int] = mapped_column(ForeignKey("pokemon_instances.id"), index=True)
    seller_discord_id: Mapped[int] = mapped_column(BigInteger, index=True)
    buyer_discord_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    price: Mapped[int] = mapped_column(Integer, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
