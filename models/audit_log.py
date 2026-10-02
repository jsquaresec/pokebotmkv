from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    actor_discord_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    target_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
