from repositories.audit_logs import AuditLogRepository

class AuditService:
    def __init__(self, repo: AuditLogRepository):
        self.repo = repo

    async def log(self, event_type: str, actor_discord_id: int | None = None, target_id: int | None = None, details: str = ""):
        return await self.repo.create(event_type, actor_discord_id, target_id, details)
