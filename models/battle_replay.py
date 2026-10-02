from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class BattleReplay(Base):
    __tablename__ = "battle_replays"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    battle_id: Mapped[int] = mapped_column(Integer, index=True)
    battle_type: Mapped[str] = mapped_column(String(50), index=True)
    replay_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
