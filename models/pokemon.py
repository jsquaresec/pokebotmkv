from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class PokemonInstance(Base):
    __tablename__ = "pokemon_instances"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    species: Mapped[str] = mapped_column(String(100), index=True)
    level: Mapped[int] = mapped_column(Integer, default=5)
    current_hp: Mapped[int] = mapped_column(Integer, default=20)
    max_hp: Mapped[int] = mapped_column(Integer, default=20)
    attack: Mapped[int] = mapped_column(Integer, default=10)
    defense: Mapped[int] = mapped_column(Integer, default=10)
    speed: Mapped[int] = mapped_column(Integer, default=10)
    shiny: Mapped[bool] = mapped_column(Boolean, default=False)
    dex_number: Mapped[int] = mapped_column(Integer, default=0, index=True)
    form: Mapped[str] = mapped_column(String(80), default="Normal")
    primary_type: Mapped[str] = mapped_column(String(30), default="normal")
    secondary_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    experience: Mapped[int] = mapped_column(Integer, default=0)
    iv_hp: Mapped[int] = mapped_column(Integer, default=0)
    iv_attack: Mapped[int] = mapped_column(Integer, default=0)
    iv_defense: Mapped[int] = mapped_column(Integer, default=0)
    iv_speed: Mapped[int] = mapped_column(Integer, default=0)
    locked: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    nickname: Mapped[str | None] = mapped_column(String(40), nullable=True)
    nature: Mapped[str] = mapped_column(String(30), default="Hardy")
    ability: Mapped[str] = mapped_column(String(80), default="Adaptability")
    gender: Mapped[str] = mapped_column(String(12), default="unknown")
    favorite: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    held_item: Mapped[str | None] = mapped_column(String(50), nullable=True)
    moves_json: Mapped[str] = mapped_column(Text, default="[]")
    catalog_revision: Mapped[int] = mapped_column(Integer, default=1, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    @property
    def iv_percent(self) -> float:
        return round((self.iv_hp + self.iv_attack + self.iv_defense + self.iv_speed) / 124 * 100, 2)

    @property
    def display_name(self) -> str:
        return self.nickname or self.species
