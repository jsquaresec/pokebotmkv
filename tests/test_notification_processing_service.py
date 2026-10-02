import asyncio
from services.notification_processing_service import NotificationProcessingService

class DummyRow:
    def __init__(self):
        self.status = "queued"
        self.retry_count = 0

class DummyRepo:
    async def save(self, row):
        return row

async def main():
    service = NotificationProcessingService(DummyRepo())

    row = DummyRow()
    await service.mark_sent(row)
    assert row.status == "sent"
    assert row.retry_count == 0

    row2 = DummyRow()
    await service.mark_failed(row2)
    assert row2.status == "failed"
    assert row2.retry_count == 1

    row3 = DummyRow()
    await service.retry(row3)
    assert row3.status == "queued"
    assert row3.retry_count == 1

    row4 = DummyRow()
    await service.fail_or_dead_letter(row4)
    assert row4.status in {"failed", "dead_lettered"}
    assert row4.retry_count == 1

    row5 = DummyRow()
    row5.retry_count = 99
    await service.requeue_failed_if_allowed(row5)
    assert row5.status == "dead_lettered"

    print("notification processing service tests passed")

if __name__ == "__main__":
    asyncio.run(main())
