from datetime import datetime
from sqlalchemy import BigInteger, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class TradeOffer(Base):
    __tablename__ = "trade_offers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    from_discord_id: Mapped[int] = mapped_column(BigInteger, index=True)
    to_discord_id: Mapped[int] = mapped_column(BigInteger, index=True)
    offered_json: Mapped[str] = mapped_column(Text, default="{}")
    requested_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(30), default="open", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
