from fastapi import APIRouter
from core.database import SessionLocal
from repositories.rulesets import RulesetRepository

router = APIRouter(prefix="/rulesets", tags=["rulesets"])

@router.get("")
async def list_rulesets():
    async with SessionLocal() as session:
        rows = await RulesetRepository(session).list_all()
        return [{"id": x.id, "name": x.name, "description": x.description, "ranked": x.is_ranked_legal} for x in rows]
