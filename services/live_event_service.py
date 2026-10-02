from repositories.live_events import LiveEventRepository

class LiveEventService:
    def __init__(self, repo: LiveEventRepository):
        self.repo = repo

    async def list_active(self):
        return await self.repo.list_active()
