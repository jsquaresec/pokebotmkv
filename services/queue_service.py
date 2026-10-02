from repositories.queue_entries import QueueEntryRepository

class QueueService:
    def __init__(self, repo: QueueEntryRepository):
        self.repo = repo

    async def join_or_match(self, discord_id: int, rating: int):
        existing = await self.repo.get_by_discord_id(discord_id)
        if existing is not None:
            return {"status": "already_queued"}

        await self.repo.enqueue(discord_id, rating)
        entries = await self.repo.list_entries()
        if len(entries) < 2:
            return {"status": "queued"}

        entries.sort(key=lambda x: (x.rating, x.created_at))
        p1 = entries[0]
        p2 = entries[1]
        await self.repo.delete(p1)
        await self.repo.delete(p2)
        return {"status": "matched", "players": (p1.discord_id, p2.discord_id)}

    async def leave(self, discord_id: int) -> bool:
        entry = await self.repo.get_by_discord_id(discord_id)
        if entry is None:
            return False
        await self.repo.delete(entry)
        return True
