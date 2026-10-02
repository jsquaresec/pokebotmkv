from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import SessionLocal
from repositories.ranked_profiles import RankedProfileRepository
from services.ranked_tier_service import RankedTierService

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

async def get_session():
    async with SessionLocal() as session:
        yield session

@router.get("/global")
async def global_leaderboard(session: AsyncSession = Depends(get_session)):
    repo = RankedProfileRepository(session)
    rows = await repo.top_profiles(25)
    tiers = RankedTierService()
    return [
        {
            "rank": i + 1,
            "owner_id": row.owner_id,
            "rating": row.rating,
            "wins": row.wins,
            "losses": row.losses,
            "tier": tiers.tier_for_rating(row.rating),
        }
        for i, row in enumerate(rows)
    ]
