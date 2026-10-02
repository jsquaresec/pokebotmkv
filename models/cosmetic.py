from datetime import datetime
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class Cosmetic(Base):
    __tablename__ = "cosmetics"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    cosmetic_type: Mapped[str] = mapped_column(String(50), index=True)
    rarity: Mapped[str] = mapped_column(String(30), default="common")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
