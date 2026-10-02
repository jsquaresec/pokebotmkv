from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import SessionLocal
from repositories.audit_logs import AuditLogRepository
from repositories.battle_replays import BattleReplayRepository

router = APIRouter()

async def get_session():
    async with SessionLocal() as session:
        yield session

@router.get("/audit/logs")
async def get_audit_logs(session: AsyncSession = Depends(get_session)):
    repo = AuditLogRepository(session)
    rows = await repo.latest(50)
    return [
        {
            "id": r.id,
            "event_type": r.event_type,
            "actor": r.actor_discord_id,
            "target": r.target_id,
            "details": r.details,
        }
        for r in rows
    ]

@router.get("/debug/battle/{battle_id}")
async def debug_battle(battle_id: int, session: AsyncSession = Depends(get_session)):
    replay_repo = BattleReplayRepository(session)
    replay = await replay_repo.get_by_battle_id(battle_id)

    audit_repo = AuditLogRepository(session)
    audits = await audit_repo.latest(100)

    return {
        "battle_id": battle_id,
        "replay": replay.replay_json if replay else None,
        "audit_trail": [
            {
                "event": a.event_type,
                "actor": a.actor_discord_id,
                "details": a.details
            }
            for a in audits if a.target_id == battle_id
        ]
    }
