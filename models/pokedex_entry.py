from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class PokedexEntry(Base):
    __tablename__ = "pokedex_entries"
    __table_args__ = (UniqueConstraint("discord_id", "species", name="uq_pokedex_user_species"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[int] = mapped_column(BigInteger, index=True)
    species: Mapped[str] = mapped_column(String(100), index=True)
    seen_count: Mapped[int] = mapped_column(Integer, default=0)
    caught_count: Mapped[int] = mapped_column(Integer, default=0)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    first_caught_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
