from config import settings

class NotificationProcessingService:
    def __init__(self, repo):
        self.repo = repo

    async def mark_sent(self, row):
        row.status = "sent"
        return await self.repo.save(row)

    async def mark_failed(self, row):
        row.status = "failed"
        row.retry_count += 1
        return await self.repo.save(row)

    async def retry(self, row):
        row.status = "queued"
        row.retry_count += 1
        return await self.repo.save(row)

    async def fail_or_dead_letter(self, row):
        if row.retry_count + 1 >= settings.notification_max_retries:
            row.status = "dead_lettered"
            row.retry_count += 1
            return await self.repo.save(row)
        row.status = "failed"
        row.retry_count += 1
        return await self.repo.save(row)

    async def requeue_failed_if_allowed(self, row):
        if row.retry_count >= settings.notification_max_retries:
            row.status = "dead_lettered"
            return await self.repo.save(row)
        row.status = "queued"
        return await self.repo.save(row)
