from datetime import datetime
from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class LiveEvent(Base):
    __tablename__ = "live_events"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    config_json: Mapped[str] = mapped_column(Text, default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
