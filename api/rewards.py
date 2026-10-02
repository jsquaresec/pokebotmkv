import json
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import SessionLocal
from repositories.reward_claims import RewardClaimRepository
from services.reward_service import RewardService

router = APIRouter(prefix="/rewards", tags=["rewards"])

async def get_session():
    async with SessionLocal() as session:
        yield session

@router.get("/recent")
async def recent_rewards(session: AsyncSession = Depends(get_session)):
    rows = await RewardService(RewardClaimRepository(session)).recent(50)
    return [
        {
            "id": r.id,
            "recipient_discord_id": r.recipient_discord_id,
            "reward_type": r.reward_type,
            "amount": r.amount,
            "related_battle_id": r.related_battle_id,
            "details": json.loads(r.details_json),
        }
        for r in rows
    ]
