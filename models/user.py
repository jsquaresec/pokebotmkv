from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    discord_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100))
    balance: Mapped[int] = mapped_column(Integer, default=1000)
    trainer_level: Mapped[int] = mapped_column(Integer, default=1)
    trainer_xp: Mapped[int] = mapped_column(Integer, default=0)
    season_xp: Mapped[int] = mapped_column(Integer, default=0)
    bio: Mapped[str] = mapped_column(String(240), default="")
    selected_title: Mapped[str] = mapped_column(String(80), default="Rookie Trainer")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
