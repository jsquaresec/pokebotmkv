from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class ActiveBattle(Base):
    __tablename__ = "active_battles"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    battle_type: Mapped[str] = mapped_column(String(50), index=True)
    player_one_discord_id: Mapped[int] = mapped_column(BigInteger, index=True)
    player_two_discord_id: Mapped[int] = mapped_column(BigInteger, index=True)
    state_json: Mapped[str] = mapped_column(Text)
    finished: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
