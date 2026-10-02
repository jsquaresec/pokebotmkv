from repositories.cosmetics import CosmeticRepository

class CosmeticService:
    def __init__(self, repo: CosmeticRepository):
        self.repo = repo

    async def browse_active(self):
        return await self.repo.list_active()
