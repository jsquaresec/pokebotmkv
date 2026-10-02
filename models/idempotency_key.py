from datetime import datetime
from sqlalchemy import BigInteger, DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (UniqueConstraint("scope", "request_key", name="uq_idempotency_scope_key"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    scope: Mapped[str] = mapped_column(String(50), index=True)
    request_key: Mapped[str] = mapped_column(String(100))
    actor_discord_id: Mapped[int] = mapped_column(BigInteger, index=True)
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
