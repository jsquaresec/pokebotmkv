from datetime import datetime, timedelta
from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class WildEncounter(Base):
    __tablename__ = "wild_encounters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, index=True)
    message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    species: Mapped[str] = mapped_column(String(100), index=True)
    level: Mapped[int] = mapped_column(Integer, default=5)
    current_hp: Mapped[int] = mapped_column(Integer, default=20)
    max_hp: Mapped[int] = mapped_column(Integer, default=20)
    rarity: Mapped[str] = mapped_column(String(30), default="common")
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    battle_state_json: Mapped[str] = mapped_column(Text, default="{}", server_default="{}")
    claimed_by_discord_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=5))
