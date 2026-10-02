import asyncio
from core.logging_setup import configure_logging
from core.database import SessionLocal, init_models
from services.redis_queue_service import RedisQueueService
from services.notification_service import NotificationService
from repositories.notification_deliveries import NotificationDeliveryRepository

async def main():
    configure_logging("INFO")
    await init_models()
    queue = RedisQueueService()

    while True:
        event = await queue.pop("battle_events")
        if event is not None:
            print(f"Consumed battle event: {event}")
            if event.get("type") == "ranked_match_created":
                async with SessionLocal() as session:
                    service = NotificationService(NotificationDeliveryRepository(session))
                    await service.record_match_created(
                        event["player_one_discord_id"],
                        event["battle_id"],
                        event,
                    )
                    await service.record_match_created(
                        event["player_two_discord_id"],
                        event["battle_id"],
                        event,
                    )
        else:
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
