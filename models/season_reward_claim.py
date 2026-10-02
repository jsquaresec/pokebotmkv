from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class SeasonRewardClaim(Base):
    __tablename__ = "season_reward_claims"
    __table_args__ = (UniqueConstraint("discord_id", "season_code", "tier", name="uq_season_claim"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[int] = mapped_column(BigInteger, index=True)
    season_code: Mapped[str] = mapped_column(String(50), index=True)
    tier: Mapped[int] = mapped_column(Integer)
    claimed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
