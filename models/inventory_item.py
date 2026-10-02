from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    __table_args__ = (UniqueConstraint("owner_discord_id", "sku", name="uq_inventory_owner_sku"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_discord_id: Mapped[int] = mapped_column(BigInteger, index=True)
    sku: Mapped[str] = mapped_column(String(50), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
