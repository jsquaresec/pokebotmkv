from datetime import date, datetime
from sqlalchemy import BigInteger, Date, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class DailyMission(Base):
    __tablename__ = 'daily_missions'
    __table_args__ = (UniqueConstraint('discord_id', 'day', 'code', name='uq_daily_mission_user_day_code'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[int] = mapped_column(BigInteger, index=True)
    day: Mapped[date] = mapped_column(Date)
    code: Mapped[str] = mapped_column(String(30))
    progress: Mapped[int] = mapped_column(Integer, default=0)
    reward_sku: Mapped[str] = mapped_column(String(50))
    reward_quantity: Mapped[int] = mapped_column(Integer)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

