from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class QuestProgress(Base):
    __tablename__ = "quest_progress"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recipient_discord_id: Mapped[int] = mapped_column(BigInteger, index=True)
    quest_code: Mapped[str] = mapped_column(String(50), index=True)
    progress_value: Mapped[int] = mapped_column(Integer, default=0)
    target_value: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
