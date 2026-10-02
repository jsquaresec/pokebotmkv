from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class PartySlot(Base):
    __tablename__ = "party_slots"
    __table_args__ = (UniqueConstraint("owner_id", "slot_index", name="uq_party_owner_slot"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    pokemon_id: Mapped[int] = mapped_column(ForeignKey("pokemon_instances.id"), index=True)
    slot_index: Mapped[int] = mapped_column(Integer)
