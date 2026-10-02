from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import SessionLocal
from repositories.daily_rewards import DailyRewardRepository
from repositories.quests import QuestRepository
from services.quest_service import QuestService

router = APIRouter(prefix="/live", tags=["live"])

async def get_session():
    async with SessionLocal() as session:
        yield session

@router.get("/daily/{discord_id}")
async def daily_snapshot(discord_id: int, session: AsyncSession = Depends(get_session)):
    latest = await DailyRewardRepository(session).latest_for_user(discord_id)
    if latest is None:
        return {"discord_id": discord_id, "streak": 0, "last_claimed": None}
    return {"discord_id": discord_id, "streak": latest.streak_count, "last_claimed": latest.created_at.isoformat()}

@router.get("/quests/{discord_id}")
async def quest_snapshot(discord_id: int, session: AsyncSession = Depends(get_session)):
    svc = QuestService(QuestRepository(session))
    await svc.ensure_defaults(discord_id)
    rows = await QuestRepository(session).list_for_user(discord_id)
    return [
        {"quest_code": r.quest_code, "progress": r.progress_value, "target": r.target_value, "status": r.status}
        for r in rows
    ]
