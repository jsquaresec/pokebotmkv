from datetime import datetime
from sqlalchemy import BigInteger, DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class Achievement(Base):
    __tablename__ = "achievements"
    __table_args__ = (UniqueConstraint("discord_id", "code", name="uq_achievement_user_code"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[int] = mapped_column(BigInteger, index=True)
    code: Mapped[str] = mapped_column(String(80), index=True)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
