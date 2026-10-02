import asyncio
from core.logging_setup import configure_logging
from core.database import SessionLocal, init_models
from services.matchmaking_worker_service import MatchmakingWorkerService
from services.battle_event_service import BattleEventService

async def main():
    configure_logging("INFO")
    await init_models()
    events = BattleEventService()

    while True:
        async with SessionLocal() as session:
            service = MatchmakingWorkerService(session)
            result = await service.process_once()
            if result is not None:
                print(f"Created ranked battle: {result}")
                await events.publish_match_created(
                    result["battle_id"],
                    result["player_one_discord_id"],
                    result["player_two_discord_id"],
                )
        await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(main())
