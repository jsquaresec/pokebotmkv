from datetime import datetime
from sqlalchemy import BigInteger, DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class Friendship(Base):
    __tablename__ = "friendships"
    __table_args__ = (UniqueConstraint("requester_discord_id", "addressee_discord_id", name="uq_friend_pair"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    requester_discord_id: Mapped[int] = mapped_column(BigInteger, index=True)
    addressee_discord_id: Mapped[int] = mapped_column(BigInteger, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
