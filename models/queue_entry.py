from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class QueueEntry(Base):
    __tablename__ = "queue_entries"
    __table_args__ = (UniqueConstraint("discord_id", name="uq_queue_discord_id"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    discord_id: Mapped[int] = mapped_column(BigInteger, index=True)
    rating: Mapped[int] = mapped_column(Integer, default=1000)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
