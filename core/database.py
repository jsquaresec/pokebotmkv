from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import settings
from models.base import Base
import models  # noqa: F401 - ensure model registration

engine = create_async_engine(settings.database_url, echo=False, future=True)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def init_models() -> None:
    if not settings.auto_create_schema:
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
