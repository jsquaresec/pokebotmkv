from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class RewardClaim(Base):
    __tablename__ = "reward_claims"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recipient_discord_id: Mapped[int] = mapped_column(BigInteger, index=True)
    reward_type: Mapped[str] = mapped_column(String(50), index=True)
    amount: Mapped[int] = mapped_column(Integer, default=0)
    related_battle_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
