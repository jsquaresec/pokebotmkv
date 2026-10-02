import asyncio
from core.logging_setup import configure_logging
from core.database import SessionLocal, init_models
from repositories.notification_deliveries import NotificationDeliveryRepository
from services.notification_processing_service import NotificationProcessingService

async def main():
    configure_logging("INFO")
    await init_models()

    while True:
        async with SessionLocal() as session:
            repo = NotificationDeliveryRepository(session)
            service = NotificationProcessingService(repo)
            rows = await repo.queued(20)

            for row in rows:
                try:
                    print(f"Processing notification #{row.id} for recipient {row.recipient_discord_id}")
                    await service.mark_sent(row)
                except Exception:
                    await service.fail_or_dead_letter(row)

        await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(main())
