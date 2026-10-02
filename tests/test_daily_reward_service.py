from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from models import Base, User
from models.daily_reward_claim import DailyRewardClaim
from repositories.daily_rewards import DailyRewardRepository
from services.daily_reward_service import DailyRewardService

@pytest.fixture
async def db():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        session.add(User(discord_id=123, username='Trainer', balance=1000))
        await session.commit()
        yield session
    await engine.dispose()

async def test_streak_pays_once_and_survives_reload(db):
    now = datetime(2026, 10, 1, 23, 59, tzinfo=timezone.utc)
    svc = DailyRewardService(DailyRewardRepository(db))
    for day, reward in enumerate((1000, 1100, 1200)):
        moment = now + timedelta(days=day)
        result = await svc.claim(123, moment)
        await db.commit()
        assert result['reward'] == reward and result['streak'] == day + 1
        db.expire_all()
        duplicate = await DailyRewardService(DailyRewardRepository(db)).claim(123, moment)
        assert duplicate['claimed'] is False and duplicate['reward'] == 0
    assert result['balance'] == 4300
    assert await db.scalar(select(func.count()).select_from(DailyRewardClaim)) == 3

async def test_midnight_and_missed_day(db):
    svc = DailyRewardService(DailyRewardRepository(db))
    await svc.claim(123, datetime(2026, 10, 1, 23, 59))
    await db.commit()
    second = await svc.claim(123, datetime(2026, 10, 2))
    await db.commit()
    assert second['reward'] == 1100
    reset = await svc.claim(123, datetime(2026, 10, 4))
    assert reset['streak'] == 1 and reset['reward'] == 1000

async def test_rollback_undoes_claim_and_gold(db):
    svc = DailyRewardService(DailyRewardRepository(db))
    await svc.claim(123, datetime(2026, 10, 1))
    await db.rollback()
    assert await db.scalar(select(func.count()).select_from(DailyRewardClaim)) == 0
    assert (await db.scalar(select(User))).balance == 1000

async def test_requires_trainer(db):
    with pytest.raises(ValueError, match='/start'):
        await DailyRewardService(DailyRewardRepository(db)).claim(999)

@pytest.mark.parametrize('streak, expected', [(1, 1000), (2, 1100), (90, 9900), (91, 10000), (92, 10000), (1000, 10000)])
def test_reward_cap(streak, expected):
    assert DailyRewardService.reward_for_streak(streak) == expected
