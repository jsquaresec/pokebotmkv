from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class DailyRewardClaim(Base):
    __tablename__ = "daily_reward_claims"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recipient_discord_id: Mapped[int] = mapped_column(BigInteger, index=True)
    streak_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
